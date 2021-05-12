import os

from aws_cdk import (core as cdk,
                     aws_apigateway as apigateway,
                     aws_s3 as s3,
                     aws_s3_notifications as s3_notify,
                     aws_lambda as lambda_,
                     aws_mediaconvert as mediaconvert,
                     aws_stepfunctions as stepfunctions,
                     aws_stepfunctions_tasks as stp_tasks,
                     aws_iam as iam,
                     aws_secretsmanager as secretsmanager)

from aws_cdk.aws_lambda_python import PythonFunction

TWITCH_CLIENT_SECRET_ARN = "arn:aws:secretsmanager:us-east-1:576758376358:secret:TWITCH_SECRET-xylhKu"
TWITCH_CLIENT_ID = "2nakqoqdxka9v5oekyo6742bmnxt2o"
MONGODB_FULL_URI_ARN = 'arn:aws:secretsmanager:us-east-1:576758376358:secret:MONGODB-6SPDyv'

class RenderLambdaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        individual_clips = s3.Bucket(scope=self,
                                     id="IndividualClips",
                                     public_read_access=True)

        cors = apigateway.CorsOptions(allow_origins=apigateway.Cors.ALL_ORIGINS)

        # API For Frontend
        clip_api = apigateway.RestApi(self, "clip-api",
                                      rest_api_name="Clips service",
                                      description="Service handles combining clips", default_cors_preflight_options=cors)

        clip_queuer = PythonFunction(self, 'ClipQueuer',
                                     handler='handler',
                                     index='handler.py',
                                     entry=os.path.join(
                                         os.getcwd(), 'lambdas', 'clip_queuer'),
                                     runtime=lambda_.Runtime.PYTHON_3_8,
                                     environment={
                                         'BUCKET': individual_clips.bucket_name
                                     },
                                     timeout=cdk.Duration.seconds(15),
                                     memory_size=256)

        addToQueue = apigateway.LambdaIntegration(clip_queuer,
                                                  request_templates={"application/json": '{ "statusCode": "200" }'})

        clips_endpoint = clip_api.root.add_resource("clips")

        clips_endpoint.add_method("POST", addToQueue)

        # Clip Downloader Container

        image_name = "lambdaClipDownloader"
        # image_version = "latest"

        ecr_image = lambda_.EcrImageCode.from_asset_image(
            directory=os.path.join(os.getcwd(), 'lambdas', 'downloader')
        )

        downloader = lambda_.Function(self,
                                      id=image_name,
                                      description="Containerized Clip Downloader",
                                      code=ecr_image,
                                      handler=lambda_.Handler.FROM_IMAGE,
                                      runtime=lambda_.Runtime.FROM_IMAGE,
                                      environment={
                                          'BUCKET': individual_clips.bucket_name
                                      },
                                      timeout=cdk.Duration.seconds(60),
                                      memory_size=512)

        individual_clips.grant_write(downloader)

        combined_clips = s3.Bucket(scope=self,
                                   id="CombinedClips",
                                   public_read_access=True)

        mediaconvert_queue = mediaconvert.CfnQueue(self, id="ClipCombiner")

        mediaconvert_role = iam.Role(self, "MediaConvert",
                                     assumed_by=iam.ServicePrincipal("mediaconvert.amazonaws.com"))
        individual_clips.grant_read(mediaconvert_role)
        combined_clips.grant_write(mediaconvert_role)

        mediaconvert_create_job = iam.PolicyStatement(
            actions=['mediaconvert:CreateJob'], resources=[mediaconvert_queue.attr_arn])

        mediaconvert_pass_role = iam.PolicyStatement(
            actions=["iam:PassRole", "iam:ListRoles"], resources=["arn:aws:iam::*:role/*"])

        renderer = PythonFunction(self, 'FinalRenderer',
                                  handler='handler',
                                  index='handler.py',
                                  initial_policy=[
                                      mediaconvert_create_job, mediaconvert_pass_role],
                                  entry=os.path.join(
                                      os.getcwd(), 'lambdas', 'renderer'),
                                  runtime=lambda_.Runtime.PYTHON_3_8,
                                  environment={
                                      'IN_BUCKET': individual_clips.bucket_name,
                                      'OUT_BUCKET': combined_clips.bucket_name,
                                      'QUEUE_ARN': mediaconvert_queue.attr_arn,
                                      'QUEUE_ROLE': mediaconvert_role.role_arn
                                  },
                                  memory_size=128)

        mongodb_full_uri = secretsmanager.Secret.from_secret_complete_arn(self, 'MONGODB_FULL_URI', MONGODB_FULL_URI_ARN)
        twitch_client_secret = secretsmanager.Secret.from_secret_complete_arn(self, 'TWITCH_CLIENT_SECRET', TWITCH_CLIENT_SECRET_ARN)

        # notification lambda
        notify_lambda = PythonFunction(self, 'Notify',
                                       handler='handler',
                                       index='handler.py',
                                       entry=os.path.join(
                                           os.getcwd(), 'lambdas', 'notify'),
                                       runtime=lambda_.Runtime.PYTHON_3_8,
                                       environment={
                                           'COMBINED_BUCKET_DNS': combined_clips.bucket_domain_name,
                                           'INDIVIDUAL_BUCKET_DNS': individual_clips.bucket_domain_name,
                                           'DB_NAME': 'pillar',
                                           'FROM_EMAIL': 'steven@pillar.gg',
                                           "TWITCH_CLIENT_ID": TWITCH_CLIENT_ID,
                                           "TWITCH_CLIENT_SECRET_ARN": TWITCH_CLIENT_SECRET_ARN,
                                           "MONGODB_URI_SECRET_ARN": mongodb_full_uri.secret_arn
                                       },
                                       memory_size=256,
                                       timeout=cdk.Duration.seconds(60))

        mongodb_full_uri.grant_read(notify_lambda)
        twitch_client_secret.grant_read(notify_lambda)

        ses_email_role = iam.PolicyStatement(actions=['ses:SendEmail', 'ses:SendRawEmail'], resources=['*'])
        notify_lambda.add_to_role_policy(ses_email_role)

        item_added = s3_notify.LambdaDestination(notify_lambda)

        combined_clips.add_event_notification(
            s3.EventType.OBJECT_CREATED, item_added)

        # state machine
        get_clips_task = stp_tasks.LambdaInvoke(self, "Download Clip",
                                                lambda_function=downloader
                                                )

        render_video_task = stp_tasks.LambdaInvoke(self, "Render Video",
                                                   lambda_function=renderer)

        notify_task = stp_tasks.LambdaInvoke(self, "Send notification",
                                             lambda_function=notify_lambda)

        process_clips = stepfunctions.Map(
            self, "Process Clips", input_path="$.clips").iterator(get_clips_task)

        success = stepfunctions.Succeed(self, "Video Processing Finished.")

        choice = stepfunctions.Choice(self, "Render?")

        choice.when(stepfunctions.Condition.boolean_equals(
            "$[0].Payload.render", False), notify_task)
        choice.when(stepfunctions.Condition.boolean_equals(
            "$[0].Payload.render", True), render_video_task)

        definition = process_clips.next(choice)

        state_machine = stepfunctions.StateMachine(self, "Renderer",
                                                   definition=definition
                                                   )

        clip_queuer.add_environment(
            'STEPFUNCTION_ARN', state_machine.state_machine_arn)

        state_machine.grant_start_execution(clip_queuer)
