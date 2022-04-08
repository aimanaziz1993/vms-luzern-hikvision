"""
# print('http scheme', request.scheme)
# print('http url 2', request.build_absolute_uri('?'))
# print('absolute root url 2', request.build_absolute_uri('/')[:-1].strip("/"))
"""

import uuid
import string
import random
from datetime import timedelta

def generate_ref_code():
    code = str( uuid.uuid4() ).replace("-", "")[:12]
    return code

def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def timedeltaObj(timedelta_obj):
    
    timetot = ""

    secs = timedelta.total_seconds(timedelta_obj)

    if secs > 0 and secs <=60:
        timetot += "{} s".format(int(secs))
        # timetotal = int(secs)

    elif secs > 60 and secs <=3600:
        mins = secs // 60
        timetot += "{} mins".format(int(mins))
        secs = secs - mins*60
        # timetotal = int(mins)

    elif secs > 3600:
        hrs = secs // 3600
        timetot += " {} hours".format(int(hrs))
        secs = secs - hrs*3600
        # timetotal = int(hrs)

    return timetot