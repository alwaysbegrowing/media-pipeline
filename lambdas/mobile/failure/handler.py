import os
import boto3

FROM_EMAIL = os.getenv('FROM_EMAIL')
email_client = boto3.client('ses')


def handler(event, context):

    # get email and display name from event user
    email = event['user']['email']
    display_name = event['user']['display_name']

    # get the Error from the event
    error = event['Error']

    message = error['Cause']
    error_name = error['Error']

    # construct the email body
    html = f'''
            <body>
            {display_name}, <br>
            There was an error creating the compilation :( <br>
            Please reply to this email and we will be happy to fix it!<br>
            Here are more details on the error:<br>
            <br>
            <b>Error Name:</b> {error_name}<br>
            <b>Error Cause:</b> <br/> {message}<br>
            '''

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
