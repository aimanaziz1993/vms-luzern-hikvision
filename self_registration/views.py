import json
import re
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

from accounts.models import SecurityOption, Tenant
from self_registration.utils import generate_ref_code
from .models import Visitor
from .forms import VisitorCheckInForm, VisitorKioskRegistrationForm, VisitorRegistrationForm, StaffRegistrationForm

from sorl.thumbnail import get_thumbnail

def visitor_reg(request, *args, **kwargs):
    try:
        context = {}
        try:
            security = SecurityOption.objects.first()
            security = security.security
        except:
            pass

        form = VisitorRegistrationForm(request.POST or None)
        code = str(kwargs.get('refs_tenant'))
        tenant = Tenant.objects.get(code=code)

        if request.method == 'POST':
            form = VisitorRegistrationForm(request.POST, request.FILES)
            if form.is_valid():
                form.clean()
                visitor = form.save(commit=False)
                visitor.tenant = tenant
                visitor.save()

                # visitor.appointment.add(tenant)
                # visitor.save()

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

                # logic for security
                if security:
                    pass

                messages.success(request, 'Success')
                return render(request, 'visitors/success.html', { 'code': visitor.code })
            else:
                print('form_invalid')

        context['code'] = code
        context['tenant'] = tenant
        context['form'] = form
        return render(request, 'visitors/visitor_self_register.html', context)
    except:
        print('here')
        security = SecurityOption.objects.first()
        security = security.security

        context = {}
        context['code'] = None
        form = VisitorKioskRegistrationForm(request.POST or None, request.FILES or None)

        if request.method == 'POST':
            # appointments = request.POST.getlist('appointment')

            if form.is_valid():
                form.clean()
                visitor = form.save(commit=False)

                # if security:
                #     visitor.is_approved = 1
                # else:
                #     visitor.is_approved = 2
                
                visitor.save()
                
                # for a in appointments:
                #     visitor.appointment.add(a)

                # visitor.save()

                if visitor.photo:
                    im = get_thumbnail(visitor.photo, '300x300', crop='center', quality=99)

                messages.success(request, 'Success')
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
                staff = form.save()
                staff.appointment.add(tenant)
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

                messages.success(request, 'Success')
                return render(request, 'staffs/success.html', { 'code': staff.code })

        context = { 'segment': 'staffs', 'tenant': tenant, 'form': form, 'code': code }
        return render(request, 'staffs/staff_self_register.html', context)
    except:
        # context = {}
        # context['code'] = None
        # return render(request, 'staffs/staff_self_register.html', context)
        return HttpResponseForbidden('<h1>403 Forbidden</h1>', content_type='text/html')

def check_in(request):
    context = {}

    if request.method == 'POST':

        try:
            visitor = Visitor.objects.get(code=request.POST.get('search'))

            # for v in visitor:

            if visitor.is_approved == 1 and visitor.is_active == True:
                return JsonResponse({
                    'error': True,
                    'data': 'Your registration is currently pending approval from Host. Kindly call the Host to approve your appointment. Thank you.'
                })
            elif visitor.is_approved == 2 and visitor.is_active == True:
                return JsonResponse({
                    'error': False,
                })
            elif visitor.is_approved == 2 and visitor.is_active == False:
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
                visitor_update = form.save(commit=False)
                # visitor_update.code = generate_ref_code()
                visitor_update.is_active = False
                # Add field is checked in
                # visitor_update.is_checked_in = True
                visitor_update.save()

                # Try Except push to FRA Logic with the updated info


                return render(request, 'check_in/checkin_success.html', { 'visitor': visitor_update })
            else:
                print('invalid form')

                return JsonResponse({
                    'error': True,
                    'message': form.errors
                })

        elif visitor.is_approved == 1:
            return JsonResponse({
                'error': True,
                'data': "Your registration is currently pending approval from Host. Kindly call the Host to approve your appointment. Thank you.",
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