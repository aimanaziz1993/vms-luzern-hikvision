import json
import re
import os
import base64
import cv2
import numpy as np
from datetime import date, datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from time import strftime
from django import template
from django.template import loader
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.serializers import serialize
from django.template.loader import render_to_string, get_template
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files import File
from django.db.models import Q
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder

import sys
import qrcode
import qrcode.image.svg
from io import BytesIO
from PIL import Image, ImageDraw

from luzern_vms.settings import BASE_DIR
from accounts.models import Device, SecurityOption, Tenant
from self_registration.utils import generate_ref_code
from .models import Visitor, PhotoValidation
from .forms import VisitorCheckInForm, VisitorMobileRegistrationForm, VisitorKioskRegistrationForm, VisitorRegistrationForm, StaffRegistrationForm, VisitorUpdateRegistrationForm, HostForm

from hikvision_api.api import initiate, Card, FaceData, Person
from hikvision_api.cron import clear_redundant_visitor
from hikvision_api.cron import push_to_fra
from sorl.thumbnail import get_thumbnail
from hashlib import md5
from time import localtime

def option_page(request):
    import sys
    base_url = str( str(request.scheme) + '://' + sys.argv[-1] )
    return render (request, 'options.html', {'base_url': base_url})


def visitor_reg_mobile(request, *args, **kwargs):
    context = {}
    context['code'] = None
    context['isMobile'] = True
    security = False
    try:
        security = SecurityOption.objects.first()
        security = security.security
    except:
        pass
    
    form = VisitorMobileRegistrationForm(request.POST or None)
    hosts = HostForm(request.POST or None)

    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        tenant = Tenant.objects.get(user_id=tenant_id)
        if form.is_valid():
            form.clean()
            visitor = form.save(commit=True)
            qr_image = qrcode.make(visitor.code)
            qr_offset = Image.new('RGB', (280,280), 'white')
            draw_img = ImageDraw.Draw(qr_offset)
            qr_offset.paste(qr_image)
            filename = f'{visitor.code}_{visitor.identification_no}'
            print('filename qr', filename)
            thumb_io  = BytesIO()
            qr_offset.save(thumb_io , 'PNG')
            visitor.qr_image.save(filename+'.png', ContentFile(thumb_io.getvalue()), save=False)
            qr_offset.close()
            visitor.tenant = tenant

            try:
                if request.POST['photo2'] != '':
                    photoTemp = request.POST['photo2']
                    trimmed_base64_string = photoTemp.replace('data:image/jpeg;base64,', '')
                    imgdata = base64.b64decode(trimmed_base64_string)
                    filePrefix = md5(str(localtime()).encode('utf-8')).hexdigest()
                    filename = filePrefix+'_visitors.jpg'
                    visitor.photo = ContentFile(imgdata, filename)

                if security:
                    visitor.is_approved = 1
                else:
                    visitor.is_approved = 2
                visitor.save()

                # pass visitor to check their past data from FRA
                try:
                    get_all_possible_same_visitor_by_phone_no = Visitor.objects.filter(contact_no__icontains = visitor.contact_no)
                    clear_redundant_visitor(get_all_possible_same_visitor_by_phone_no, request.scheme)
                except:
                    print('deleting past data not available at the moment')

                if visitor.photo:
                    im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                email_template = 'emailnew/visitor_registration.html'
                email_context = { 'visitor': visitor }

                try:
                    if visitor.email:
                        to = [ visitor.email, tenant.user.email ]
                    else:
                        to = [ tenant.user.email ]
                    html_email = render_to_string(email_template, email_context)
                    email = EmailMultiAlternatives(
                        subject='VMS-Luzerne: Visitor Appointment Registration',
                        body='mail testing',
                        from_email='ifa@concorde.com.sg',
                        to = to
                    )
                    from email.mime.image import MIMEImage
                    if visitor.qr_image:
                        mime_img = MIMEImage(visitor.qr_image.read())
                        mime_img.add_header('Content-ID', '<image>')
                    email.attach(mime_img)
                    email.attach_alternative(html_email, "text/html")
                    email.send(fail_silently=False)

                except Exception as e:
                    raise e

                if not security:
                    device = Device.objects.get(pk=visitor.tenant.device.pk)
                    host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                    absolute_uri = sys.argv[-1]
                    push_to_fra(device, host, absolute_uri, visitor)

                messages.success(request, 'Success')
                return render(request, 'visitors/success.html', { 'code': visitor.code, 'visitor': visitor })

            # CASE when visitor not include face photo
            except:
                if security:
                    visitor.is_approved = 1
                else:
                    visitor.is_approved = 2
                visitor.save()

                # pass visitor to check their past data from FRA
                try:
                    get_all_possible_same_visitor_by_phone_no = Visitor.objects.filter(contact_no__icontains = visitor.contact_no)
                    clear_redundant_visitor(get_all_possible_same_visitor_by_phone_no, request.scheme)
                except:
                    print('deleting past data not available at the moment')

                if visitor.photo:
                    im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                email_template = 'emailnew/visitor_registration.html'
                email_context = { 'visitor': visitor }

                try:
                    if visitor.email:
                        to = [ visitor.email, tenant.user.email ]
                    else:
                        to = [ tenant.user.email ]
                    html_email = render_to_string(email_template, email_context)
                    email = EmailMultiAlternatives(
                        subject='VMS-Luzerne: Visitor Appointment Registration',
                        body='mail testing',
                        from_email='ifa@concorde.com.sg',
                        to = to
                    )
                    from email.mime.image import MIMEImage
                    if visitor.qr_image:
                        mime_img = MIMEImage(visitor.qr_image.read())
                        mime_img.add_header('Content-ID', '<image>')
                    email.attach(mime_img)
                    email.attach_alternative(html_email, "text/html")
                    email.send(fail_silently=False)
                except Exception as e:
                    raise e

                if not security:
                    device = Device.objects.get(pk=visitor.tenant.device.pk)
                    host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                    absolute_uri = sys.argv[-1]
                    push_to_fra(device, host, absolute_uri, visitor)
                    

                messages.success(request, 'Success')
                return render(request, 'visitors/success_kiosk.html', { 'code': visitor.code, 'visitor': visitor  })
        else:
            print('form_invalid')

    # context['code'] = tenant.code
    # context['tenant'] = tenant
    context['form'] = form
    context['hosts'] = hosts
    return render(request, 'visitors/visitor_self_register_mobile.html', context)

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
            form = VisitorRegistrationForm(request.POST)
            
            if form.is_valid():
                form.clean()
                visitor = form.save(commit=True)
                qr_image = qrcode.make(visitor.code)
                qr_offset = Image.new('RGB', (280,280), 'white')
                draw_img = ImageDraw.Draw(qr_offset)
                qr_offset.paste(qr_image)
                filename = f'{visitor.code}_{visitor.identification_no}'
                print('filename qr', filename)
                thumb_io  = BytesIO()
                qr_offset.save(thumb_io , 'PNG')
                visitor.qr_image.save(filename+'.png', ContentFile(thumb_io.getvalue()), save=False)
                qr_offset.close()
                visitor.tenant = tenant

                try:                   
                    # photoTemp = request.FILES["photo"].name
                    # photoTemp = str(photoTemp)

                    # tempPath = os.path.join(BASE_DIR, 'static', 'media')

                    # with open(f"{tempPath}/{photoTemp}", 'rb') as f:   # use 'rb' mode for python3
                    #     data = File(f)
                    #     filename = f'{visitor.code}_{visitor.identification_no}.jpg'
                    #     visitor.photo.save(filename, data, True)

                    if request.POST['photo2'] != '':
                        photoTemp = request.POST['photo2']
                        trimmed_base64_string = photoTemp.replace('data:image/jpeg;base64,', '')
                        imgdata = base64.b64decode(trimmed_base64_string)
                        filePrefix = md5(str(localtime()).encode('utf-8')).hexdigest()
                        filename = filePrefix+'_visitors.jpg'
                        visitor.photo = ContentFile(imgdata, filename)

                    if security:
                        visitor.is_approved = 1
                    else:
                        visitor.is_approved = 2
                    visitor.save()

                    # pass visitor to check their past data from FRA
                    try:
                        get_all_possible_same_visitor_by_phone_no = Visitor.objects.filter(contact_no__icontains = visitor.contact_no)
                        clear_redundant_visitor(get_all_possible_same_visitor_by_phone_no, request.scheme)
                    except:
                        print('deleting past data not available at the moment')

                    if visitor.photo:
                        im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                    email_template = 'emailnew/visitor_registration.html'
                    email_context = { 'visitor': visitor }

                    try:
                        if visitor.email:
                            to = [ visitor.email, tenant.user.email ]
                        else:
                            to = [ tenant.user.email ]
                        html_email = render_to_string(email_template, email_context)
                        email = EmailMultiAlternatives(
                            subject='VMS-Luzerne: Visitor Appointment Registration',
                            body='mail testing',
                            from_email='ifa@concorde.com.sg',
                            to = to
                        )
                        from email.mime.image import MIMEImage
                        if visitor.qr_image:
                            mime_img = MIMEImage(visitor.qr_image.read())
                            mime_img.add_header('Content-ID', '<image>')
                        email.attach(mime_img)
                        email.attach_alternative(html_email, "text/html")
                        email.send(fail_silently=False)
 
                    except Exception as e:
                        raise e

                    if not security:
                        device = Device.objects.get(pk=visitor.tenant.device.pk)
                        host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                        absolute_uri = sys.argv[-1]
                        push_to_fra(device, host, absolute_uri, visitor)

                    messages.success(request, 'Success')
                    return render(request, 'visitors/success.html', { 'code': visitor.code, 'visitor': visitor })

                # CASE when visitor not include face photo
                except:
                    if security:
                        visitor.is_approved = 1
                    else:
                        visitor.is_approved = 2
                    visitor.save()

                    # pass visitor to check their past data from FRA
                    try:
                        get_all_possible_same_visitor_by_phone_no = Visitor.objects.filter(contact_no__icontains = visitor.contact_no)
                        clear_redundant_visitor(get_all_possible_same_visitor_by_phone_no, request.scheme)
                    except:
                        print('deleting past data not available at the moment')

                    if visitor.photo:
                        im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                    email_template = 'emailnew/visitor_registration.html'
                    email_context = { 'visitor': visitor }

                    try:
                        if visitor.email:
                            to = [ visitor.email, tenant.user.email ]
                        else:
                            to = [ tenant.user.email ]
                        html_email = render_to_string(email_template, email_context)
                        email = EmailMultiAlternatives(
                            subject='VMS-Luzerne: Visitor Appointment Registration',
                            body='mail testing',
                            from_email='ifa@concorde.com.sg',
                            to = to
                        )
                        from email.mime.image import MIMEImage
                        if visitor.qr_image:
                            mime_img = MIMEImage(visitor.qr_image.read())
                            mime_img.add_header('Content-ID', '<image>')
                        email.attach(mime_img)
                        email.attach_alternative(html_email, "text/html")
                        email.send(fail_silently=False)
                    except Exception as e:
                        raise e

                    if not security:
                        device = Device.objects.get(pk=visitor.tenant.device.pk)
                        host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                        absolute_uri = sys.argv[-1]
                        push_to_fra(device, host, absolute_uri, visitor)
                        

                    messages.success(request, 'Success')
                    return render(request, 'visitors/success.html', { 'code': visitor.code, 'visitor': visitor })
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
        hosts = HostForm(request.POST or None)

        if request.method == 'POST':
            tenant_id = request.POST.get('tenant')
            tenant = Tenant.objects.get(user_id=tenant_id)

            if form.is_valid():
                form.clean()
                visitor = form.save(commit=True)
                # visitor.start_date = datetime.now()
                # generate QR code image from visitor code, this will serve as check in
                qr_image = qrcode.make(visitor.code)
                qr_offset = Image.new('RGB', (280,280), 'white')
                draw_img = ImageDraw.Draw(qr_offset)
                qr_offset.paste(qr_image)
                filename = f'{visitor.code}_{visitor.identification_no}'
                print('filename qr', filename)
                thumb_io  = BytesIO()
                qr_offset.save(thumb_io , 'PNG')
                visitor.qr_image.save(filename+'.png', ContentFile(thumb_io.getvalue()), save=False)
                qr_offset.close()
                visitor.tenant = tenant

                if request.POST['id_photo'] != '':
                    photoTemp = request.POST['id_photo']
                    trimmed_base64_string = photoTemp.replace('data:image/jpeg;base64,', '')
                    imgdata = base64.b64decode(trimmed_base64_string)
                    filePrefix = md5(str(localtime()).encode('utf-8')).hexdigest()
                    filename = filePrefix+'_tempImg.jpg'

                    visitor.photo = ContentFile(imgdata, filename)

                if security:
                    visitor.is_approved = 1
                else:
                    visitor.is_approved = 2
                
                visitor.save()

                # pass visitor to check their past data from FRA
                try:
                    get_all_possible_same_visitor_by_phone_no = Visitor.objects.filter(contact_no__icontains = visitor.contact_no)
                    clear_redundant_visitor(get_all_possible_same_visitor_by_phone_no, request.scheme)
                except:
                    print('deleting past data not available at the moment')
                
                # Store thumbnail picture version
                if visitor.photo:
                    im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                # Emailing when enable
                email_template = 'emailnew/visitor_registration.html'
                email_context = { 'visitor': visitor }

                try:
                    html_email = render_to_string(email_template, email_context)
                    if visitor.email:
                        to = [ visitor.email, tenant.user.email ]
                    else:
                        to = [ tenant.user.email ]
                    email = EmailMultiAlternatives(
                        subject='VMS-Luzerne: Visitor Appointment Registration',
                        body='mail testing',
                        from_email='ifa@concorde.com.sg',
                        to = to
                    )
                    from email.mime.image import MIMEImage
                    if visitor.qr_image:
                        mime_img = MIMEImage(visitor.qr_image.read())
                        mime_img.add_header('Content-ID', '<image>')
                    email.attach(mime_img)
                    email.attach_alternative(html_email, "text/html")
                    email.send(fail_silently=False)
                except Exception as e:
                    raise e

                #check-in func
                device = Device.objects.get(pk=visitor.tenant.device.pk)
                host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
                absolute_uri = sys.argv[-1]

                if not security:
                    push_to_fra(device, host, absolute_uri, visitor)

                from django.conf import settings
                url = settings.DOMAIN_SET
                    
                self_register_url = str( url + '/self-register' )
                
            messages.success(request, 'Visitor Registration Success. Thank you.')
            return render(request, 'visitors/success_kiosk.html', { 'code': visitor.code, 'visitor': visitor, 'self_register_url': self_register_url })
            
        context = { 'segment': 'visitors kiosk', 'form': form, 'hosts': hosts }

        return render(request, 'visitors/visitor_self_register.html', context)

def staff_reg(request, *args, **kwargs):

    try:
        form = StaffRegistrationForm(request.POST or None)
        code = str(kwargs.get('refs_tenant'))
        tenant = Tenant.objects.get(code=code)

        if request.method == 'POST':
            form = StaffRegistrationForm(request.POST)
            if form.is_valid():
                staff = form.save(commit=False)
                staff.tenant = tenant
                staff.is_approved = 1

                try:
                    # photoTemp = request.FILES["photo"].name
                    # photoTemp = str(photoTemp)

                    # tempPath = os.path.join(BASE_DIR, 'static', 'media')

                    # with open(f"{tempPath}/{photoTemp}", 'rb') as f:   # use 'rb' mode for python3
                    #     data = File(f)
                    #     filename = f'{code}_{staff.identification_no}.jpg'
                    #     staff.photo.save(filename, data, True)
                    if request.POST['photo2'] != '':
                        photoTemp = request.POST['photo2']
                        trimmed_base64_string = photoTemp.replace('data:image/jpeg;base64,', '')
                        imgdata = base64.b64decode(trimmed_base64_string)
                        filePrefix = md5(str(localtime()).encode('utf-8')).hexdigest()
                        filename = filePrefix+'_staffs.jpg'
                        staff.photo = ContentFile(imgdata, filename)

                    staff.save()

                    email_template = 'emailnew/staff_pending.html'
                    email_context = { 'code': staff.code, 'approval_status': staff.is_approved }

                    try:
                        html_email = render_to_string(email_template, email_context)
                        email = EmailMultiAlternatives(
                            subject='VMS-Luzerne: Staff Registration',
                            body='mail testing',
                            from_email='ifa@concorde.com.sg',
                            to = [ staff.email, tenant.user.email ]
                        )
                        email.attach_alternative(html_email, "text/html")
                        email.send(fail_silently=False)
                    except Exception as e:
                        raise e

                    messages.success(request, 'Staff Registration Success. Thank you.')
                    return render(request, 'staffs/success.html', { 'code': staff.code, 'staff': staff })
                except:
                    staff.save()

                    email_template = 'emailnew/staff_pending.html'
                    email_context = { 'code': staff.code, 'approval_status': staff.is_approved }

                    try:
                        html_email = render_to_string(email_template, email_context)
                        email = EmailMultiAlternatives(
                            subject='VMS-Luzerne: Staff Registration',
                            body='mail testing',
                            from_email='ifa@concorde.com.sg',
                            to = [ staff.email, tenant.user.email ]
                        )
                        email.attach_alternative(html_email, "text/html")
                        email.send(fail_silently=False)
                    except Exception as e:
                        raise e

                    messages.success(request, 'Staff Registration Success. Thank you.')
                    return render(request, 'staffs/success.html', { 'code': staff.code, 'staff': staff })

        context = { 'segment': 'staffs', 'tenant': tenant, 'form': form, 'code': code }
        return render(request, 'staffs/staff_self_register.html', context)
    except:
        return HttpResponseForbidden('<h1>403 Forbidden</h1>', content_type='text/html')

def search_registration(request):
    context = {}
    if request.method == 'POST':
        print( request.POST.get('search') )
        try:
            visitor = Visitor.objects.get(contact_no=request.POST.get('search'))
            return HttpResponseRedirect( reverse('search-result', kwargs={'mobile': visitor.contact_no}) )

        except Visitor.DoesNotExist as e:
            return render(request, 'search/search_mobile.html', { 'notfound': 'Visitor registration not found. Kindly do a self registration or try with another number. Thank you.' })
    return render(request, 'search/search_mobile.html', context)

def search_result(request, *args, **kwargs):
    mobile = str(kwargs.get('mobile', ''))
    try:
        visitor = Visitor.objects.get(contact_no__exact=mobile)
        form = VisitorUpdateRegistrationForm(request.POST or None, request.FILES or None, instance=visitor)

        if request.method == 'POST':
            print(request.POST)
            if form.is_valid():
                tenant = Tenant.objects.get(pk=request.POST.get('tenant'))
                form.clean()
                visitor_update = form.save(commit=False)
                visitor_update.tenant = tenant
                visitor_update.save()

                messages.success(request, 'You have successfully update your registration.')

            else:
                print('invalid')
                form.errors

    except Visitor.DoesNotExist as e:
        return HttpResponseBadRequest()

    return render (request, 'search/result.html', {'form': form, 'visitor': visitor})

def check_in(request):
    context = {}
    if request.method == 'POST':

        try:
            if request.POST.get('cond') == 'search':
                visitor = Visitor.objects.get(code=request.POST.get('search'))

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
                elif visitor.is_approved == 3:
                    return JsonResponse({
                        'error': True,
                        'data': "Your entries has been denied by Host. Kindly contact Host for further information.",
                    }) 
                else:
                    return JsonResponse({
                        'error': False,
                    })
            elif request.POST.get('cond') == 'phone':
                # Filter list queryset of visitor with same phone no
                phone = request.POST.get('phone')

                visitor = Visitor.objects.filter(contact_no__icontains = phone, is_checkin=False, is_active=True)
                if visitor:
                    for v in visitor:
                        if v.is_approved == 2 and v.is_active == True:
                            return JsonResponse({
                                'error': False,
                            })
                        else:
                            return JsonResponse({
                                'error': True,
                                'data': "Your entries has been denied by Host. Kindly contact Host for further information.",
                            })
                    
                else:
                    return JsonResponse({
                    'error': True,
                    'data': "Details not found.",
                })
            else:
                return JsonResponse({
                    'error': True,
                    'data': "Try again.",
                }) 

        except Visitor.DoesNotExist as e:
            return JsonResponse({
                'error': True,
                'data': "Opps, The details you provided not exist. Try Again.",
            })
    return render(request, 'check_in/check_in.html', context)

def details_checkin(request, *args, **kwargs):

    if request.is_ajax():
        template_name = 'check_in/modal/checkin_detail_inner.html'
    else:
        template_name = 'check_in/modal/checkin_detail.html'

    search = request.GET.get('search')
    phone = request.GET.get('phone')

    if request.GET.get('condition') == 'search':
        visitor = get_object_or_404(Visitor, code__exact=search)
    elif request.GET.get('condition') == 'phone':
        visitor = Visitor.objects.filter(contact_no__icontains=phone, is_checkin=False, is_active=True, is_approved=2)

        # find closest date to visitor list
        if visitor:
            current_dt = datetime.now()
            visitor_dt = []
            for v in visitor:
                visitor_dt.append(v.start_date)

            closest_date = min(visitor_dt, key=lambda d: abs(d - current_dt))
            if closest_date < current_dt:
                print('You cannot check in past data registration')
                visitor = Visitor.objects.filter(start_date=closest_date).first()
            else:
                visitor = Visitor.objects.get(start_date=closest_date)
    else:
        visitor = Visitor.objects.get(id = request.POST.get('visitor_id'))

    form = VisitorCheckInForm(request.POST or None, request.FILES or None, instance=visitor)

    if request.is_ajax() and request.method == 'POST':
        if visitor.is_approved == 2:
            if form.is_valid():
                # Step 1: Check date time with datetime now / also done using form.clean(), save data for temp process to allow FRA data push first
                # form.clean()
                visitor_update = form.save(commit=False)
                visitor_update.start_date = datetime.now()
                visitor_update.save()

                # Try Except push to FRA Logic with the updated info
                device = Device.objects.get(pk=visitor_update.tenant.device.pk)
                host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
                absolute_uri = sys.argv[-1]

                try:
                    initialize = initiate(device.device_username, device.device_password)
                    auth = initialize['auth']

                    if initialize['client'] and auth:
                        if visitor_update.photo:
                            print('here')
                            img = get_thumbnail(visitor_update.photo, '200x200', crop='center', quality=99)
                            faceURL = str( str(absolute_uri) + '/static' + str(img.url) )
                            print('push face url', faceURL)
                        if visitor_update.code:
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
                            valid_end = visitor_update.end_date.strftime("%Y-%m-%dT%H:%M:00")
                            
                            add_res = person_instance.add(visitor_update, user_type, valid_begin, valid_end, host, auth)
                            print(add_res)
                            a_status = add_res['statusCode'] or None

                            if a_status != 1:
                                if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
                                    edit_res = person_instance.update(visitor_update, user_type, valid_begin, valid_end, host, auth)
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
                            search_card_res = card_instance.search(visitor_update.code, host, auth)
                            print(search_card_res)
                            c_status = search_card_res['CardInfoSearch']['totalMatches']
                            print( search_card_res['CardInfoSearch']['totalMatches'] )

                            if c_status == 0:
                                print("Card not found")
                                add_card = card_instance.add(visitor_update.code, host, auth)
                                print(add_card)
                                ac_status = add_card['statusCode']

                                if ac_status != 1:
                                    return JsonResponse({
                                        'error': True,
                                        'data': "Check in failed during adding person Card information. Please try again. Thank you.",
                                    })

                            print("Card information added")

                            # Push Step 3: Add Picture Data, Check FPID returned - ONLY RUN THIS WHEN PHOTO IS NOT NONE
                            if visitor_update.photo:
                                face_data_instance = FaceData()
                                face_add_response = face_data_instance.face_data_add(1, visitor_update.code, visitor_update.name, faceURL, host, auth)
                                print(face_add_response)

                                f_status = face_add_response['statusCode']
                                error_msg = face_add_response['subStatusCode']
                                
                                if f_status != 1:
                                    # if add face failed, edit person face from FRA using FPID
                                    if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
                                        # if face_add_response['subStatusCode'] == 'deviceUserAlreadyExistFace':
                                        edit_face = face_data_instance.face_data_update(1, visitor_update.code, visitor_update.name, faceURL, host, auth)
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
                                        search_res = person_instance.search(visitor_update.code, host, auth)
                                        print(search_res)

                                        # delete_res = person_instance.delete(visitor_update.code, host, auth)
                                        # print(delete_res)

                                        # return JsonResponse({
                                        #     'error': True,
                                        #     'data': f"Check in failed during face validation. Please try again by updating your face photo here. Thank you.",
                                        # })

                            # Step 4: Get All past checked in visitor with status True 
                            get_checked_in_visitor = Visitor.objects.filter(is_checkin = True)
                            # Get & loop all past visitor code - compare code to FRA & delete all visitor from FRA
                            for visitor in get_checked_in_visitor:
                                # delete every code if exist in FRA
                                if visitor.end_date <= datetime.now() or visitor.contact_no == visitor_update.contact_no:
                                    print("deleting all end date visitor")
                                    del_res = person_instance.delete(visitor.code, host, auth)
                                    print(del_res)

                            visitor_update.is_checkin = True
                            visitor_update.save()

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

                return render(request, 'check_in/checkin_success.html', { 'visitor': visitor_update })
            else:
                print('invalid')
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

def checkout(request):
    context = {}
    visitor = []

    if request.is_ajax() and request.method == 'GET':
        query = request.GET.get('q')
        visitors = Visitor.objects.filter( Q( code__exact=query ) | Q( contact_no__icontains=query ), is_checkin=True )
        
        if visitors:
            for v in visitors:
                device = Device.objects.get(pk = v.tenant.device.pk)
                host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
                # absolute_uri = sys.argv[-1]

                # loop through API FRA search Person
                initialize = initiate(device.device_username, device.device_password)
                auth = initialize['auth']

                if initialize['client'] and auth:

                    # Search Person to FRA until found
                    person_instance = Person()
                    search_res = person_instance.search(v.code, host, auth)
                    print(search_res)

                    if search_res['UserInfoSearch']['responseStatusStrg'] == 'OK':
                        if v.photo:
                            photo = v.photo.url
                        else:
                            photo = ""
                        data = {
                            'tenant': v.tenant.company_name,
                            'code': v.code,
                            'name': v.name,
                            'identification_no': v.identification_no,
                            'photo': photo,
                            'contact_no': v.contact_no,
                            'start_date': v.start_date,
                            'end_date': v.end_date,
                        }
                        visitor.append(data)
            
            return JsonResponse({
                'error': False,
                'data': json.dumps(visitor, cls=DjangoJSONEncoder)
            }, safe=False)
        else:
            return JsonResponse({
                'error': True,
                'data': []
            })

    if request.is_ajax() and request.method == 'POST':
        
        code = request.POST.get('code')

        # update visitor current checkout time, active to False
        visitor = Visitor.objects.get(code=code)

        device = Device.objects.get(pk = visitor.tenant.device.pk)
        host = str( str(request.scheme) + '://' + str(device.ip_addr) )
        # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
        # absolute_uri = sys.argv[-1]

        initialize = initiate(device.device_username, device.device_password)
        auth = initialize['auth']

        if initialize['client'] and auth:

            # Delete Person from FRA
            person_instance = Person()
            del_res = person_instance.delete(visitor.code, host, auth)
            print(del_res)

            visitor.is_active = False
            visitor.end_date = datetime.now()
            visitor.save()

            return JsonResponse({
                'error': False
            })

    return render(request, 'check_out/check_out.html', { 'visitor': json.dumps(visitor) } )


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
                    return JsonResponse({'valid': False, 'message': 'NRIC must be last 3 digits and an Alphabet [Case Sensitive]'})

                else:
                    return JsonResponse({'valid': True,'message': 'Ok'})
        else:
            if regval == False:
                return JsonResponse({'valid': False, 'message': 'NRIC must be last 3 digits and an Alphabet [Case Sensitive]'})
            else:
                return JsonResponse({'valid': True,'message': 'Ok'})
    return HttpResponse("nric validation")

def validate_photo(request):
    appPath = os.path.join(BASE_DIR, 'self_registration')
    cascadePath = os.path.join(f'{appPath}/haarcascade/haarcascade_frontalface_default.xml')

    photo_base64 = request.POST.get('photo')
    format, imgstr = photo_base64.split(';base64,') 
    ext = format.split('/')[-1]

    with open(f"{appPath}/temp/temp." + ext, "wb") as f:
        f.write(base64.b64decode(imgstr))

    faceCascade = cv2.CascadeClassifier(cascadePath)
    img = cv2.imread(os.path.join(f'{appPath}/temp/temp.' + ext))
    grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    detect_face = faceCascade.detectMultiScale(
        grayscale,
        scaleFactor = 1.3,
        minNeighbors = 5,
        minSize = (30,30),
    )
    
    print("Found %s faces!" % len(detect_face))

    if len(detect_face) == 1:

        # Handle face photo manipulation for optimized zoom-in view
        dt = datetime.now()
        dt = dt.replace(tzinfo=timezone.utc).timestamp() * 1000
        dt = int(dt)

        for (x, y, w, h) in detect_face:
            # new_x = int( x - (0.1 * x) )
            # new_x = 0.5*new_x
            
            # new_y = int( y - (0.1 * y) )
            # new_y = 0.5*new_y
            # w = int( w + (0.7 * w) )
            # h = int( h + (0.8 * h) )
            # cv2.rectangle(img, (new_x,new_y), (new_x+w, new_y+h), (0, 255, 0), 1)
            # faces = img[new_y:new_y+h, new_x:new_x+w]
            faces = img[y:y+h, x:x+w]

            tempPath = os.path.join(BASE_DIR, 'static', 'media')
            filename = str(dt) + '_' + str(w) + str(h) + '_face.' + ext
            cv2.imwrite(os.path.join( tempPath, filename ), faces)

            # return Json Response of image
            try:
                with open(f"{tempPath}\\{dt}_{w}{h}_face." + ext, "rb") as f:
                    # return HttpResponse(f.read(), content_type="image/jpeg")

                    # Handle image encoding to pass through json response
                    absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")

                    return JsonResponse({
                        'error': False,
                        'msg': 'Face validated ✅',
                        'photo': str( f"{absolute_uri}/static/media/{filename}" ),
                        'imgSrc': str( f"{tempPath}\\{filename}" ),
                        'filename': filename
                    })
            except IOError as ioerr:
                # return HttpResponse(IOError)
                return JsonResponse({
                    'error': True,
                    'msg': 'Face verification failed. Try again.'
                })

        # cv2.imshow("faces found", img)
        # cv2.waitKey(0)

        # return JsonResponse({
        #     'error': False,
        #     'msg': 'Face validated ✅'
        # })
    elif len(detect_face) > 1:
        return JsonResponse({
            'error': True,
            'msg': 'Face verification failed. Try upload new selfies.'
        })

    return JsonResponse({
        'error': True,
        'msg': 'Face verification failed. Try upload new selfies.'
    })


def fra_validation(request):

    try:
        context = {}
        model = PhotoValidation()
        absolute_uri = sys.argv[-1]
        from django.conf import settings
        url = settings.DOMAIN_SET
        # save photo and generate code into db
        if request.method == 'POST':
            if request.POST['type'] == 'webcam':
                photoTemp = request.POST['photo']
                trimmed_base64_string = photoTemp.replace('data:image/jpeg;base64,', '')
                imgdata = base64.b64decode(trimmed_base64_string)
                filePrefix = md5(str(localtime()).encode('utf-8')).hexdigest()
                filename = filePrefix+'_tempImg.jpg'
                model.photo = ContentFile(imgdata, filename)
                model.save()
            else:
                print(request.POST)
                # exit()
                # pass

            # push photo to FRA & return message\
            try:
                if model.photo:
                    img = get_thumbnail(model.photo, '200x200', crop='center', quality=99)
                    faceURL = str( str(request.scheme) + '://' + str(absolute_uri) + '/static' + str(img.url) )
                    print('push face url', faceURL)
                   
                if request.POST['tenant_id']:
                    test = request.POST.get('isStaffReg')
                    
                    if test == '1':
                        tenant = Tenant.objects.get(code=request.POST['tenant_id'])
                    else:
                        tenant = Tenant.objects.get(pk=request.POST['tenant_id'])
                       
                    device = Device.objects.get(pk=tenant.device.id)
                    host = str( str(request.scheme) + '://' + str(device.ip_addr) )
                    # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")

                    initialize = initiate(device.device_username, device.device_password)
                    auth = initialize['auth']

                    if initialize['client'] and auth:

                        person_instance = Person()
                        user_type = 'visitor'

                        # Person Add - Step 2: Manipulating date to match time local format --> "endTime":"2023-02-09T17:30:08",
                        # valid_begin = visitor_update.start_date.strftime("%Y-%m-%dT%H:%M:00")
                        
                        df = datetime.now()
                        valid_begin = df.strftime("%Y-%m-%dT%H:%M:00")
                        today = date.today()
                        df_end = df + relativedelta(years=1)
                        valid_end = df_end.strftime("%Y-%m-%dT%H:%M:00")

                        print('valid end', valid_end)
                        
                        add_res = person_instance.add_for_validation_purpose(model, user_type, valid_begin, valid_end, host, auth)
                        print(add_res)
                        a_status = add_res['statusCode'] or None

                        print(a_status)

                        face_data_instance = FaceData()
                        face_add_response = face_data_instance.face_data_add(1, model.code, model.code, faceURL, host, auth)
                        print(face_add_response)

                        if face_add_response['statusCode'] == 1:
                            # handle delete from fra after valid pushed photo
                            search_res = person_instance.search(model.code, host, auth)
                            print(search_res)

                            delete_res = person_instance.delete(model.code, host, auth)
                            print(delete_res)
                            # success case
                            
                            newPath = str( str(url) + '/static' + str(img.url) )
                            print('faceURL->',newPath)

                            tempPath = os.path.join(BASE_DIR, 'static', 'media')

                            return JsonResponse({
                                'error': False,
                                'msg': 'Face validated ✅',
                                'photo': str( f"{absolute_uri}/static/media/validated_photo/{filename}" ),
                                'imgSrc': str( f"{tempPath}\\validated_photo\\{filename}" ),
                                'filename': filename
                            })
                        else:
                            # handle delete from fra if failed to push photo
                            search_res = person_instance.search(model.code, host, auth)
                            print(search_res)

                            delete_res = person_instance.delete(model.code, host, auth)
                            print(delete_res)

                            return JsonResponse({
                                'error': True,
                                'msg': 'Face validation failed. Please retake photo.'
                            })
                else:
                    pass
            except:
                return JsonResponse({
                    'error': True,
                    'msg': 'Face validation failed. Please retake photo.'
                })

            

    except:
        # error case
        return JsonResponse({
            'error': True,
            'msg': 'Something went wrong during face validation. Try again.',
        })

def server_error(request, exception):
    return render(request, '500.html')