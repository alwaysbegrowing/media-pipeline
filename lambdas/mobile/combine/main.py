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
    content_x = 0
    content_y = 420
    facecam_x = 260
    facecam_y = 0

    cmd = f"ffmpeg -i {background_file} -i {content_file} -i {facecam_file} -filter_complex '[0:v] boxblur={blur_strength}:1 [a]; [a][1:v] overlay={content_x}:{content_y} [b]; [b][2:v] overlay={facecam_x}:{facecam_y}' -r 60 -c:v libx264 -pix_fmt yuv420p {output_file}"

    subprocess.run(cmd, shell=True)


def create_blurred_mobile_video(background_file, content_file, output_file, blur_strength=15):

    # the x and y coordinates will change when we
    # start working with different aspect ratios
    content_x = 0
    content_y = 420

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
        upload_file_name = f's3://{OUT_BUCKET}/{output_file}'
        print(background_local_file)
        print(upload_file_name)
        s3.put(background_local_file,
               upload_file_name)
        s3.close()
        subprocess.run("rm -r /tmp/*", shell=True)
        return {'output_file': output_file}

    if facecam_file:
        create_fc_mobile_video(f'/tmp/{background_file_name}', f'/tmp/{content_file_name}',
                               f'/tmp/{facecam_file_name}', 'output.mp4', blur_strength=BLUR_STRENGTH)
    else:
        create_blurred_mobile_video(
            f'/tmp/{background_file_name}', f'/tmp/{content_file_name}', '/tmp/output.mp4', blur_strength=BLUR_STRENGTH)

    s3.put('/tmp/output.mp4', f's3://{OUT_BUCKET}/{output_file}')
    s3.close()
    subprocess.run("rm -r /tmp/*", shell=True)
    return {
        'output_file': f's3://{OUT_BUCKET}/{output_file}'
    }
