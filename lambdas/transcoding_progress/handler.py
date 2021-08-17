import json
import boto3
stepfunctions = boto3.client('stepfunctions')

def handler(event, context):
    print('event', event)
    user_metadata = event['detail']['userMetadata']
    requester_id = user_metadata['RequesterId']
    bucket = user_metadata['Bucket']
    token = f'{user_metadata["TaskToken1"]}{user_metadata["TaskToken2"]}{user_metadata["TaskToken3"]}'

    if (event['detail']['status'] == "COMPLETE"):
        stepfunctions.send_task_success(
            taskToken=token, output=json.dumps({'RequesterId': requester_id, 'Bucket': bucket, 'Key': event['detail']['outputGroupDetails'][0]['outputDetails'][0]['outputFilePaths'][0].replace(f's3://{bucket}/', "")}))

    if (event['detail']['status'] == "STATUS_UPDATE"):
        stepfunctions.send_task_heartbeat(taskToken=token)

    if (event['detail']['status'] == "ERROR"):
        stepfunctions.send_task_failure(
            taskToken=token, error=event['detail']['errorCode'], cause=event['detail']['errorMessage'])