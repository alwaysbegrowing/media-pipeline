#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from stack.stack import RenderLambdaStack

app = cdk.App()

# production. Will be deployed from GitHub Actions CI on `master` branch
RenderLambdaStack(app, "RenderLambdaStack", 
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

# staging. Will be deployed from GitHub Actions CI on `develop` branch
RenderLambdaStack(app, "StagingRenderLambda", 
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

# For development only
RenderLambdaStack(app, "DevRenderLambda", 
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

app.synth()
