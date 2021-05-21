#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from stack.stack import RenderLambdaStack
from stack.pipelines import RenderLambdaPipeline, ProdRenderLambdaPipeline

app = cdk.App()

# Testing Stack
RenderLambdaStack(app, "RenderLambdaStack", 
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

# staging pipeline
RenderLambdaPipeline(app, 'PreProdRenderLambdaPipeline')

# production pipeline
ProdRenderLambdaPipeline(app, 'ProdRenderLambdaPipeline')

app.synth()
