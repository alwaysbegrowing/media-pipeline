import json
import boto3
stepfunctions = boto3.client('stepfunctions')


def handler(event, context):
    print(f'event: {json.dumps(event)}')
    user_metadata = event['detail']['userMetadata']
    token = f'{user_metadata["TaskToken1"]}{user_metadata["TaskToken2"]}{user_metadata["TaskToken3"]}'

    if (event['detail']['status'] == "COMPLETE"):
        if 'Mobile' in event['detail']['queue']:
            outputData = {}
            outputGroupDetails = event['detail']['outputGroupDetails']
            # all of these are stored in arrays,
            # this guarantees it
            # will check all data
            for outputGroup in outputGroupDetails:
                outputDetails = outputGroup['outputDetails']
                for outputDetail in outputDetails:
                    outputFilePaths = outputDetail['outputFilePaths']
                    for path in outputFilePaths:
                        if 'background' in path:
                            outputData['background_file'] = path
                        if 'content' in path:
                            outputData['content_file'] = path
                        if 'facecam' in path:
                            outputData['facecam_file'] = path

            stepfunctions.send_task_success(
                taskToken=token, output=json.dumps(outputData))
        else:
            stepfunctions.send_task_success(taskToken=token, output=json.dumps(
                {'outputFilePath': event['detail']['outputGroupDetails'][0]['outputDetails'][0]['outputFilePaths'][0]}))

    if (event['detail']['status'] == "STATUS_UPDATE"):
        stepfunctions.send_task_heartbeat(taskToken=token)

    if (event['detail']['status'] == "ERROR"):
        stepfunctions.send_task_failure(
            taskToken=token,
            error=event['detail']['errorCode'],
            cause=event['detail']['errorMessage'])
