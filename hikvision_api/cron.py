from hikvision_api.api import initiate, Card, FaceData, Person
from accounts.models import Device
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from datetime import datetime
from sorl.thumbnail import get_thumbnail
# from .models import Visitor

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

def push_to_fra(device, host, absolute_uri, visitor):
    try:
        initialize = initiate(device.device_username, device.device_password)
        auth = initialize['auth']

        if initialize['client'] and auth:
            if visitor.photo:
                print('here')
                img = get_thumbnail(visitor.photo, '200x200', crop='center', quality=99)
                faceURL = str( str(absolute_uri) + '/static' + str(img.url) )
                print('push face url', faceURL)
            if visitor.code:
                pass
            
            # Try push Step 1 add person first, if failed reject check-in
            try:
                # Person Add - Step 1: Initiate instance,
                person_instance = Person()
                user_type = 'visitor'

                # Person Add - Step 2: Manipulating date to match time local format --> "endTime":"2023-02-09T17:30:08",
                # valid_begin = visitor_update.start_date.strftime("%Y-%m-%dT%H:%M:00")

                df = datetime.now()
                valid_begin = df.strftime("%Y-%m-%dT%H:%M:00")
                valid_end = visitor.end_date.strftime("%Y-%m-%dT%H:%M:00")
                
                add_res = person_instance.add(visitor, user_type, valid_begin, valid_end, host, auth)
                print(add_res)
                a_status = add_res['statusCode'] or None

                if a_status != 1:
                    if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
                        edit_res = person_instance.update(visitor, user_type, valid_begin, valid_end, host, auth)
                        print(edit_res)
                        e_status = edit_res['statusCode'] or None

                        if e_status != 1:
                            return JsonResponse({
                                'error': True,
                                'data': "Check in failed during editing person into FRA. Please try again. Thank you.",
                            })
                    else:
                        return JsonResponse({
                            'error': True,
                            'data': "Check in failed during adding person into FRA. Please try again. Thank you.",
                        })

                # Step 2: Add card for employee,visitor of the building, Tenant & Building owner only (Not applicable to visitor check in)
                # test card
                card_instance = Card()
                search_card_res = card_instance.search(visitor.code, host, auth)
                print(search_card_res)
                c_status = search_card_res['CardInfoSearch']['totalMatches']
                print( search_card_res['CardInfoSearch']['totalMatches'] )

                if c_status == 0:
                    print("Card not found")
                    add_card = card_instance.add(visitor.code, host, auth)
                    print(add_card)
                    ac_status = add_card['statusCode']

                    if ac_status != 1:
                        return JsonResponse({
                            'error': True,
                            'data': "Check in failed during adding person Card information. Please try again. Thank you.",
                        })

                print("Card information added")

                # Push Step 3: Add Picture Data, Check FPID returned - ONLY RUN THIS WHEN PHOTO IS NOT NONE
                if visitor.photo:
                    face_data_instance = FaceData()
                    face_add_response = face_data_instance.face_data_add(1, visitor.code, visitor.name, faceURL, host, auth)
                    print(face_add_response)

                    f_status = face_add_response['statusCode']
                    error_msg = face_add_response['subStatusCode']
                    
                    if f_status != 1:
                        # if add face failed, edit person face from FRA using FPID
                        if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
                            # if face_add_response['subStatusCode'] == 'deviceUserAlreadyExistFace':
                            edit_face = face_data_instance.face_data_update(1, visitor.code, visitor.name, faceURL, host, auth)
                            print(edit_face)
                            fe_status = edit_face['statusCode'] or None

                            if fe_status != 1:
                                return JsonResponse({
                                    'error': True,
                                    'data': "Check in failed during editing person face into FRA. Please try again. Thank you.",
                                })
                        else:
                            print('face failed to be upload')
                            # search & delete user instance in FRA
                            search_res = person_instance.search(visitor.code, host, auth)
                            print(search_res)

                            # delete_res = person_instance.delete(visitor_update.code, host, auth)
                            # print(delete_res)

                            # return JsonResponse({
                            #     'error': True,
                            #     'data': f"Check in failed during face validation. Please try again by updating your face photo here. Thank you.",
                            # })

                # Step 4: Get All past checked in visitor with status True 
                # get_checked_in_visitor = modalvisitor
                # # Get & loop all past visitor code - compare code to FRA & delete all visitor from FRA
                # for visitor in get_checked_in_visitor:
                #     # delete every code if exist in FRA
                #     if visitor.end_date <= datetime.now() or visitor.contact_no == visitor.contact_no:
                #         print("deleting all end date visitor")
                #         del_res = person_instance.delete(visitor.code, host, auth)
                #         print(del_res)

                # visitor.is_checkin = True
                # visitor.save()

                # return JsonResponse({
                #     'error': False
                # })

            except:
                # t = loader.get_template('templates/500.html')
                # template = loader.get_template('templates/500.html')
                # return HttpResponse(template)
                return JsonResponse({
                    'error': True,
                    'data': "Something went wrong during the check in process. Please try again. Thank you.",
                })
    except:
        pass
