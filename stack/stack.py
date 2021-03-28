import os

from aws_cdk.aws_lambda_event_sources import SqsEventSource

from aws_cdk import (core as cdk,
                     aws_apigateway as apigateway,
                     aws_sqs as sqs,
                     aws_lambda as lambda_,
                     aws_mediaconvert as mediaconvert)


class RenderLambdaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        mediaconvert_queue = mediaconvert.CfnQueue(self, id="ClipCombiner")


        clip_api = apigateway.RestApi(self, "clip-api",
                                 rest_api_name="Clips service",
                                 description="Service handles combining clips")

        clip_queuer = lambda_.Function(self, 'ClipQueuer',
                                      handler='handler.handler',
                                      runtime=lambda_.Runtime.PYTHON_3_8,
                                      code=lambda_.Code.from_asset(
                                          path=os.path.join('lambdas/clip_queuer')),
                                      environment={
                                          'MEDIA_QUEUE': mediaconvert_queue.attr_arn}
                                      )

        getfromQueue = apigateway.LambdaIntegration(clip_queuer,
                request_templates={"application/json": '{ "statusCode": "200" }'})

        clips_endpoint = clip_api.root.add_resource("clips")

        clips_endpoint.add_method("POST", getfromQueue)
        clips_endpoint.add_method("GET", getfromQueue)


        queue = sqs.Queue(self, "ClipInputQueue")

        event_source = SqsEventSource(queue=queue, batch_size=1, enabled=True)


        sqs_lambda = lambda_.Function(self, 'ClipCreator',
                                      handler='handler.handler',
                                      runtime=lambda_.Runtime.PYTHON_3_8,
                                      code=lambda_.Code.from_asset(
                                          path=os.path.join('lambdas/clip_creator')),
                                      environment={
                                          'MEDIA_QUEUE': mediaconvert_queue.attr_arn}
                                      )

        sqs_lambda.add_event_source(event_source)
