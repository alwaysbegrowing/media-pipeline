import os

from aws_cdk.aws_lambda_event_sources import SqsEventSource

from aws_cdk import (core as cdk,
                     aws_apigateway as apigateway,
                     aws_sqs as sqs,
                     aws_s3 as s3,
                     aws_lambda as lambda_,
                     aws_mediaconvert as mediaconvert)

from aws_cdk.aws_lambda_python import PythonFunction, PythonLayerVersion


class RenderLambdaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        individual_clips = s3.Bucket(self,
                                     "IndividualClips")

        combined_clips = s3.Bucket(self,
                                   "CombinedClips")

        mediaconvert_queue = mediaconvert.CfnQueue(self, id="ClipCombiner")
        # individual_clips.grant_read(mediaconvert_queue)
        # combined_clips.grant_write(mediaconvert_queue)

        clip_api = apigateway.RestApi(self, "clip-api",
                                      rest_api_name="Clips service",
                                      description="Service handles combining clips")

        # TODO wtf why do I have to specify code as a param here?
        temp_layer = lambda_.LayerVersion(self, "FFMPEG", code=lambda_.Code.from_asset(
            path=os.path.join(
                'lambdas/clip_queuer')
        ))

        ffmpeg_layer=temp_layer.from_layer_version_arn(self, 'ffmpeg',
        layer_version_arn='arn:aws:serverlessrepo:us-east-1:145266761615:applications/ffmpeg-lambda-layer')

        clip_queuer = PythonFunction(self, 'ClipQueuer',
                                     handler='handler',
                                     index='handler.py',
                                     entry='./lambdas/clip_queuer',
                                     runtime=lambda_.Runtime.PYTHON_3_8,
                                     environment={
                                         'MEDIA_QUEUE': mediaconvert_queue.attr_arn,
                                         'BUCKET': individual_clips.bucket_name
                                     },
                                     layers=[ffmpeg_layer]

                                     )



        #    layer = lambda_.LayerVersion(self, 'FFMPEG', code=None)
        # layer.

        individual_clips.grant_read(clip_queuer)

        getfromQueue = apigateway.LambdaIntegration(clip_queuer,
                                                    request_templates={"application/json": '{ "statusCode": "200" }'})

        clips_endpoint = clip_api.root.add_resource("clips")

        clips_endpoint.add_method("POST", getfromQueue)
