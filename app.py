#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from stack.stack import RenderLambdaStack
from stack.pipelines import RenderLambdaPipeline, ProdRenderLambdaPipeline

app = cdk.App()

# Testing Stack
RenderLambdaStack(app, "RenderLambdaStack", 'dev',
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

RenderLambdaStack(app, "Prod-Render", 'pillar',
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

RenderLambdaStack(app, "QA-Render", 'preprod',
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

app.synth()
