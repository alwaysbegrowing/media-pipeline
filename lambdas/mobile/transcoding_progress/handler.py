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
        outputData = {}
        outputGroupDetails = event['detail']['outputGroupDetails']
        # all of these are stored in arrays,
        # this guarantees it will check
        # data
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

    if (event['detail']['status'] == "STATUS_UPDATE"):
        stepfunctions.send_task_heartbeat(taskToken=token)

    if (event['detail']['status'] == "ERROR"):
        stepfunctions.send_task_failure(
            taskToken=token,
            error=event['detail']['errorCode'],
            cause=event['detail']['errorMessage'])
