import os
import json

from aws_cdk import (core as cdk,
                     aws_apigateway as apigateway,
                     aws_s3 as s3,
                     aws_s3_notifications as s3_notify,
                     aws_lambda as lambda_,
                     aws_mediaconvert as mediaconvert,
                     aws_stepfunctions as stepfunctions,
                     aws_stepfunctions_tasks as stp_tasks,
                     aws_iam as iam,
                     aws_events as events,
                     aws_events_targets as events_targets,
                     aws_secretsmanager as secretsmanager)

from aws_cdk.aws_lambda_python import PythonFunction

TWITCH_CLIENT_ID = "phpnjz4llxez4zpw3iurfthoi573c8"
MONGODB_FULL_URI_ARN = 'arn:aws:secretsmanager:us-east-1:576758376358:secret:MONGODB-6SPDyv'


class RenderLambdaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lifetime = s3.LifecycleRule(expiration=cdk.Duration.days(
            30), enabled=True, id='30-Day-Retention')

        individual_clips = s3.Bucket(scope=self,
                                     id="IndividualClips",
                                     public_read_access=True,
                                     lifecycle_rules=[lifetime])

        cors = apigateway.CorsOptions(
            allow_origins=apigateway.Cors.ALL_ORIGINS)

        clip_api = apigateway.RestApi(self, "clip-api",
                                      rest_api_name="Clips service",
                                      description="Service handles combining clips", default_cors_preflight_options=cors)

        transcoding_finished = PythonFunction(self, 'transcoding_finished',
                                              handler='handler',
                                              index='handler.py',
                                              entry=os.path.join(
                                                  os.getcwd(), 'lambdas', 'transcoding_progress'),
                                              runtime=lambda_.Runtime.PYTHON_3_8,

                                              timeout=cdk.Duration.seconds(60),
                                              memory_size=128)


        clips_endpoint = clip_api.root.add_resource("clips")

        ecr_image = lambda_.EcrImageCode.from_asset_image(
            directory=os.path.join(os.getcwd(), 'lambdas', 'downloader')
        )

        downloader = lambda_.Function(self,
                                      'ClipDownloader',
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
                                   public_read_access=True,
                                   lifecycle_rules=[lifetime])

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
                                  description='MediaConvert job queuer',
                                  handler='handler',
                                  index='handler.py',
                                  initial_policy=[
                                      mediaconvert_create_job, mediaconvert_pass_role],
                                  entry=os.path.join(
                                      os.getcwd(), 'lambdas', 'renderer'),
                                  runtime=lambda_.Runtime.PYTHON_3_8,
                                  environment={
                                      'OUT_BUCKET': combined_clips.bucket_name,
                                      'QUEUE_ARN': mediaconvert_queue.attr_arn,
                                      'QUEUE_ROLE': mediaconvert_role.role_arn
                                  },
                                  memory_size=128)

        mongodb_full_uri = secretsmanager.Secret.from_secret_complete_arn(
            self, 'MONGODB_FULL_URI', MONGODB_FULL_URI_ARN)

        notify_lambda = PythonFunction(self, 'Notify',
                                       description='SES Email Lambda',
                                       handler='handler',
                                       index='handler.py',
                                       entry=os.path.join(
                                           os.getcwd(), 'lambdas', 'notify'),
                                       runtime=lambda_.Runtime.PYTHON_3_8,
                                       environment={
                                           'FROM_EMAIL': 'steven@pillar.gg',

                                       },
                                       memory_size=256,
                                       timeout=cdk.Duration.seconds(60))

        ses_email_role = iam.PolicyStatement(
            actions=['ses:SendEmail', 'ses:SendRawEmail'], resources=['*'])
        notify_lambda.add_to_role_policy(ses_email_role)

        get_clips_task = stp_tasks.LambdaInvoke(self, "Download Individual Clips",
                                                lambda_function=downloader
                                                )

        render_video_task = stp_tasks.LambdaInvoke(self, "Call Mediaconvert", heartbeat=cdk.Duration.seconds(600),
                                                   result_path="$.mediaConvertResult", lambda_function=renderer, integration_pattern=stepfunctions.IntegrationPattern.WAIT_FOR_TASK_TOKEN, payload=stepfunctions.TaskInput.from_object({"individualClips.$": "$.downloadResult.individualClips", "userId.$": "$.user.id", "TaskToken": stepfunctions.JsonPath.task_token}))

        notify_task = stp_tasks.LambdaInvoke(self, "Send Email",
                                             lambda_function=notify_lambda)

        process_clips = stepfunctions.Map(
            self, "Process Clips", items_path="$.data.clips",  result_selector={"individualClips.$": "$[*].Payload"}, result_path="$.downloadResult",  parameters={"clip.$": "$$.Map.Item.Value", "index.$": "$$.Map.Item.Index", "videoId.$": "$.data.videoId"}).iterator(get_clips_task)

        yt_upload_fn = PythonFunction(self, 'Youtube Upload',
                                      handler='handler',
                                      index='handler.py',
                                      entry=os.path.join(
                                          os.getcwd(), 'lambdas', 'yt_upload'),
                                      runtime=lambda_.Runtime.PYTHON_3_8,
                                      timeout=cdk.Duration.seconds(30),
                                      memory_size=128,
                                      environment={
                                          'TWITCH_CLIENT_ID': TWITCH_CLIENT_ID,
                                      })
        upload_to_youtube_question = stepfunctions.Choice(
            self, "Upload To Youtube?"
        )


        upload_to_yt_task = stp_tasks.LambdaInvoke(self, "Upload To Youtube",
                                             lambda_function=yt_upload_fn)
        mongodb_full_uri.grant_read(yt_upload_fn)

        definition = process_clips.next(render_video_task).next(upload_to_youtube_question.when(stepfunctions.Condition.boolean_equals("$.data", True), upload_to_yt_task).otherwise(notify_task))
        state_machine = stepfunctions.StateMachine(self, "Renderer",
                                                   definition=definition
                                                   )

        request_template = {"application/json": json.dumps(
            {"stateMachineArn": state_machine.state_machine_arn, "input": "{\"data\": $util.escapeJavaScript($input.json('$')), \"user\": $util.escapeJavaScript($context.authorizer.user)}"})}
        api_role = iam.Role(self, "ClipApiRole", assumed_by=iam.ServicePrincipal(
            "apigateway.amazonaws.com"))
        state_machine.grant_start_execution(api_role)
        integrationResponses = [
            apigateway.IntegrationResponse(selection_pattern="200",
                                           status_code="200",
                                           response_parameters={
                                               "method.response.header.Access-Control-Allow-Origin": "'*'"},
                                           response_templates={
                                               "application/json": "$input.json('$')",

                                           })
        ]
        integration = apigateway.AwsIntegration(service='states', action='StartExecution', options=apigateway.IntegrationOptions(
            credentials_role=api_role, request_templates=request_template, integration_responses=integrationResponses))

        method_responses = [apigateway.MethodResponse(status_code="200", response_parameters={"method.response.header.Access-Control-Allow-Origin": True}, response_models={
                                                      "application/json": apigateway.EmptyModel()})]

        auth_fn = PythonFunction(self, 'Authorizer',
                                 handler='handler',
                                 index='handler.py',
                                 entry=os.path.join(
                                     os.getcwd(), 'lambdas', 'authorizer'),
                                 runtime=lambda_.Runtime.PYTHON_3_8,
                                 timeout=cdk.Duration.seconds(30),
                                 memory_size=128,
                                 environment={
                                     'TWITCH_CLIENT_ID': TWITCH_CLIENT_ID,
                                 })

        auth = apigateway.TokenAuthorizer(
            self, 'Token Authorizer', handler=auth_fn)

        clips_endpoint.add_method(
            "POST", integration, method_responses=method_responses, authorizer=auth)

        events_rule = events.Rule(self, "TranscodingFinished", rule_name="MediaConvertFinished", event_pattern=events.EventPattern(source=[
                                  "aws.mediaconvert"], detail_type=["MediaConvert Job State Change"], detail={"queue": [mediaconvert_queue.attr_arn]}), targets=[events_targets.LambdaFunction(transcoding_finished)])
        transcoding_finished.add_to_role_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, actions=[
                                                "states:SendTask*"], resources=[state_machine.state_machine_arn]))
