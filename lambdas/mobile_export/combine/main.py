import os
import subprocess
import uuid

import s3fs

FINAL_BUCKET = os.getenv('FINAL_BUCKET')

BLUR_STRENGTH = 15

WATERMARK_FILE = 'https://pillaroverlays.s3.amazonaws.com/watermark.png'


def create_facecam_mobile_video(
        background_file,
        content_file,
        facecam_file,
        output_file,
        **options):

    # specifies the x and y coordinates of the content
    content_x = options.get('content_x', 0)
    content_y = options.get('content_y', 420)
    # specifies the x and y coordinates of the facecam
    facecam_x = options.get('facecam_x', 260)
    facecam_y = options.get('facecam_y', 0)
    # how strong the blur should be
    blur_strength = options.get('blur_strength', 15)
    # whether or not to put a watermark on the video
    watermark = options.get('watermark', True)
    # the x and y coordinates of the watermark
    watermark_x = options.get('watermark_x', 10)
    watermark_y = options.get('watermark_y', 1720)
    # the x and y scale of the watermark
    watermark_scale_x = options.get('watermark_scale_x', 350)
    watermark_scale_y = options.get('watermark_scale_y', 100)
    # this can be any public URL or a local file
    watermark_file = options.get('watermark_file', WATERMARK_FILE)

    # if there is a watermark, add it to the video
    if watermark:
        # generates the FFMPEG command sequence to add the watermark
        watermark_command = f"[3:v] scale={watermark_scale_x}:{watermark_scale_y},colorchannelmixer=aa=0.5 [d]; [c][d] overlay={watermark_x}:{watermark_y}"
        # the ffmpeg command to create the video
        cmd = f"ffmpeg -i {background_file} -i {content_file} -i {facecam_file} -i {watermark_file} -filter_complex '[0:v] boxblur={blur_strength}:1 [a]; [a][1:v] overlay={content_x}:{content_y} [b]; [b][2:v] overlay={facecam_x}:{facecam_y} [c];{watermark_command}' -r 60 -c:v libx264 -pix_fmt yuv420p {output_file}"
    else:
        # if there is no watermark, omit the watermark file and command
        cmd = f"ffmpeg -i {background_file} -i {content_file} -i {facecam_file} -filter_complex '[0:v] boxblur={blur_strength}:1 [a]; [a][1:v] overlay={content_x}:{content_y} [b]; [b][2:v] overlay={facecam_x}:{facecam_y}' -r 60 -c:v libx264 -pix_fmt yuv420p {output_file}"

    subprocess.run(cmd, shell=True)


def create_blurred_mobile_video(
        background_file,
        content_file,
        output_file,
        **options):

    # specifies the x and y coordinates of the content
    content_x = options.get('content_x', 0)
    content_y = options.get('content_y', 420)
    # how strong the blur should be
    blur_strength = options.get('blur_strength', 15)
    # whether or not to put a watermark on the video
    watermark = options.get('watermark', True)
    # the x and y coordinates of the watermark
    watermark_x = options.get('watermark_x', 10)
    watermark_y = options.get('watermark_y', 1720)
    # the x and y scale of the watermark
    watermark_scale_x = options.get('watermark_scale_x', 350)
    watermark_scale_y = options.get('watermark_scale_y', 100)
    # this can be any public URL or a local file
    watermark_file = options.get('watermark_file', WATERMARK_FILE)

    # if there is a watermark, add it to the video
    if watermark:
        # generates the FFMPEG command sequence to add the watermark
        watermark_command = f"[2:v] scale={watermark_scale_x}:{watermark_scale_y},colorchannelmixer=aa=0.5 [c]; [b][c] overlay={watermark_x}:{watermark_y}"
        # the ffmpeg command to create the video
        cmd = f"ffmpeg -i {background_file} -i {content_file} -i {watermark_file} -filter_complex '[0:v] boxblur={blur_strength}:1 [a]; [a][1:v] overlay={content_x}:{content_y} [b];{watermark_command}' -r 60 -c:v libx264 -pix_fmt yuv420p {output_file}"
    else:
        # if there is no watermark, omit the watermark file and command
        cmd = f"ffmpeg -i {background_file} -i {content_file} -filter_complex '[0:v] boxblur={blur_strength}:1 [a]; [a][1:v] overlay={content_x}:{content_y}' -r 60 -c:v libx264 -pix_fmt yuv420p {output_file}"

    subprocess.run(cmd, shell=True)


def handler(event, context):

    os.chdir('/tmp')

    print(f"Event: {event}")

    background_file = event.get('background_file')
    content_file = event.get('content_file')
    facecam_file = event.get('facecam_file')

    if not background_file:
        raise Exception('Missing background file')

    background_file_name = background_file.split('/')[-1]
    content_file_name = ''
    facecam_file_name = ''
    if content_file:
        content_file_name = content_file.split('/')[-1]
    if facecam_file:
        facecam_file_name = facecam_file.split('/')[-1]

    s3 = s3fs.S3FileSystem(anon=False)

    s3.get(background_file, f'/tmp/{background_file_name}')
    if content_file:
        s3.get(content_file, f'/tmp/{content_file_name}')
    if facecam_file:
        s3.get(facecam_file, f'/tmp/{facecam_file_name}')

    # create a random name
    output_file = f'{uuid.uuid4()}.mp4'

    if not facecam_file and not content_file:
        background_local_file = f'/tmp/{background_file_name}'
        upload_file_name = f's3://{FINAL_BUCKET}/{output_file}'
        print(background_local_file)
        print(upload_file_name)
        s3.put(background_local_file,
               upload_file_name)
        subprocess.run("rm -r /tmp/*", shell=True)
        return {'output_file': upload_file_name}

    if facecam_file:
        create_facecam_mobile_video(
            f'/tmp/{background_file_name}',
            f'/tmp/{content_file_name}',
            f'/tmp/{facecam_file_name}',
            'output.mp4',
            blur_strength=BLUR_STRENGTH)
    else:
        create_blurred_mobile_video(
            f'/tmp/{background_file_name}',
            f'/tmp/{content_file_name}',
            '/tmp/output.mp4',
            blur_strength=BLUR_STRENGTH)

    s3.put('/tmp/output.mp4', f's3://{FINAL_BUCKET}/{output_file}')
    subprocess.run("rm -r /tmp/*", shell=True)
    return {
        'output_file': f's3://{FINAL_BUCKET}/{output_file}'
    }
