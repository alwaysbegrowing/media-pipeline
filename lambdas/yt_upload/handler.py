import os
import boto3


FROM_EMAIL = os.getenv('FROM_EMAIL')
email_client = boto3.client('ses')

def handler(event, context):
    

    return {'statusCode': 200}
