import os

import pymongo
import boto3

cached_uri = None
cached_db = None

MONGODB_SECRET_NAME = 'MONGODB_FULL_URI'
db_name = os.getenv('DB_NAME')


def connect_to_db():
    global cached_uri
    global cached_db
    if (cached_db):
        return cached_db

    if (not cached_uri):
        session = boto3.session.Session()
        secret_client = session.client(
            service_name='secretsmanager'
        )
        cached_uri = secret_client.get_secret_value(
            SecretId=MONGODB_SECRET_NAME)['SecretString']
    client = pymongo.MongoClient(cached_uri)
    db = client[db_name]
    return db
