from datetime import datetime

import boto3

# misc functions


def json_handler(item):
    if type(item) is datetime:
        return item.isoformat()
    else:
        return str(item)


def get_secret(arn):
    client = boto3.client('secretsmanager')
    resp = client.get_secret_value(SecretId=arn)
    return resp.get('SecretString')
