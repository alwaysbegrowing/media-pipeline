#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from stack.stack import RenderLambdaStack

app = cdk.App()

# Dev Stack
# This is the development or the "Hack stack"
# and will change regularly.
RenderLambdaStack(app, "RenderLambdaStack", 'dev',
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

# Prod Stack
# this is the production stack and 
# gets automatically deployed by CI.
# DO NOT TOUCH!
RenderLambdaStack(app, "Prod-Render", 'pillar',
                  env=cdk.Environment(account='576758376358', region='us-east-1')
)

app.synth()
