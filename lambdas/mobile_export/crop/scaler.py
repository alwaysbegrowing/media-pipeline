import youtube_dl


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


class ClipScaler:
    def __init__(self, video_id):
        self.video_id = video_id
        self.video_width, self.video_height = get_twitch_vod_width_height(
            video_id)
        self.x_scale = self.video_width / 1920
        self.y_scale = self.video_height / 1080

    def scale_coordinates(self, x, y, width, height):

        x = int(x * self.x_scale)
        y = int(y * self.y_scale)
        width = int(width * self.x_scale)
        height = int(height * self.y_scale)

        if x % 2 != 0:
            x += 1
        if y % 2 != 0:
            y += 1
        if width % 2 != 0:
            width += 1
        if height % 2 != 0:
            height += 1

        return x, y, width, height


if __name__ == "__main__":
    video_id = '1227210464'
    x = 656
    y = 0
    width = 606
    height = 1080
    clip_scaler = ClipScaler(video_id)
    print(clip_scaler.scale_coordinates(x, y, width, height))
