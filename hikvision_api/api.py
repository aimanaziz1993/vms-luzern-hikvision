# -*- coding: utf-8 -*-
# -------------------------------------------------------
# __author__ = 'Aiman Aziz'
# date: 07/Apr/2022
# -------------------------------------------------------
from django.http import HttpResponseBadRequest

import requests
import json
import os

from requests.auth import HTTPDigestAuth
from requests import Session
from types import SimpleNamespace

from accounts.models import Device

# Default
HIKVISION_ACT_LOGIN='login'
HIKVISION_ACT_PASSWORD='password'
HIKVISION_ACT_HOST='host'

class LoginPasswordMissingError(Exception):
    pass

class CheckStatusCodeResponse(Exception):
    pass

def get_text_status_response(digits, body):

    obj = {}

    if digits == 1:
        obj = {
            'status': 'ok',
            'msg': ''
        }
    elif digits == 2:
        pass
    elif digits == 3:
        pass
    elif digits == 4:
        pass
    elif digits == 5:
        obj = {
            'status': 'invalid message format',
            'msg': ''
        }
    elif digits == 6:
        obj = {
            'status': 'invalid content',
            'msg': body['subStatusCode']
        }
    elif digits == 7:
        pass
    else:
        obj = None

    return obj


def initiate(id=None, pwd=None):
    client = False

    if id is None or pwd is None:
        raise LoginPasswordMissingError(
            "Hikvision Access Control Terminals API methods require login and password"
        )

    auth = HTTPDigestAuth(id, pwd)
    
    if auth:
        session = Session()
        session.auth = auth
        client = True
        return { 'client': client, 'auth': auth, 'session': session }
    else:
        print("Session undefined. Device not successfully verified")
        client = False

class Person(object):
    def __init__(self):
        pass

    def search(self, id, host, auth):
        try:
            
            path = host+'/ISAPI/AccessControl/UserInfo/Search?format=json'
            body = {
                        "UserInfoSearchCond": {
                            "searchID": "4",
                            "searchResultPosition": 0,
                            "maxResults": 32,
                            "EmployeeNoList":[
                                {
                                    "employeeNo": str(id)
                                }
                            ]
                        }
                    }
            response = requests.post(path, data=json.dumps(body), auth=auth, timeout=5)

            # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
            result = json.loads( json.dumps( response.json() ) )
            return result
        except:
            return HttpResponseBadRequest()

    def add_for_validation_purpose(self, data, user_type, valid_begin, valid_end, host, auth):
        
        path = host+'/ISAPI/AccessControl/UserInfo/Record?format=json'
        body =  {
            "UserInfo": {
                "employeeNo": str(data.code),
                "name": data.code,
                "userType": user_type,
                "Valid":{
                    "enable": True,
                    "beginTime": str(valid_begin),
                    "endTime": str(valid_end),
                    "timeType":"local"
                },
                "userVerifyMode": "cardOrFace",
                "floorNumber": 1,
                "password": "",
                "doorRight": "1",
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ],
                "checkUser": True
            }
        }
        response = requests.post(path, data=json.dumps(body), auth=auth)
        
        # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        result = json.loads( json.dumps( response.json() ) )
        return result

    def add(self, data, user_type, valid_begin, valid_end, host, auth):
        
        path = host+'/ISAPI/AccessControl/UserInfo/Record?format=json'
        body =  {
            "UserInfo": {
                "employeeNo": str(data.code),
                "name": data.name,
                "userType": user_type,
                "Valid":{
                    "enable": True,
                    "beginTime": str(valid_begin),
                    "endTime": str(valid_end),
                    "timeType":"local"
                },
                "userVerifyMode": "cardOrFace",
                "floorNumber": int(data.tenant.device.floor.id),
                "password": "",
                "doorRight": "1",
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ],
                "checkUser": True
            }
        }
        response = requests.post(path, data=json.dumps(body), auth=auth)
        
        # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        result = json.loads( json.dumps( response.json() ) )
        return result
    
    def delete(self, id, host, auth):
        
        path = host+'/ISAPI/AccessControl/UserInfo/Delete?format=json'
        body = {
                    "UserInfoDelCond": {                        
                        "EmployeeNoList":[
                            {
                                "employeeNo": str(id)
                            }
                        ]
                    }
                }
        response = requests.put(path, data=json.dumps(body), auth=auth)
        # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        result = json.loads( json.dumps( response.json() ) )
        return result

    def update(self, data, user_type, valid_begin, valid_end, host, auth):
        
        path = host+'/ISAPI/AccessControl/UserInfo/Modify?format=json'
        body =  {
            "UserInfo": {
                "employeeNo": str(data.code),
                "name": data.name,
                "userType": user_type,
                "Valid":{
                    "enable": True,
                    "beginTime": str(valid_begin),
                    "endTime": str(valid_end),
                    "timeType":"local"
                },
                "userVerifyMode": "cardOrFace",
                "floorNumber": int(data.tenant.device.floor.id),
                "password": "",
                "doorRight": "1",
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ],
                "checkUser": True
            }
        }
        response = requests.put(path, data=json.dumps(body), auth=auth)
        
        # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        result = json.loads( json.dumps( response.json() ) )
        return result

    def get_count(self, host, auth):
        
        path = host+'/ISAPI/AccessControl/UserInfo/Count?format=json'
        
        response = requests.get(path, auth=auth)
        result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        return result.UserInfoCount.userNumber

class FaceDataLib(object):

    def fp_library_add(self, faceLibType, name, customInfo, host, auth):
        
        path = host+'/ISAPI/Intelligent/FDLib?format=json'
        body = {
            'faceLibType': faceLibType,
            'name': name,
            'customInfo': customInfo
        }
        response = requests.post(path, data=json.dumps(body), auth=auth)
        

        result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        return result

    def fp_library_update(self, fdid, faceLibType, name, customInfo, host, auth):
        
        path = f'{host}/ISAPI/Intelligent/FDLib?format=json&FDID={fdid}&faceLibType={faceLibType}'
        body = {
            "name": "CustomTestLibraryBlackFD",
            "customInfo": "test libraryBlackFD"
            }
        response = requests.put(path, data=json.dumps(body), auth=auth)
        
        result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        return result

    def fp_library_delete(self, fdid, faceLibType, host, auth):
        
        path = f'{host}/ISAPI/Intelligent/FDLib?format=json&FDID={fdid}&faceLibType={faceLibType}'
        
        response = requests.delete(path, auth=auth)
        
        result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        return result

    def fp_library_list(self, host, auth):
        
        path = '{host}/ISAPI/Intelligent/FDLib?format=json'
        response = requests.get(path, auth=auth)
        result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        return result


class FaceData(object):
    
    def face_data_add(self, FDID, FPID, name, faceURL, host, auth):
        
        path = host+'/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json'
        # body = {
        #     "faceLibType": faceLibType,
        #     "FDID": str(FDID),
        #     "FPID": str(FPID),
        #     "name": name,
        #     "gender": gender,
        #     "bornTime": bornTime, #"19940226T000000+0500"
        #     "city": city,
        #     "faceURL": faceURL
        # }
        body = {
            "faceLibType": "blackFD",
            "FDID": str(FDID), # always 1 or get info from face picture library
            "FPID": str(FPID),
            "name": name,
            "bornTime": "", # ISO8601 time format
            "faceURL": faceURL
        }
        response = requests.post(path, data=json.dumps(body), auth=auth)
        
        
        # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        result = json.loads(json.dumps(response.json()))
        return result

    def face_data_update(self, FDID, FPID, name, faceURL, host, auth):
        
        path = f'{host}/ISAPI/Intelligent/FDLib/FDSearch?format=json&FDID={FDID}&FPID={FPID}&faceLibType=blackFD'
        # body = {
        #     "name": name,
        #     "gender": gender,
        #     "bornTime": bornTime, #"19940226T000000+0500"
        #     "city": city,
        #     "faceURL": faceURL
        # }
        body = {
            "faceLibType": "blackFD",
            "FDID": str(FDID), # always 1 or get info from face picture library
            "FPID": str(FPID),
            "name": name,
            "bornTime": "", # ISO8601 time format
            "faceURL": faceURL
        }
        response = requests.put(path, data=json.dumps(body), auth=auth)
        
        # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        result = json.loads(json.dumps(response.json()))
        return result

    def face_data_delete(self, faceLibType, FDID, FPIDList, host, auth):
        
        path = f'{host}/ISAPI/Intelligent/FDLib/FDSearch/Delete?format=json&FDID={FDID}&faceLibType={faceLibType}'
        fpidlist = []
        for fpid in FPIDList:
            fpidlist.append({
                'value': fpid
            })
        body = {
            'FPID': fpidlist
            }
             
        response = requests.put(path, data=json.dumps(body), auth=auth)
        
        result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        return result

    def face_data_search(self, faceLibType, FDID, FPID, host, auth):
        
        path = f'{host}/ISAPI/Intelligent/FDLib/FDSearch?format=json'
        body = {
            "searchResultPosition": 0,
            "maxResults": 32,
            "faceLibType": f'{faceLibType}',
            "FDID": f'{FDID}',
            # "FPID": f'{FPID}'
        }
        response = requests.post(path, data=json.dumps(body), auth=auth)
        # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
        result = json.loads(json.dumps(response.json()))
        return result


class Card(object):
    def __init__(self):
        pass

    def search(self, id, host, auth):
        try:
            
            path = host+'/ISAPI/AccessControl/CardInfo/Search?format=json'
            body =  {
                        "CardInfoSearchCond": {
                            "searchID": "4",
                            "searchResultPosition": 0,
                            "maxResults": 32,
                            "EmployeeNoList":[
                                {
                                    "employeeNo": str(id)
                                }
                            ]
                        }
                    }
            response = requests.post(path, data=json.dumps(body), auth=auth)
            # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
            result = json.loads( json.dumps( response.json() ) )
            return result
        except:
            return HttpResponseBadRequest()

    def add(self, employeeNo, host, auth):
        try:
            path = host+'/ISAPI/AccessControl/CardInfo/Record?format=json'
            body = {
                "CardInfo": {
                    "employeeNo": str(employeeNo),
                    "cardNo": str(employeeNo),
                    "deleteCard": "false",
                    "cardType": "normalCard",
                    # "leaderCard": ,
                    "checkCardNo": True,
                    "addCard": True,
                }
            }
            response = requests.post(path, data=json.dumps(body), auth=auth)
            # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
            result = json.loads( json.dumps( response.json() ) )
            return result
        except:
            return HttpResponseBadRequest()

class Event(object):
    def __init__(self):
        pass

    def search(self, host, auth):
        try:
            
            path = host+'/ISAPI/AccessControl/AcsEvent?format=json'
            body =  {
                        "AcsEventCond": {
                            "searchID": "4",
                            "searchResultPosition": 0,
                            "maxResults": 32,
                            "major": 0,
                            "minor": 0,
                            "startTime": "2022-04-19T00:00:00+08:00",
                            "endTime": "2022-04-19T23:59:59+08:00"
                        }
                    }
            response = requests.post(path, data=json.dumps(body), auth=auth)
            # result = json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d))
            result = json.loads( json.dumps( response.json() ) )
            return result
        except:
            return HttpResponseBadRequest()