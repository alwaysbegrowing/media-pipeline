import math


def seconds_to_ffmpeg_time(input_seconds):
    '''
    Converts the start_time and end_time in seconds to a time that FFMPEG can understand
    '''
    hours_float = input_seconds / 3600
    hours = math.floor(hours_float)
    minutes_float = (hours_float - hours) * 60
    minutes = math.floor(minutes_float)
    seconds_float = (minutes_float - minutes) * 60
    # this will need to be improved at some point
    seconds = math.ceil(seconds_float) - 1

    if seconds >= 60:
        minutes += math.floor(seconds / 60)
        seconds -= 60

    return f'{hours:02}:{minutes:02}:{seconds:02}'
