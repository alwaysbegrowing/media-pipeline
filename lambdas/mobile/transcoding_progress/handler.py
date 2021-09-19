# this will be modified to wait until after
# the transcode is done, then pass the output
# into the next step function

import json
import boto3
stepfunctions = boto3.client('stepfunctions')


def handler(event, context):
    print('event', event)
    user_metadata = event['detail']['userMetadata']
    token = f'{user_metadata["TaskToken1"]}{user_metadata["TaskToken2"]}{user_metadata["TaskToken3"]}'

    if (event['detail']['status'] == "COMPLETE"):
        print(event)
        stepfunctions.send_task_success(taskToken=token, output=json.dumps(
            {'outputFilePath': event['detail']['outputGroupDetails'][0]['outputDetails'][0]['outputFilePaths'][0]}))

    if (event['detail']['status'] == "STATUS_UPDATE"):
        stepfunctions.send_task_heartbeat(taskToken=token)

    if (event['detail']['status'] == "ERROR"):
        stepfunctions.send_task_failure(
            taskToken=token,
            error=event['detail']['errorCode'],
            cause=event['detail']['errorMessage'])
