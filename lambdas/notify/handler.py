import os
import boto3


FROM_EMAIL = os.getenv('FROM_EMAIL')
email_client = boto3.client('ses')


def nth_repl(s, sub, repl, n):
    find = s.find(sub)
    # If find is not -1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != n:
        # find + 1 means we start searching from after the last match
        find = s.find(sub, find + 1)
        i += 1
    # If i is equal to n we found nth match so replace
    if i == n:
        return s[:find] + repl + s[find+len(sub):]
    return s

# formats s3 url to a http url
def s3_to_http(s3_url):
    return nth_repl(s3_url, '/', '.s3.amazonaws.com/', 3).replace('s3://', 'https://')


def handler(event, context):
    s3_url = event['mediaConvertResult']['outputFilePath']
    request_email = event['user']['email']
    display_name = event['user']['display_name']


    compilation_file_url = s3_to_http(s3_url)



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
