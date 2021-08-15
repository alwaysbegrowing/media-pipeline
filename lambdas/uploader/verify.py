
def verify_request_body(body: dict) -> str:
    try:
        clips = body['clips']

        for clip in clips:
            start_time = clip.get('start_time') or clip.get('startTime')
            end_time = clip.get('end_time') or clip.get('endTime')
            duration = end_time - start_time
            if duration <= 0:
                raise AssertionError(f'Body Malformed: "clips" contains clip with negative duration. duration: {duration}; clip: {clip}')
    
    except Exception as e:
        print(e)
        return str(e)

    video_id = body.get('videoId')

    if video_id is None:
        return 'Body Malformed: Missing "videoId".'

    return ''