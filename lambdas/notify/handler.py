import os
import boto3


FROM_EMAIL = os.getenv('FROM_EMAIL')
email_client = boto3.client('ses')

def handler(event, context):
    bucket = event['mediaConvertResult']['Bucket']
    Key = event['mediaConvertResult']['Key']
    request_email = event['user']['email']
    display_name = event['user']['display_name']


    compilation_file_url = 'https://' + bucket + '.s3.amazonaws.com' + '/' + Key
   

    html = f'''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
  <meta http-equiv="Content-Type" content="text/html charset=UTF-8" />
  <head>
  </head>
  <body>
  {display_name}, <br>
  Here is your Pillar compilation: <br>
  
  {compilation_file_url}
  <br>
  Thanks for using Pillar! <br>
  See you soon, <br>
  The Pillar Team
      </body>
</html>
    '''

    email_client.send_email(
        Source=FROM_EMAIL,
        Destination={
            'BccAddresses': [
                request_email,
            ]
        },
        Message={
            'Subject': {
                'Data': 'Pillar - Your video is ready (link inside)'
            },
            'Body': {
                'Html': {
                    'Data': html
                }
            }
        }
    )

    return {'statusCode': 200}
