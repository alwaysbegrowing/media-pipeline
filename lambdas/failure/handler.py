import os
import boto3
import slack

from get_secret import get_secret

FROM_EMAIL = os.getenv('FROM_EMAIL')
SLACK_TOKEN_ARN = os.getenv('SLACK_TOKEN_ARN')
SLACK_TOKEN = get_secret(SLACK_TOKEN_ARN)
email_client = boto3.client('ses')


def handler(event, context):

    # get email and display name from event user
    email = event['user']['email']
    display_name = event['user']['display_name']

    # get the Error from the event
    error = event['Error']

    message = error['Cause']
    error_name = error['Error']

    print(message)

    # construct the email body
    html = f'''
            <body>
            {display_name}, <br>
            There was an error creating the compilation :( <br>
            Please reply to this email and we will be happy to fix it!<br>
            Here are more details on the error:<br>
            <br>
            <b>Error Name:</b> {error_name}<br>
    '''

    slack_message = f'''
        Client Display Name: {display_name} \n
        Client Email: {email} \n
        Error Name: {error_name} \n
        Error Message: {message}
    '''

    client = slack.WebClient(token=SLACK_TOKEN)

    # send the slack message
    response = client.chat_postMessage(
        channel='#failures',
        text=slack_message,
        username=error,
        icon_emoji=':robot_face:'
    )

    # send the email
    response = email_client.send_email(
        Source=FROM_EMAIL,
        Destination={
            'BccAddresses': [
                email,
            ],
        },
        Message={
            'Subject': {
                'Data': 'Error creating compilation',
            },
            'Body': {
                'Html': {
                    'Data': html,
                },
            },
        },
    )

    return response
