import json

import boto3

cached_yt_secrets = None


def get_yt_secrets():
    global cached_yt_secrets
    YT_SECRET_NAME = "YT_CREDENTIALS"

    if (not cached_yt_secrets):
        session = boto3.session.Session()
        secret_client = session.client(
            service_name='secretsmanager'
        )
        cached_yt_secrets = secret_client.get_secret_value(
            SecretId=YT_SECRET_NAME)['SecretString']
    yt_secrets = json.loads(cached_yt_secrets)
    yt_client_id = yt_secrets['YT_CLIENT_ID']
    yt_client_secret = yt_secrets['YT_CLIENT_SECRET']
    return yt_client_id, yt_client_secret
