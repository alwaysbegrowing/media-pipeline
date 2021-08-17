import json
import boto3
stepfunctions = boto3.client('stepfunctions')

def handler(event, context):
    print('event', event)
    user_metadata = event['detail']['userMetadata']
    token = f'{user_metadata["TaskToken1"]}{user_metadata["TaskToken2"]}{user_metadata["TaskToken3"]}'

    if (event['detail']['status'] == "COMPLETE"):
        stepfunctions.send_task_success(taskToken=token, output=json.dumps({'status': 'complete'}))
    
    if (event['detail']['status'] == "STATUS_UPDATE"):
        stepfunctions.send_task_heartbeat(taskToken=token)
    
    if (event['detail']['status'] == "ERROR"):
        stepfunctions.send_task_failure(taskToken=token, error=event['detail']['errorMessage'])