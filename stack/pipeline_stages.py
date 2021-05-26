import typing

from aws_cdk.core import CfnOutput, Construct, Stage, Environment
from stack.stack import RenderLambdaStack

class PreprodStage(Stage):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        service = RenderLambdaStack(self, 'PreProdRenderStack', 'preprod')

class ProdStage(Stage):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        service = RenderLambdaStack(self, 'ProdRenderStack', mongodb_database='pillar')
    
