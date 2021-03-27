import os

from aws_cdk import core as cdk
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_mediaconvert as mediaconvert
from aws_cdk.aws_lambda_event_sources import SqsEventSource

class CombineLambdaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        queue = sqs.Queue(self, "ClipInputQueue")

        event_source = SqsEventSource(queue=queue, batch_size=1, enabled=True)

        sqs_lambda = _lambda.Function(self, 'ClipInputLambda',
            handler='handler.handler',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(path=os.path.join('lambda'))
        )

        sqs_lambda.add_event_source(event_source)
