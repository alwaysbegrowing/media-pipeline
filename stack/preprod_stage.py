import typing

from aws_cdk.core import CfnOutput, Construct, Stage, StageProps
from stack.stack import RenderLambdaStack

class PreprodStage(Stage):
    def __init__(self, scope: Construct, id: str, props: StageProps) -> None:
        super().__init__(scope, id, props)

        service = RenderLambdaStack(self, 'RenderStack')

        