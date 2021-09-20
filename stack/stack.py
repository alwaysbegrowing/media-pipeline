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
MONGODB_FULL_URI_ARN = 'arn:aws:secretsmanager:us-east-1:576758376358:secret:MONGODB_FULL_URI-DBSAtt'
YT_CREDENTIALS = 'arn:aws:secretsmanager:us-east-1:576758376358:secret:YT_CREDENTIALS-7vn4OJ'


class RenderLambdaStack(cdk.Stack):

    def __init__(
            self,
            scope: cdk.Construct,
            construct_id: str,
            mongo_db_database: str = 'pillar',
            **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lifetime = s3.LifecycleRule(expiration=cdk.Duration.days(
            30), enabled=True, id='30-Day-Retention')

        individual_clips = s3.Bucket(scope=self,
                                     id="IndividualClips",
                                     public_read_access=True,
                                     lifecycle_rules=[lifetime])

        cors = apigateway.CorsOptions(
            allow_origins=apigateway.Cors.ALL_ORIGINS)

        clip_api = apigateway.RestApi(
            self,
            "clip-api",
            rest_api_name="Clips service",
            description="Service handles combining clips",
            default_cors_preflight_options=cors)

        transcoding_finished = PythonFunction(
            self,
            'transcoding_finished',
            handler='handler',
            index='handler.py',
            entry=os.path.join(
                os.getcwd(),
                'lambdas',
                'transcoding_progress'),
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(60),
            memory_size=128)

        clips_endpoint = clip_api.root.add_resource("clips")

        ecr_image = lambda_.EcrImageCode.from_asset_image(
            directory=os.path.join(os.getcwd(), 'lambdas', 'downloader')
        )

        downloader = lambda_.Function(
            self,
            'ClipDownloader',
            description="Containerized Clip Downloader",
            code=ecr_image,
            handler=lambda_.Handler.FROM_IMAGE,
            runtime=lambda_.Runtime.FROM_IMAGE,
            environment={
                'BUCKET': individual_clips.bucket_name},
            timeout=cdk.Duration.seconds(240),
            memory_size=1024)

        individual_clips.grant_write(downloader)

        combined_clips = s3.Bucket(scope=self,
                                   id="CombinedClips",
                                   public_read_access=True,
                                   lifecycle_rules=[lifetime])

        mediaconvert_queue = mediaconvert.CfnQueue(self, id="ClipCombiner")

        mediaconvert_role = iam.Role(
            self,
            "MediaConvert",
            assumed_by=iam.ServicePrincipal("mediaconvert.amazonaws.com"))
        individual_clips.grant_read(mediaconvert_role)
        combined_clips.grant_write(mediaconvert_role)

        mediaconvert_create_job = iam.PolicyStatement(
            actions=['mediaconvert:CreateJob'], resources=[
                mediaconvert_queue.attr_arn])

        mediaconvert_pass_role = iam.PolicyStatement(
            actions=[
                "iam:PassRole",
                "iam:ListRoles"],
            resources=["arn:aws:iam::*:role/*"])

        renderer = PythonFunction(
            self,
            'FinalRenderer',
            description='MediaConvert job queuer',
            handler='handler',
            index='handler.py',
            initial_policy=[
                mediaconvert_create_job,
                mediaconvert_pass_role],
            entry=os.path.join(
                os.getcwd(),
                'lambdas',
                'renderer'),
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                'OUT_BUCKET': combined_clips.bucket_name,
                'QUEUE_ARN': mediaconvert_queue.attr_arn,
                'QUEUE_ROLE': mediaconvert_role.role_arn},
            memory_size=128)

        mongodb_full_uri = secretsmanager.Secret.from_secret_complete_arn(
            self, 'MONGODB_FULL_URI', MONGODB_FULL_URI_ARN)

        youtube_secrets = secretsmanager.Secret.from_secret_complete_arn(
            self, 'YT_CREDENTIALS', YT_CREDENTIALS)

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

        notify_task = stp_tasks.LambdaInvoke(self, "Send Email",
                                             lambda_function=notify_lambda)

        send_failure_email = stp_tasks.LambdaInvoke(
            self, "Send Mobile Export Failure Email", lambda_function=notify_lambda)

        get_clips_task = stp_tasks.LambdaInvoke(
            self, "Download Individual Clips", lambda_function=downloader).add_catch(
            send_failure_email, result_path="$.Error")

        render_video_task = stp_tasks.LambdaInvoke(
            self,
            "Call Mediaconvert",
            heartbeat=cdk.Duration.seconds(600),
            result_path="$.mediaConvertResult",
            lambda_function=renderer,
            integration_pattern=stepfunctions.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
            payload=stepfunctions.TaskInput.from_object(
                {
                    "individualClips.$": "$.downloadResult.individualClips",
                    "displayName.$": "$.user.display_name",
                    "TaskToken": stepfunctions.JsonPath.task_token}))

        process_clips = stepfunctions.Map(
            self,
            "Process Clips",
            items_path="$.data.clips",
            result_selector={
                "individualClips.$": "$[*].Payload"},
            result_path="$.downloadResult",
            parameters={
                "clip.$": "$$.Map.Item.Value",
                "index.$": "$$.Map.Item.Index",
                "videoId.$": "$.data.videoId"}).iterator(get_clips_task)

        yt_upload_fn = PythonFunction(self, 'Youtube Upload',
                                      handler='handler',
                                      index='handler.py',
                                      entry=os.path.join(
                                          os.getcwd(), 'lambdas', 'yt_upload'),
                                      runtime=lambda_.Runtime.PYTHON_3_8,
                                      timeout=cdk.Duration.seconds(30),
                                      memory_size=1024,
                                      environment={
                                          'TWITCH_CLIENT_ID': TWITCH_CLIENT_ID,
                                          'DB_NAME': mongo_db_database,
                                      })

        upload_to_youtube_question = stepfunctions.Choice(
            self, "Upload To Youtube?"
        )

        upload_to_yt_task = stp_tasks.LambdaInvoke(
            self,
            "Upload To Youtube",
            result_selector={
                "youtubeData.$": "$.Payload"},
            lambda_function=yt_upload_fn,
            result_path="$.UploadToYoutubeResult")
        mongodb_full_uri.grant_read(yt_upload_fn)
        youtube_secrets.grant_read(yt_upload_fn)
        combined_clips.grant_read(yt_upload_fn)

        definition = process_clips.next(render_video_task).next(
            upload_to_youtube_question.when(
                stepfunctions.Condition.boolean_equals(
                    "$.data.uploadToYoutube",
                    True),
                upload_to_yt_task.next(notify_task)).otherwise(notify_task))
        state_machine = stepfunctions.StateMachine(self, "Renderer",
                                                   definition=definition
                                                   )

        # This transforms the input into the format that the step functions are expecting.
        # they expect input with the input data being a string https://docs.aws.amazon.com/step-functions/latest/dg/tutorial-api-gateway.html#api-gateway-step-3
        # this gets complicated with the mapping template utils https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html#util-template-reference
        # the replace variable is to fix https://github.com/pillargg/pillar.gg/issues/164
        # all the code below does is manipulation on the input to get the mapping template to look like
        # {"input": "{\"data\": $util.escapeJavaScript($input.json('$')).replaceAll("\\'", "'"), \"user\": $util.escapeJavaScript($context.authorizer.user)}", "stateMachineArn": "arn:aws:states:us-east-1:576758376358:stateMachine:RendererE9DA6252-h0z0K3nEWfic"}
        replace = "replacement_string"
        input_data = "$util.escapeJavaScript($input.json('$'))" + replace
        auth_data = "$util.escapeJavaScript($context.authorizer.user)"
        step_function_input = f'{{\"data\": {input_data}, \"user\": {auth_data}}}'
        data = {"input": step_function_input,
                "stateMachineArn": state_machine.state_machine_arn}
        json_formatted_data = (json.dumps(data))
        final_data = json_formatted_data.replace(
            'replacement_string', '''.replaceAll("\\\\'", "'")''')
        request_template = {
            "application/json": final_data
        }

        api_role = iam.Role(
            self,
            "ClipApiRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"))
        state_machine.grant_start_execution(api_role)
        integrationResponses = [
            apigateway.IntegrationResponse(
                selection_pattern="200",
                status_code="200",
                response_parameters={
                    "method.response.header.Access-Control-Allow-Origin": "'*'"},
                response_templates={
                    "application/json": "$input.json('$')",
                })]
        integration = apigateway.AwsIntegration(
            service='states',
            action='StartExecution',
            options=apigateway.IntegrationOptions(
                credentials_role=api_role,
                request_templates=request_template,
                integration_responses=integrationResponses))

        method_responses = [
            apigateway.MethodResponse(
                status_code="200",
                response_parameters={
                    "method.response.header.Access-Control-Allow-Origin": True},
                response_models={
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
            "POST",
            integration,
            method_responses=method_responses,
            authorizer=auth)

        events_rule = events.Rule(
            self,
            "TranscodingFinished",
            rule_name=f"MediaConvertFinished-{construct_id}",
            event_pattern=events.EventPattern(
                source=["aws.mediaconvert"],
                detail_type=["MediaConvert Job State Change"],
                detail={
                    "queue": [
                        mediaconvert_queue.attr_arn]}),
            targets=[
                events_targets.LambdaFunction(transcoding_finished)])
        transcoding_finished.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["states:SendTask*"],
                resources=[
                    state_machine.state_machine_arn]))

        # mobile export section

        # API input will look something like this:
        # {
        #   "ClipData": {
        #     "videoId": 857674564,
        #     "clip": {
        #       "starTime": 30,
        #       "endTime": 120
        #     }
        #   },
        #   "Outputs": {
        #         "background": {
        #             "bucket": "bucket_name",
        #             "x": 100,
        #             "y": 100,
        #             "width": 100,
        #             "height": 100,
        #             "res_x": 100,
        #             "res_y": 100
        #         }
        #     }
        # }

        # mobile export queue
        mobile_mediaconvert_queue = mediaconvert.CfnQueue(
            self, id="MobileExportRender")

        # mobile mediaconvert role setup
        mobile_mediaconvert_role = iam.Role(
            self,
            "MediaConvertMobile",
            assumed_by=iam.ServicePrincipal("mediaconvert.amazonaws.com"))
        individual_clips.grant_read(mediaconvert_role)

        mobile_mediaconvert_create_job = iam.PolicyStatement(
            actions=['mediaconvert:CreateJob'], resources=[
                mobile_mediaconvert_queue.attr_arn])

        # background clips s3 bucket
        cropped_clips_bucket = s3.Bucket(
            scope=self, id="CroppedClipsBucket", lifecycle_rules=[lifetime])
        cropped_clips_bucket.grant_write(mobile_mediaconvert_role)

        # mobile export bucket
        mobile_export_bucket = s3.Bucket(scope=self,
                                         id="MobileExportBucket",
                                         lifecycle_rules=[lifetime],
                                         public_read_access=True)

        # mobile export api
        mobile_export_api = apigateway.RestApi(self, "MobileExportApi",
                                               rest_api_name=f"MobileExportApi-{construct_id}",
                                               description="Mobile export api",
                                               default_cors_preflight_options=cors)

        # python crop lambda
        crop_lambda = PythonFunction(self, "Crop Lambda",
                                     handler='handler',
                                     index='handler.py',
                                     entry=os.path.join(
                                         os.getcwd(), 'lambdas', 'mobile', 'crop'),
                                     runtime=lambda_.Runtime.PYTHON_3_8,
                                     timeout=cdk.Duration.seconds(30),
                                     memory_size=128,
                                     initial_policy=[  # reuse policy statements from above: mediaconvert_pass_role, mediaconvert_create_job
                                         mobile_mediaconvert_create_job,
                                         mediaconvert_pass_role
                                     ],
                                     environment={
                                         'IN_BUCKET': individual_clips.bucket_name,
                                         'OUT_BUCKET': cropped_clips_bucket.bucket_name,
                                         'MEDIACONVERT_ARN': mobile_mediaconvert_queue.attr_arn,
                                         'ROLE_ARN': mobile_mediaconvert_role.role_arn,
                                     })

        cropped_clips_bucket.grant_write(crop_lambda)
        individual_clips.grant_read(crop_lambda)

        # docker combiner lambda
        mobile_ecr_image = lambda_.EcrImageCode.from_asset_image(
            directory=os.path.join(
                os.getcwd(), 'lambdas', 'mobile', 'combine'),
        )

        combiner_lambda = lambda_.Function(self, "MobileCombiner",
                                           code=mobile_ecr_image,
                                           handler=lambda_.Handler.FROM_IMAGE,
                                           runtime=lambda_.Runtime.FROM_IMAGE,
                                           environment={
                                               'IN_BUCKET': cropped_clips_bucket.bucket_name,
                                               'OUT_BUCKET': mobile_export_bucket.bucket_name,
                                           },
                                           timeout=cdk.Duration.minutes(10),
                                           memory_size=3096)

        cropped_clips_bucket.grant_read(combiner_lambda)
        mobile_export_bucket.grant_read_write(combiner_lambda)

        # mobile transcoding progress lambda
        transcoding_progress_lambda = PythonFunction(self, "TranscodingProgressLambda",
                                                     handler='handler',
                                                     index='handler.py',
                                                     entry=os.path.join(
                                                         os.getcwd(), 'lambdas', 'mobile', 'transcoding_progress'),
                                                     runtime=lambda_.Runtime.PYTHON_3_8,
                                                     timeout=cdk.Duration.seconds(
                                                         30),
                                                     memory_size=128)

        # state machine definition

        send_mobile_failure_email = stp_tasks.LambdaInvoke(
            self, "Send Failure Email", lambda_function=notify_lambda)

        # download clip task
        download_clip_task = stp_tasks.LambdaInvoke(self, "Download Clip",
                                                    lambda_function=downloader,
                                                    input_path="$.ClipData",
                                                    result_selector={
                                                        'file.$': '$.Payload.file'
                                                    },
                                                    result_path="$.ClipName",
                                                    output_path="$"
                                                    ).add_catch(
            send_mobile_failure_email, result_path="$.Error")

        # crop video task
        crop_video_task = stp_tasks.LambdaInvoke(self, "Crop Video",
                                                 lambda_function=crop_lambda,
                                                 heartbeat=cdk.Duration.seconds(
                                                     30),
                                                 result_path="$.crop",
                                                 output_path="$",
                                                 integration_pattern=stepfunctions.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
                                                 payload=stepfunctions.TaskInput.from_object(
                                                     {
                                                         "TaskToken": stepfunctions.JsonPath.task_token,
                                                         "ClipName.$": "$.ClipName.file",
                                                         "Outputs.$": "$.Outputs"
                                                     }
                                                 )
                                                 )

        combine_video_task = stp_tasks.LambdaInvoke(self, "Combine Video",
                                                    lambda_function=combiner_lambda,
                                                    result_path="$.combine",
                                                    input_path="$.crop",
                                                    output_path="$"
                                                    )

        mobile_notify_task = stp_tasks.LambdaInvoke(self, "Send Mobile Notification Email",
                                                    lambda_function=notify_lambda,
                                                    payload=stepfunctions.TaskInput.from_object({
                                                        "mediaConvertResults": {
                                                            "outputFilePath.$": "$.combine.output_file"
                                                        },
                                                        "user.$": "$.user"
                                                    })
                                                    )

        mobile_definition = download_clip_task.next(crop_video_task).next(
            combine_video_task).next(mobile_notify_task)

        mobile_export_state_machine = stepfunctions.StateMachine(
            self, "MobileExporter", definition=mobile_definition)

        mobile_api_role = iam.Role(
            self,
            "MobileExportApiRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"))
        mobile_export_state_machine.grant_start_execution(mobile_api_role)
        mobileIntegrationResponses = [
            apigateway.IntegrationResponse(
                selection_pattern="200",
                status_code="200",
                response_parameters={
                    "method.response.header.Access-Control-Allow-Origin": "'*'"},
                response_templates={
                    "application/json": "$input.json('$')",
                })]

        mobileIntegration = apigateway.AwsIntegration(
            service='states',
            action='StartExecution',
            options=apigateway.IntegrationOptions(
                credentials_role=mobile_api_role,
                request_templates=request_template,
                integration_responses=mobileIntegrationResponses))

        mobile_export_endpoint = mobile_export_api.root.add_resource("export")

        # mobile_export_auth = apigateway.TokenAuthorizer(
        #     self, 'Mobile Export Token Authorizer', handler=auth_fn)

        mobile_export_endpoint.add_method(
            "POST",
            mobileIntegration,
            method_responses=method_responses,)
        # authorizer=mobile_export_auth)

        mobile_events_rule = events.Rule(
            self,
            "MobileTranscodingFinished",
            rule_name=f"MediaConvertFinishedMobile-{construct_id}",
            event_pattern=events.EventPattern(
                source=["aws.mediaconvert"],
                detail_type=["MediaConvert Job State Change"],
                detail={
                    "queue": [
                        mobile_mediaconvert_queue.attr_arn]}),
            targets=[
                events_targets.LambdaFunction(transcoding_progress_lambda)])

        transcoding_progress_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["states:SendTask*"],
                resources=[
                    mobile_export_state_machine.state_machine_arn]))
