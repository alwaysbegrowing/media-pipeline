import json

import boto3

cached_yt_secrets = None

def get_yt_secrets():
    global cached_yt_secrets
    yt_secret_name = "YT_CREDENTIALS"

    if (not cached_yt_secrets):
        session = boto3.session.Session()
        secret_client = session.client(
            service_name='secretsmanager'
        )
        cached_yt_secrets = secret_client.get_secret_value(
                SecretId=yt_secret_name)['SecretString']
    return json.loads(cached_yt_secrets)
