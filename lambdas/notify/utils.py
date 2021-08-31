

def replace_nth_occurance(s, sub, repl, n):
    '''
    # https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string
    # In [14]: s = "foobarfoofoobarbar"

    # In [15]: replace_nth_occurance(s, "bar","replaced",3)
    # Out[15]: 'foobarfoofoobarreplaced'

    # In [16]: replace_nth_occurance(s, "foo","replaced",3)
    # Out[16]: 'foobarfooreplacedbarbar'

    # In [17]: replace_nth_occurance(s, "foo","replaced",5)
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
    return replace_nth_occurance(
        s3_url,
        '/',
        '.s3.amazonaws.com/',
        3).replace(
        's3://',
        'https://')
