import json
import re
from datetime import date, datetime, timedelta, timezone
from time import strftime
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

import qrcode
import qrcode.image.svg
from io import BytesIO
from PIL import Image, ImageDraw

from accounts.models import Device, SecurityOption, Tenant
from self_registration.utils import generate_ref_code
from .models import Visitor
from .forms import VisitorCheckInForm, VisitorKioskRegistrationForm, VisitorRegistrationForm, StaffRegistrationForm, VisitorUpdateRegistrationForm

from hikvision_api.api import initiate, Card, FaceData, Person

from sorl.thumbnail import get_thumbnail

def option_page(request):

    return render (request, 'options.html', {})


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
                visitor = form.save(commit=True)
                qr_image = qrcode.make(visitor.code)
                qr_offset = Image.new('RGB', (310,310), 'white')
                draw_img = ImageDraw.Draw(qr_offset)
                qr_offset.paste(qr_image)
                filename = f'{visitor.code}_{visitor.identification_no}'
                print('filename qr', filename)
                thumb_io  = BytesIO()
                qr_offset.save(thumb_io , 'PNG')
                visitor.qr_image.save(filename+'.png', ContentFile(thumb_io.getvalue()), save=False)
                qr_offset.close()
                visitor.tenant = tenant

                if security:
                    visitor.is_approved = 1
                else:
                    visitor.is_approved = 2
                visitor.save()

                if visitor.photo:
                    im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                email_template = 'emailnew/visitor_registration.html'

                email_context = { 'visitor': visitor }

                try:
                    html_email = render_to_string(email_template, email_context)
                    email = EmailMultiAlternatives(
                        subject='VMS-Luzern: Visitor Appointment Registration',
                        body='mail testing',
                        from_email='webmaster@localhost',
                        to = [tenant.user.email]
                    )
                    email.attach_alternative(html_email, "text/html")
                    email.send(fail_silently=False)
                    # email = send_mail(
                    #     'VMS-Luzern: Visitor Appointment Registration',
                    #     html_email,
                    #     'webmaster@localhost',
                    #     [ tenant.user.email ],
                    #     fail_silently=False
                    # )
                except Exception as e:
                    raise e

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

        if request.method == 'POST':
            tenant_id = request.POST.get('tenant')
            tenant = Tenant.objects.get(user_id=tenant_id)

            if form.is_valid():
                form.clean()
                visitor = form.save(commit=True)
                # visitor.start_date = datetime.now()
                # generate QR code image from visitor code, this will serve as check in
                qr_image = qrcode.make(visitor.code)
                qr_offset = Image.new('RGB', (310,310), 'white')
                draw_img = ImageDraw.Draw(qr_offset)
                qr_offset.paste(qr_image)
                filename = f'{visitor.code}_{visitor.identification_no}'
                print('filename qr', filename)
                thumb_io  = BytesIO()
                qr_offset.save(thumb_io , 'PNG')
                visitor.qr_image.save(filename+'.png', ContentFile(thumb_io.getvalue()), save=False)
                qr_offset.close()
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
                email_template = 'emailnew/visitor_registration.html'
                email_context = { 'visitor': visitor }

                try:
                    html_email = render_to_string(email_template, email_context)
                    # email = send_mail(
                    #     'VMS-Luzern: Visitor Appointment Registration',
                    #     html_email,
                    #     'webmaster@localhost',
                    #     [ tenant.user.email ],
                    #     fail_silently=False
                    # )
                    email = EmailMultiAlternatives(
                        subject='VMS-Luzern: Visitor Appointment Registration',
                        body='mail testing',
                        from_email='webmaster@localhost',
                        to = [ tenant.user.email ]
                    )
                    email.attach_alternative(html_email, "text/html")
                    email.send(fail_silently=False)
                except Exception as e:
                    raise e

                messages.success(request, 'Visitor Registration Success. Thank you.')
                return render(request, 'visitors/success.html', { 'code': visitor.code, 'visitor': visitor })

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

                email_template = 'emailnew/staff_pending.html'
                email_context = { 'code': staff.code, 'approval_status': staff.is_approved }

                try:
                    html_email = render_to_string(email_template, email_context)
                    # email = send_mail(
                    #     'VMS-Luzern: Staff Registration',
                    #     html_email,
                    #     'webmaster@localhost',
                    #     [ staff.email ],
                    #     fail_silently=False
                    # )
                    email = EmailMultiAlternatives(
                        subject='VMS-Luzern: Staff Registration',
                        body='mail testing',
                        from_email='webmaster@localhost',
                        to = [ staff.email ]
                    )
                    email.attach_alternative(html_email, "text/html")
                    email.send(fail_silently=False)
                except Exception as e:
                    raise e

                messages.success(request, 'Staff Registration Success. Thank you.')
                return render(request, 'staffs/success.html', { 'code': staff.code })

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
                else:
                    return JsonResponse({
                        'error': False,
                    })
            elif request.POST.get('cond') == 'phone':
                # Filter list queryset of visitor with same phone no
                visitor = Visitor.objects.filter(contact_no__icontains = request.POST.get('phone'), is_checkin=False)
                if visitor:
                    return JsonResponse({
                        'error': False,
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
        # visitor = get_object_or_404(Visitor, contact_no__icontains=phone)
        visitor = Visitor.objects.filter(contact_no__icontains=phone, is_checkin=False)

        # find closest date to visitor list
        if visitor:
            current_dt = datetime.now()
            visitor_dt = []
            for v in visitor:
                visitor_dt.append(v.start_date)

            closest_date = min(visitor_dt, key=lambda d: abs(d - current_dt))
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
                # generate QR code image for unique card ID
                qr_image = qrcode.make(visitor_update.code)
                qr_offset = Image.new('RGB', (310,310), 'white')
                draw_img = ImageDraw.Draw(qr_offset)
                qr_offset.paste(qr_image)
                filename = f'{visitor_update.code}_{visitor_update.identification_no}'
                print('filename qr', filename)
                thumb_io  = BytesIO()
                qr_offset.save(thumb_io , 'PNG')
                visitor_update.qr_image.save(filename+'.png', ContentFile(thumb_io.getvalue()), save=False)
                qr_offset.close()
                visitor_update.save()

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

                            # Push Step 3: Add Picture Data, Check FPID returned
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
                                    return JsonResponse({
                                        'error': True,
                                        'data': f"Check in failed during face validation. Please try again. You can always update your selfie picture here. Thank you.",
                                    })

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