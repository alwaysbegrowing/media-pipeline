import os

import s3fs
from ffmpy import FFmpeg

IN_BUCKET = os.getenv('IN_BUCKET')
OUT_BUCKET = os.getenv('OUT_BUCKET')

BLUR_STRENGTH = 15


def handler(event, context):

    # get clip name from event
    clip_name = event['clip_name']
    print(clip_name)

    # get s3 filesystem
    s3 = s3fs.S3FileSystem(anon=False)

    s3_file = s3.open(f'{IN_BUCKET}/{clip_name}', 'rb')

    print('Downloading file.')
    # save s3 file to local file
    local_file = open(f'/tmp/{clip_name}', 'wb')
    local_file.write(s3_file.read())
    local_file.close()
    s3_file.close()

    print('Blurring file.')

    # generate ffmpeg command
    ffmpeg_inputs = {
        f'/tmp/{clip_name}': None
    }

    ffmpeg_outputs = {
        f'/tmp/blur-{clip_name}': ['-vf', f'"boxblur={BLUR_STRENGTH}:1"']
    }

    ffmpeg = FFmpeg(
        inputs=ffmpeg_inputs,
        outputs=ffmpeg_outputs,
        global_options=[]
    )

    print('Running ffmpeg.')

    # run ffmpeg
    ffmpeg.run()

    print('Uploading file.')

    # upload file to s3

    s3_file = s3.open(f'{OUT_BUCKET}/{clip_name}', 'wb')
    s3_file.write(open(f'/tmp/blur-{clip_name}', 'rb').read())
    s3_file.close()

    print('Removing local files.')

    # remove local files
    os.remove(f'/tmp/{clip_name}')
    os.remove(f'/tmp/blur-{clip_name}')

    return {
        'blurredName': f'blur-{clip_name}'
    }
