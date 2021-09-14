import os
import subprocess
import uuid

import s3fs

IN_BUCKET = os.getenv('IN_BUCKET')
OUT_BUCKET = os.getenv('OUT_BUCKET')

BLUR_STRENGTH = 15


def create_fc_mobile_video(background_file, content_file, facecam_file, output_file, blur_strength=15):

    # the x and y coordinates will change when we
    # start working with different aspect ratios

    cmd = f"ffmpeg -i {background_file} -i {content_file} -i {facecam_file} -filter_complex '[0:v] boxblur={blur_strength}:1 [a]; [a][1:v] overlay=0:420 [b]; [b][2:v] overlay=260:0' -r 60 -c:v libx264 -pix_fmt yuv420p {output_file}"

    subprocess.run(cmd, shell=True)


def create_blurred_mobile_video(background_file, content_file, output_file, blur_strength=15):

    # the x and y coordinates will change when we
    # start working with different aspect ratios

    cmd = f"ffmpeg -i {background_file} -i {content_file} -filter_complex '[0:v] boxblur={blur_strength}:1 [a]; [a][1:v] overlay=0:420' -r 60 -c:v libx264 -pix_fmt yuv420p {output_file}"

    subprocess.run(cmd, shell=True)


def handler(event, context):

    os.chdir('/tmp')

    background_file = event.get('background')
    content_file = event.get('content')
    facecam_file = event.get('facecam')

    if not background_file:
        raise Exception('Missing background file')

    # get the video files from s3
    with s3fs.S3FileSystem(anon=False) as s3:
        s3.get(f's3://{IN_BUCKET}/{background_file}')
        if content_file:
            s3.get(f's3://{IN_BUCKET}/{content_file}')
        if facecam_file:
            s3.get(f's3://{IN_BUCKET}/{facecam_file}')

    # create a random name
    output_file = f'{uuid.uuid4()}.mp4'

    if not facecam_file and not content_file:
        with s3fs.S3FileSystem(anon=False) as s3:
            s3.put(f'/tmp/{background_file}',
                   f's3://{OUT_BUCKET}/{output_file}')
        return {'output_file': output_file}

    if facecam_file:
        create_fc_mobile_video(background_file, content_file,
                               facecam_file, 'output.mp4', blur_strength=BLUR_STRENGTH)
    else:
        create_blurred_mobile_video(
            background_file, content_file, 'output.mp4', blur_strength=BLUR_STRENGTH)

    # upload the video to s3
    with s3fs.S3FileSystem(anon=False) as s3:
        s3.put('output.mp4', f's3://{OUT_BUCKET}/{output_file}')

    return {
        'output_file': output_file
    }
