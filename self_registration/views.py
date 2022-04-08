import json
import re
from datetime import datetime, timedelta, timezone
from time import strftime
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.core.mail import send_mail
from django.core.serializers import serialize
from django.template.loader import render_to_string, get_template
from django.db import transaction

from accounts.models import Device, SecurityOption, Tenant
from self_registration.utils import generate_ref_code
from .models import Visitor
from .forms import VisitorCheckInForm, VisitorKioskRegistrationForm, VisitorRegistrationForm, StaffRegistrationForm

from hikvision_api.api import CheckStatusCodeResponse, FaceData, get_text_status_response, initiate, Person

from sorl.thumbnail import get_thumbnail

def visitor_reg(request, *args, **kwargs):
    try:
        context = {}
        security = False
        try:
            security = SecurityOption.objects.first()
            security = security.security
        except:
            security = False
        
        form = VisitorRegistrationForm(request.POST or None)
        code = str(kwargs.get('refs_tenant'))
        tenant = Tenant.objects.get(code=code)

        if request.method == 'POST':
            form = VisitorRegistrationForm(request.POST, request.FILES)
            if form.is_valid():
                form.clean()
                visitor = form.save(commit=False)
                visitor.tenant = tenant

                if security:
                    visitor.is_approved = 1
                else:
                    visitor.is_approved = 2
                visitor.save()

                if visitor.photo:
                    im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                email_template = 'email/visitor_registration.html'

                email_context = { 'visitor': visitor }

                try:
                    html_email = render_to_string(email_template, email_context)
                    email = send_mail(
                        'VMS-Luzern: Visitor Appointment Registration',
                        html_email,
                        'webmaster@localhost',
                        [ tenant.user.email ],
                        fail_silently=False
                    )
                except Exception as e:
                    raise e

                messages.success(request, 'Success')
                return render(request, 'visitors/success.html', { 'code': visitor.code })
            else:
                print('form_invalid')

        context['code'] = code
        context['tenant'] = tenant
        context['form'] = form
        return render(request, 'visitors/visitor_self_register.html', context)
    except:
        context = {}
        context['code'] = None
        security = False
        try:
            security = SecurityOption.objects.first()
            security = security.security
        except:
            pass
        
        form = VisitorKioskRegistrationForm(request.POST or None, request.FILES or None)

        if request.method == 'POST':
            tenant_id = request.POST.get('tenant')
            tenant = Tenant.objects.get(user_id=tenant_id)

            if form.is_valid():
                form.clean()
                visitor = form.save(commit=False)
                visitor.tenant = tenant

                if security:
                    visitor.is_approved = 1
                else:
                    visitor.is_approved = 2
                
                visitor.save()
                
                # Store thumbnail picture version
                if visitor.photo:
                    im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                # Emailing when enable
                email_template = 'email/visitor_registration.html'
                email_context = { 'visitor': visitor }

                try:
                    html_email = render_to_string(email_template, email_context)
                    email = send_mail(
                        'VMS-Luzern: Visitor Appointment Registration',
                        html_email,
                        'webmaster@localhost',
                        [ tenant.user.email ],
                        fail_silently=False
                    )
                except Exception as e:
                    raise e

                messages.success(request, 'Visitor Registration Success. Thank you.')
                return render(request, 'visitors/success.html', { 'code': visitor.code })

        context = { 'segment': 'visitors kiosk', 'form': form }

        return render(request, 'visitors/visitor_self_register.html', context)

def staff_reg(request, *args, **kwargs):

    try:
        form = StaffRegistrationForm(request.POST or None)
        code = str(kwargs.get('refs_tenant'))
        tenant = Tenant.objects.get(code=code)

        if request.method == 'POST':
            form = StaffRegistrationForm(request.POST, request.FILES)
            if form.is_valid():
                staff = form.save(commit=False)
                staff.tenant = tenant
                staff.is_approved = 1
                staff.save()

                email_template = 'email/staff_pending.html'
                email_context = { 'code': staff.code }

                try:
                    html_email = render_to_string(email_template, email_context)
                    email = send_mail(
                        'VMS-Luzern: Staff Registration',
                        html_email,
                        'webmaster@localhost',
                        [ staff.email ],
                        fail_silently=False
                    )
                except Exception as e:
                    raise e

                messages.success(request, 'Staff Registration Success. Thank you.')
                return render(request, 'staffs/success.html', { 'code': staff.code })

        context = { 'segment': 'staffs', 'tenant': tenant, 'form': form, 'code': code }
        return render(request, 'staffs/staff_self_register.html', context)
    except:
        return HttpResponseForbidden('<h1>403 Forbidden</h1>', content_type='text/html')

def check_in(request):
    context = {}

    if request.method == 'POST':

        try:
            visitor = Visitor.objects.get(code=request.POST.get('search'))

            # for v in visitor:

            if visitor.is_approved == 1:
                return JsonResponse({
                    'error': True,
                    'data': 'Your registration is currently pending approval from Host. Kindly call the Host to approve your appointment. Thank you.'
                })
            elif visitor.is_approved == 2 and visitor.is_checkin == True:
                return JsonResponse({
                    'error': True,
                    'data': "You have checked in before. Kindly register for a new appointment to obtain new code for check in.",
                }) 
            else:
                return JsonResponse({
                    'error': False,
                })

        except Visitor.DoesNotExist as e:
            return JsonResponse({
                'error': True,
                'data': "Opps, The code you provided not exist. Try Again.",
            })

    return render(request, 'check_in/check_in.html', context)

def details_checkin(request, *args, **kwargs):

    if request.is_ajax():
        template_name = 'check_in/modal/checkin_detail_inner.html'
    else:
        template_name = 'check_in/modal/checkin_detail.html'

    search = request.GET.get('search')

    if search:
        visitor = get_object_or_404(Visitor, code__exact=search)
    else:
        visitor = Visitor.objects.get(id = request.POST.get('visitor_id'))

    
    form = VisitorCheckInForm(request.POST or None, request.FILES or None, instance=visitor)

    if request.is_ajax() and request.method == 'POST':
        # form_update = VisitorRegistrationForm(data=request.POST, files=request.FILES, instance=visitor)
        
        if visitor.is_approved == 2:
            if form.is_valid():
                form.clean()
                visitor_update = form.save(commit=False)

                # Try Except push to FRA Logic with the updated info
                device = Device.objects.get(pk=visitor_update.tenant.device.pk)
                host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")

                try:
                    initialize = initiate(device.device_username, device.device_password)
                    auth = initialize['auth']

                    if initialize['client'] and auth:
                        if visitor_update.photo:
                            img = get_thumbnail(visitor_update.photo, '200x200', crop='center', quality=99)
                            faceURL = str( str(absolute_uri) + '/static' + str(img.url) )
                            print(faceURL)
                        if visitor_update.code:
                            pass
                        
                        # Try push add person first, if failed reject check-in
                        # Step 1: Add Picture Data First, Check FPID returned
                        try:
                            face_data_instance = FaceData()
                            face_add_response = face_data_instance.face_data_add(1, visitor_update.code, visitor_update.name, faceURL, host, auth)
                            print(face_add_response)

                            status = face_add_response['statusCode']
                            error_msg = face_add_response['subStatusCode']

                            if status != 1:
                                return JsonResponse({
                                    'error': True,
                                    'data': f"Check in failed. Reason: {error_msg}. Please try again. Thank you.",
                                })

                        # Step 2: If exist, Search Person & Update (Overwrite person picture), If not exist, add new person
                            # use code as employee ID / FPID
                            # update include valid start & end time

                        # Step 3: Add card for employee of the building, Tenant & Building owner only (Not applicable to visitor check in)
                        
                            exit()
                            person_instance = Person()
                            user_type = 'visitor'
                            

                            # Step 1: Check date time with datetime now / also done using form.clean()

                            # Step 2: Manipulating date to match --> "endTime":"2023-02-09T17:30:08",
                            valid_begin = visitor_update.start_date.strftime("%Y-%m-%dT%H:%M:00")
                            valid_end = visitor_update.end_date.strftime("%Y-%m-%dT%H:%M:00")

                            add_res = person_instance.add(visitor_update, user_type, valid_begin, valid_end, host, auth)
                            print(add_res)
                            digit = add_res['statusCode'] or None

                            if digit != 1:
                                return JsonResponse({
                                    'error': True,
                                    'data': "Check in failed during adding person into FRA. Please try again. Thank you.",
                                })

                            return JsonResponse({
                                'error': False
                            })

                        except:
                            return JsonResponse({
                                'error': True,
                                'data': "Something went wrong during the check in process. Please try again. Thank you.",
                            })
                except:
                    pass

                exit()

                visitor_update.is_checkin = True
                visitor_update.save()

                return render(request, 'check_in/checkin_success.html', { 'visitor': visitor_update })
            else:
                return JsonResponse({
                    'error': True,
                    'message': form.errors
                })

        elif visitor.is_approved == 1:
            return JsonResponse({
                'error': True,
                'data': "Your registration is currently pending approval from Host. Kindly call the Host to approve your appointment. Thank you.",
            })
        else:
            return JsonResponse({
                'error': True,
                'data': "Check in unsuccessful. You can try to register again if the code is already invalid.",
            })

    return render(request, template_name, {
        'form': form,
        'visitor': visitor,
        # 'message': message
    })

def validate_nric(request):
    
    if request.method == 'POST':

        regval = False

        match = re.match("^\d{3}[A-Z]$", request.POST.get('nric'))

        if match:
            regval = True

        all_visitor = Visitor.objects.all()

        if all_visitor:
            for visitor in all_visitor:

                # if visitor.identification_no == request.POST.get('nric'):
                #     return JsonResponse({'valid': False, 'message': 'Identification No. has already been registered'})
                if regval == False:
                    return JsonResponse({'valid': False, 'message': 'Identification No. must be only 3 digits and an Alphabet [Case Sensitive]'})

                else:
                    return JsonResponse({'valid': True,'message': 'Ok'})

        else:
            if regval == False:
                return JsonResponse({'valid': False, 'message': 'Identification No. must be only 3 digits and an Alphabet [Case Sensitive]'})
            else:
                return JsonResponse({'valid': True,'message': 'Ok'})

    return HttpResponse("nric validation")