from hikvision_api.api import initiate, Card, FaceData, Person
from accounts.models import Device

from datetime import datetime


def clear_redundant_visitor(visitors, request):

    for visitor in visitors:

        device = Device.objects.get(pk=visitor.tenant.device.pk)
        host = str( str(request) + '://' + str(device.ip_addr) )

        initialize = initiate(device.device_username, device.device_password)
        auth = initialize['auth']

        if initialize['client'] and auth:
            try:
                # Person Add - Step 1: Initiate instance,
                person_instance = Person()

                if visitor.end_date <= datetime.now():
                    print("deleting all end date visitor")
                    del_res = person_instance.delete(visitor.code, host, auth)
                    print(del_res)
            except:
                pass
