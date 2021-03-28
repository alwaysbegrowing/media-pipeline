import os

from aws_cdk import core as cdk
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_mediaconvert as mediaconvert
from aws_cdk.aws_lambda_event_sources import SqsEventSource

class RenderLambdaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        queue = sqs.Queue(self, "ClipInputQueue")

        event_source = SqsEventSource(queue=queue, batch_size=1, enabled=True)


        mediaconvert_queue = mediaconvert.CfnQueue(self, id=f"ClipCombiner")

        sqs_lambda = lambda_.Function(self, 'ClipCreator',
            handler='handler.handler',
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset(path=os.path.join('lambdas/clip_creator')),
            environment={'MEDIA_QUEUE': mediaconvert_queue.attr_arn}
        )


        sqs_lambda.add_event_source(event_source)


