import os

import slack

from get_secret import get_secret

SLACK_TOKEN_ARN = os.getenv('SLACK_TOKEN_ARN')
SLACK_TOKEN = get_secret(SLACK_TOKEN_ARN)


def replace_nth_occurrence(s, sub, repl, n):
    '''
    # https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string
    # In [14]: s = "foobarfoofoobarbar"

    # In [15]: replace_nth_occurrence(s, "bar","replaced",3)
    # Out[15]: 'foobarfoofoobarreplaced'

    # In [16]: replace_nth_occurrence(s, "foo","replaced",3)
    # Out[16]: 'foobarfooreplacedbarbar'

    # In [17]: replace_nth_occurrence(s, "foo","replaced",5)
    # Out[17]: 'foobarfoofoobarbar'
    '''
    find = s.find(sub)
    i = find != -1
    while find != -1 and i != n:
        find = s.find(sub, find + 1)
        i += 1
    if i == n:
        return s[:find] + repl + s[find + len(sub):]
    return s

# formats s3 url to a http url


def s3_to_http(s3_url):
    return replace_nth_occurrence(
        s3_url,
        '/',
        '.s3.amazonaws.com/',
        3).replace(
        's3://',
        'https://')


def send_slack_message(display_name, request_email, error_name, error_message):
    slack_message = f'''
        Client Display Name: {display_name}
        Client Email: {request_email}
        Error Name: {error_name}
        Error Message: {error_message}
    '''
    client = slack.WebClient(token=SLACK_TOKEN)
    client.chat_postMessage(
        channel='#pillar-robots',
        text=slack_message,
        username='Media Pipeline Error',
        icon_emoji=':robot_face:'
    )
