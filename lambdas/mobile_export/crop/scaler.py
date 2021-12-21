import youtube_dl
import math

def get_twitch_vod_width_height(video_id):
    url = f'https://www.twitch.tv/videos/{video_id}'

    width = 0
    height = 0

    with youtube_dl.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        if 'width' in info:
            width = info['width']
        if 'height' in info:
            height = info['height']

    return width, height

def scale_coordinates(video_id, x, y, width, height):
    video_width, video_height = get_twitch_vod_width_height(video_id)

    if video_width == 0 or video_height == 0:
        return x, y, width, height

    x_scale = width / video_width
    y_scale = height / video_height

    x = int(x * x_scale)
    y = int(y * y_scale)
    width = int(width * x_scale)
    height = int(height * y_scale)

    return x, y, width, height
