#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from stack.stack import RenderLambdaStack

app = cdk.App()

# Testing Stack
RenderLambdaStack(app, "RenderLambdaStack", 
                  env=cdk.Environment(account='576758376358', region='us-east-1'), mongo_db_database='dev')


RenderLambdaStack(app, "Prod-Render",
                  env=cdk.Environment(account='576758376358', region='us-east-1'), mongo_db_database='pillar')


RenderLambdaStack(app, "QA-Render",
                  env=cdk.Environment(account='576758376358', region='us-east-1'), mongo_db_database='dev')


app.synth()
