import re

import requests


def twitch_auth(client_id, client_secret):
    queries = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    resp = requests.post('https://id.twitch.tv/oauth2/token', params=queries)
    return resp.json()


def get_ccc_info(twitch_client_id, twitch_client_secret, query):

    if not type(query) is dict:
        raise TypeError('Parameter "query" must be a dictionary!')

    auth = twitch_auth(twitch_client_id, twitch_client_secret)
    print(auth)
    access_token = auth['access_token']
    headers = {
        'Client-Id': twitch_client_id,
        'Authorization': f'Bearer {access_token}'
    }

    resp = requests.get('https://api.twitch.tv/helix/clips',
                        headers=headers, params=query)

    return resp.json()

    # this code can be used if we want to support
    # "highlights", or clips that the streamer themselves
    # created on their twitch VOD. For now this will remain commented out.
    # clip_data = resp.json()

    # if clip_data.get('data'):
    #     return clip_data

    # resp = requests.get('https://api.twitch.tv/helix/videos', headers=headers, params=queries)

    # return resp.json()


def twitch_time_to_seconds(duration):
    total = 0

    hour_list = re.findall(r'\dh', duration)
    if hour_list:
        hour_str = hour_list[0].replace('h', '')
        total += int(hour_str) * 3600

    minute_list = re.findall(r'\dm', duration)
    if minute_list:
        minute_str = minute_list[0].replace('m', '')
        total += int(minute_str) * 60

    second_list = re.findall(r'\ds', duration)
    if second_list:
        second_str = second_list[0].replace('s', '')
        total += int(second_str)

    return total


def get_ccc_start_end_times(twitch_client_id, twitch_client_secret, clip_slug):
    gql_url = "https://gql.twitch.tv/gql"
    gql_payload = [{
        'operationName': 'ClipsChatCard',
        'variables': {
            'slug': clip_slug
        },
        'extensions': {
            'persistedQuery': {
                'version': 1,
                'sha256Hash': '94c1c7d97d860722a5b7ef3c3b3de3783b37fc32d69bcccc8ea0cda372cf1f01'
            }
        }
    }]

    gql_headers = headers = {  # we can probably delete most of this
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
        'X-Device-Id': 'xQR0BchhwJE1VO05SLyC5ygMlNIiKcPC',
        'Accept-Language': 'en-US',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
        'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'Content-Type': 'text/plain;charset=UTF-8',
        'Accept': '*/*',
        'Origin': 'https://clips.twitch.tv',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://clips.twitch.tv/'
    }

    gql_resp = requests.post(gql_url, headers=gql_headers, json=gql_payload)

    gql_data = gql_resp.json()

    start_time = gql_data[0]['data']['clip']['videoOffsetSeconds']

    query = {
        'id': clip_slug
    }

    api_data = get_ccc_info(
        twitch_client_id, twitch_client_secret, query)['data'][0]
    end_time = start_time + twitch_time_to_seconds(api_data.get('duration'))

    return start_time, end_time
