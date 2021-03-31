import os

from aws_cdk.aws_lambda_event_sources import SqsEventSource

from aws_cdk import (core as cdk,
                     aws_apigateway as apigateway,
                     aws_sqs as sqs,
                     aws_s3 as s3,
                     aws_lambda as lambda_,
                     aws_mediaconvert as mediaconvert,
                     aws_stepfunctions as stepfunctions,
                     aws_stepfunctions_tasks as stp_tasks)

from aws_cdk.aws_lambda_python import PythonFunction, PythonLayerVersion


class RenderLambdaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        individual_clips = s3.Bucket(self,
                                     "IndividualClips")

        # API For Frontend
        clip_api = apigateway.RestApi(self, "clip-api",
                                      rest_api_name="Clips service",
                                      description="Service handles combining clips")

        clip_queuer = PythonFunction(self, 'ClipQueuer',
                                     handler='handler',
                                     index='handler.py',
                                     entry=os.path.join(
                                         os.getcwd(), 'lambdas', 'clip_queuer'),
                                     runtime=lambda_.Runtime.PYTHON_3_8,
                                     environment={
                                         'BUCKET': individual_clips.bucket_name
                                     })

        addToQueue = apigateway.LambdaIntegration(clip_queuer,
                                                  request_templates={"application/json": '{ "statusCode": "200" }'})

        clips_endpoint = clip_api.root.add_resource("clips")

        clips_endpoint.add_method("POST", addToQueue)

        # Clip Downloader Container

        image_name = "lambdaClipDownloader"
        image_version = "latest"

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
                                      }
                                      )

        # Final Renderer
        combined_clips = s3.Bucket(self,
                                   "CombinedClips")

        # mediaconvert_queue = mediaconvert.CfnQueue(self, id="ClipCombiner")
        # individual_clips.grant_read(mediaconvert_queue)
        # combined_clips.grant_write(mediaconvert_queue)

        renderer = PythonFunction(self, 'FinalRenderer',
                                  handler='handler',
                                  index='handler.py',
                                  entry=os.path.join(
                                      os.getcwd(), 'lambdas', 'clip_queuer'),
                                  runtime=lambda_.Runtime.PYTHON_3_8,
                                  environment={
                                      'IN_BUCKET': individual_clips.bucket_name,
                                      'OUT_BUCKET': combined_clips.bucket_name
                                  }
                                  )

        # state machine definition

        get_clips_task = stp_tasks.LambdaInvoke(self, "Download Clip",
                                                lambda_function=downloader
                                                )

        render_video_task = stp_tasks.LambdaInvoke(self, "Render Video",
                                                   lambda_function=renderer)

        process_clips = stepfunctions.Map(self, "Process Clips").iterator(get_clips_task)

        success = stepfunctions.Succeed(self, "Video Processing Finished.")

        definition = process_clips.next(render_video_task).next(success)

        stepfunctions.StateMachine(self, "Renderer",
                                   definition=definition
                                   )
