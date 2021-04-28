#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's cdk module.  The following line also imports it as `cdk` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.

from stack.stack import RenderLambdaStack


app = cdk.App()

# production. Will be deployed from GitHub Actions CI on `master` branch
RenderLambdaStack(app, "RenderLambdaStack")

# staging. Will be deployed from GitHub Actions CI on `develop` branch
RenderLambdaStack(app, "StagingRenderLambda")

# For development only
RenderLambdaStack(app, "DevRenderLambda")

app.synth()
