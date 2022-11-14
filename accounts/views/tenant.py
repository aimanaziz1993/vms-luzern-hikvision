from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.core.files import File
from django.core.files.base import ContentFile
from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView
from hikvision_api.cron import clear_redundant_visitor
from hikvision_api.cron import push_to_fra 

import sys
import json
import qrcode
import qrcode.image.svg
from io import BytesIO
from PIL import Image, ImageDraw
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from hikvision_api.api import initiate, Card, FaceData, Person

from sorl.thumbnail import get_thumbnail

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string, get_template

from cms.ajax_views import AjaxDeleteView, AjaxDetailView, AjaxUpdateView
from self_registration.utils import generate_ref_code, generate_ref_code2, timedeltaObj

from ..forms import TenantCreationForm, TenantProfileUpdateForm
from ..models import Device, Tenant, User
from self_registration.models import Staff, Visitor
from ..decorators import administrator_required, tenant_required

@method_decorator([login_required, administrator_required], name='dispatch')
class TenantCreationView(CreateView):
    model = User
    form_class = TenantCreationForm
    template_name = 'accounts/create_tenant.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'tenant'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "New Tenant Account created.")

        return redirect('home')

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantProfileUpdate(UpdateView):
    model = Tenant
    template_name = 'accounts/tenant_profile_update.html'
    form_class = TenantProfileUpdateForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Profile successfully updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantVisitorList(ListView):
    model = Tenant
    # paginate_by = 10
    template_name = 'accounts/tenant_visitor_list.html'

    def get_queryset(self):
        tenant = Tenant.objects.get(user=self.request.user)
        return tenant.refs_tenant_visitor.all().filter(is_active=True).order_by('-created_at')

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantVisitorListFilter(ListView):
    model = Tenant
    template_name = 'accounts/tenant_visitor_list_filter.html'

    def get_queryset(self, *args, **kwargs):
        qs = self.kwargs['status']
        tenant = Tenant.objects.get(user=self.request.user)
        visitor = tenant.refs_tenant_visitor.all().order_by('-created_at')

        if qs == 'pending':
            query_id = 1
        elif qs == 'approved':
            query_id = 2
        elif qs == 'rejected':
            query_id = 3
        else:
            query_id = 4

        visitor = visitor.filter(is_approved=query_id)
        return visitor

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantVisitorDelete(AjaxDeleteView):
    model = Tenant
    template_name = 'accounts/tenant_visitor_confirm_delete.html'

    def get_queryset(self):
        tenant = Tenant.objects.get(user=self.request.user)
        return tenant.refs_tenant_visitor.all().order_by('-created_at')

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantVisitorDetail(AjaxDetailView):
    model = Tenant

    def get_queryset(self):
        tenant = Tenant.objects.get(user=self.request.user)
        return tenant.refs_tenant_visitor.all().order_by('-created_at')

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantStaffList(ListView):
    model = Tenant
    # paginate_by = 10
    template_name = 'accounts/tenant_staff_list.html'

    def get_queryset(self):
        tenant = Tenant.objects.get(user=self.request.user)
        return tenant.refs_tenant_staff.all().order_by('-created_at')

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantStaffListFilter(ListView):
    model = Tenant
    template_name = 'accounts/tenant_staff_list_filter.html'

    def get_queryset(self, *args, **kwargs):
        qs = self.kwargs['status']
        tenant = Tenant.objects.get(user=self.request.user)
        staff = tenant.refs_tenant_staff.all().order_by('-created_at')

        if qs == 'pending':
            query_id = 1
        elif qs == 'approved':
            query_id = 2
        elif qs == 'rejected':
            query_id = 3
        else:
            query_id = 4

        staff = staff.filter(is_approved=query_id)

        return staff

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantStaffDelete(AjaxDeleteView):
    model = Tenant
    template_name = 'accounts/tenant_staff_confirm_delete.html'

    def get_queryset(self):
        tenant = Tenant.objects.get(user=self.request.user)
        return tenant.refs_tenant_staff.all().order_by('-created_at')

    def post(self, *args, **kwargs):
        if self.request.is_ajax():
            self.object = self.get_object()
            # search FRA for user
            device = Device.objects.get(pk=self.object.tenant.device.pk)
            host = str( str(self.request.scheme) + '://' + str(device.ip_addr) )
            
            initialize = initiate(device.device_username, device.device_password)
            auth = initialize['auth']

            if self.object.is_approved == 2:
                try:
                    if initialize['client'] and auth:
                        # Search User in FRA
                        person_instance = Person()
                        search_res = person_instance.search(self.object.code, host, auth)
                        print(search_res.status_code)

                        if search_res.status_code != 400:

                            if search_res['UserInfoSearch']['responseStatusStrg'] == 'OK':
                                # s_status = search_res['UserInfoSearch']['responseStatusStrg']

                            # if s_status == 'NO MATCH':
                            #     messages.error(self.request, "Object Not Deleted")
                            #     self.object.delete()
                            #     return HttpResponseBadRequest()

                                # if s_status == 'OK':
                                    # proceed delete
                                del_res = person_instance.delete(self.object.code, host, auth)
                                print(del_res)
                                d_status = del_res['statusCode']

                                if d_status != 1:
                                    print(self)
                                    data = dict()
                                    data['form_is_valid'] = False
                                    messages.error(self.request, "Object not deleted")
                                    return JsonResponse(data)

                                self.object.delete()
                                data = dict()
                                data['form_is_valid'] = True
                                messages.success(self.request, "Object Deleted Successfully")
                                return JsonResponse(data)
                            else:
                                pass
                        self.object.delete()
                        data = dict()
                        data['form_is_valid'] = True
                        messages.success(self.request, "Object Deleted Successfully")
                        return JsonResponse(data)
                                
                except:
                    self.object.delete()
                    data = dict()
                    data['form_is_valid'] = True
                    messages.success(self.request, "Object Deleted Successfully")
                    return JsonResponse(data)
            else:
                self.object.delete()
                data = dict()
                data['form_is_valid'] = True
                messages.success(self.request, "Object Deleted Successfully")
                return JsonResponse(data)
        else:
            pass
            # return self.delete(*args, **kwargs)


@method_decorator([login_required, tenant_required], name='dispatch')
class TenantStaffDetail(AjaxDetailView):
    model = Tenant

    def get_queryset(self):
        tenant = Tenant.objects.get(user=self.request.user)
        return tenant.refs_tenant_staff.all().order_by('-created_at')

@login_required
@tenant_required
def generate_code(request):
    user_id = request.POST.get('user_id')
    tenant = Tenant.objects.get(user_id = user_id)
    if request.POST:
        tenant.code = generate_ref_code2()
        tenant.save()
    return HttpResponse("done")


@login_required
@tenant_required
def staff_approval(request, pk):
    staff = Staff.objects.get(pk=pk)
    if request.POST:
        # Cleanup string ID
        employeeNo = str(request.POST.get('employeeNo'))
        # for ch in ['\\','`','*','_','{','}','[',']','(',')','>', '@', '#','+', ' ','-','.','!','$','\'']:
        #     if ch in employeeNo:
        #         employeeNo = employeeNo.replace(ch, "")

        if request.POST.get('pk') == '3':
            staff.is_active = False
            staff.is_approved = request.POST.get('pk')
            email_template = 'emailnew/staff_rejected.html'

            try:
                # Sent Email - Approval Status
                email_context = { 'code': staff.code }
                html_email = render_to_string(email_template, email_context)
                email = EmailMultiAlternatives(
                    subject='VMS-Luzerne: Staff Registration',
                    body='mail testing',
                    from_email='ifa@concorde.com.sg',
                    to = [ staff.email, staff.tenant.user.email ]
                )
                email.attach_alternative(html_email, "text/html")
                email.send(fail_silently=False)
            except Exception as e:
                raise e
        else:
            email_template = 'emailnew/staff_approve.html'
            staff.is_approved = request.POST.get('pk')
            staff.employee_no = employeeNo.upper()
            # generate QR code image for unique card ID
            qr_image = qrcode.make(staff.code)
            qr_offset = Image.new('RGB', (280,280), 'white')
            draw_img = ImageDraw.Draw(qr_offset)
            qr_offset.paste(qr_image)
            lower_code = staff.code.lower()
            filename = f'{lower_code}_{staff.identification_no}'
            print('filename qr', filename)
            thumb_io  = BytesIO()
            qr_offset.save(thumb_io , 'PNG')
            staff.qr_image.save(filename+'.png', ContentFile(thumb_io.getvalue()), save=False)
            qr_offset.close()

        staff.save()

        if staff.is_active and staff.is_approved:
            print('active - so update fra')
            # proceed push staff data to FRA as user here
            # Try Except push to FRA Logic with the updated info
            device = Device.objects.get(pk=staff.tenant.device.pk)
            host = str( str(request.scheme) + '://' + str(device.ip_addr) )
            # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
            absolute_uri = sys.argv[-1]
            
            initialize = initiate(device.device_username, device.device_password)
            auth = initialize['auth']

            if initialize['client'] and auth:
                if staff.photo:
                    img = get_thumbnail(staff.photo, '200x200', crop='center', quality=99)
                    faceURL = str( str(absolute_uri) + '/static' + str(img.url) )
                    print('push face url', faceURL)
                
                # Try push Step 1 add person first, if failed reject check-in
                try:
                    # Person Add - Step 1: Initiate instance,
                    person_instance = Person()
                    user_type = 'normal'

                    # Person Add - Step 2: Manipulating date to match time local format --> "endTime":"2023-02-09T17:30:08",
                    df = datetime.now()
                    valid_begin = df.strftime("%Y-%m-%dT%H:%M:00")

                    # 1. get current year
                    from datetime import date
                    date_today = date.today()
                    years_left = 2037 - int( date_today.year )

                    df_end = datetime.now()
                    df_end = df_end + relativedelta(years=years_left)
                    valid_end = df_end.strftime("%Y-%m-%dT%H:%M:00")

                    add_res = person_instance.add(staff, user_type, valid_begin, valid_end, host, auth)
                    print(add_res)
                    a_status = add_res['statusCode'] or None

                    if a_status != 1:
                        if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
                            edit_res = person_instance.update(staff, user_type, valid_begin, valid_end, host, auth)
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
                    # Manage Card
                    card_instance = Card()
                    search_card_res = card_instance.search(staff.code, host, auth)
                    print(search_card_res)
                    c_status = search_card_res['CardInfoSearch']['totalMatches']

                    if c_status == 0:
                        print("Card not found")
                        # if card not found, add new card information to the person - use SetUp API
                        add_card = card_instance.add(staff.code, host, auth)
                        print(add_card)
                        ac_status = add_card['statusCode']

                        if ac_status != 1:
                            return JsonResponse({
                                'error': True,
                                'data': "Check in failed during adding person Card information. Please try again. Thank you.",
                            })

                    print("Card information added")

                    if staff.photo:
                        # Push Step 3: Add Picture Data, Check FPID returned
                        face_data_instance = FaceData()
                        face_add_response = face_data_instance.face_data_add(1, staff.code, staff.name, faceURL, host, auth)
                        print(face_add_response)

                        f_status = face_add_response['statusCode']
                        error_msg = face_add_response['subStatusCode']
                        
                        if f_status != 1:
                            # if add face failed, edit person face from FRA using FPID
                            if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
                                # if face_add_response['subStatusCode'] == 'deviceUserAlreadyExistFace':
                                edit_face = face_data_instance.face_data_update(1, staff.code, staff.name, faceURL, host, auth)
                                print(edit_face)
                                fe_status = edit_face['statusCode'] or None

                                if fe_status != 1:
                                    return JsonResponse({
                                        'error': True,
                                        'data': "Check in failed during editing person face into FRA. Please try again. Thank you.",
                                    })
                            else:
                                print('face failed to be upload')
                                pass
                                # search & delete user instance in FRA
                                # search_res = person_instance.search(staff.code, host, auth)
                                # print(search_res)

                                # delete_res = person_instance.delete(staff.code, host, auth)
                                # print(delete_res)

                                # return JsonResponse({
                                #     'error': True,
                                #     'data': f"Check in failed during face validation. Please try again by updating the face photo here. Thank you.",
                                # })

                    try:
                        # Sent Email - Approval Status
                        email_context = { 'code': staff.code, 'staff': staff }
                        html_email = render_to_string(email_template, email_context)
                        email = EmailMultiAlternatives(
                            subject='VMS-Luzerne: Staff Registration',
                            body='mail testing',
                            from_email='ifa@concorde.com.sg',
                            to = [ staff.email, staff.tenant.user.email ]
                        )
                        from email.mime.image import MIMEImage
                        if staff.qr_image:
                            mime_img = MIMEImage(staff.qr_image.read())
                            mime_img.add_header('Content-ID', '<image>')
                        email.attach(mime_img)
                        email.attach_alternative(html_email, "text/html")
                        email.send(fail_silently=False)
                    except Exception as e:
                        raise e

                except:
                    # raise e
                    return JsonResponse({
                        'error': True,
                        'data': "Something went wrong during the check in process. Please try again. Thank you.",
                    })

        data = dict()
        data['updated'] = True
        return JsonResponse(data)
    # return HttpResponse()

@login_required
@tenant_required
def visitor_approval(request, pk):
    visitor = Visitor.objects.get(pk=pk)

    if request.POST:
        if request.POST.get('pk') == '3':
            visitor.is_active = False
            visitor.is_approved = request.POST.get('pk')
            # email_template = 'emailnew/staff_rejected.html'

            visitor.save()

            email_template = 'emailnew/visitor_registration.html'

            email_context = { 'visitor': visitor }

            try:
                if visitor.email:
                    to = [ visitor.email, visitor.tenant.user.email ]
                else:
                    to = [ visitor.tenant.user.email ]
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

            data = dict()
            data['updated'] = True
            return JsonResponse(data)
        else:
            # email_template = 'emailnew/staff_approve.html'
            visitor.is_approved = request.POST.get('pk')
            visitor.save()

            email_template = 'emailnew/visitor_registration.html'

            email_context = { 'visitor': visitor }

            # pass visitor to check their past data from FRA
            try:
                get_all_possible_same_visitor_by_phone_no = Visitor.objects.filter(contact_no__icontains = visitor.contact_no)
                clear_redundant_visitor(get_all_possible_same_visitor_by_phone_no, request.scheme)
            except:
                print('deleting past data not available at the moment')

            try:
                if visitor.email:
                    to = [ visitor.email, visitor.tenant.user.email ]
                else:
                    to = [ visitor.tenant.user.email ]
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

            device = Device.objects.get(pk=visitor.tenant.device.pk)
            host = str( str(request.scheme) + '://' + str(device.ip_addr) )
            # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
            absolute_uri = sys.argv[-1]

            push_to_fra(device, host, absolute_uri, visitor)
            # try:
            #     initialize = initiate(device.device_username, device.device_password)
            #     auth = initialize['auth']

            #     if initialize['client'] and auth:
            #         if visitor.photo:
            #             print('here')
            #             img = get_thumbnail(visitor.photo, '200x200', crop='center', quality=99)
            #             faceURL = str( str(absolute_uri) + '/static' + str(img.url) )
            #             print('push face url', faceURL)
            #         if visitor.code:
            #             pass
                    
            #         # Try push Step 1 add person first, if failed reject check-in
            #         try:
            #             # Person Add - Step 1: Initiate instance,
            #             person_instance = Person()
            #             user_type = 'visitor'

            #             # Person Add - Step 2: Manipulating date to match time local format --> "endTime":"2023-02-09T17:30:08",
            #             # valid_begin = visitor_update.start_date.strftime("%Y-%m-%dT%H:%M:00")

            #             df = datetime.now()
            #             valid_begin = df.strftime("%Y-%m-%dT%H:%M:00")
            #             valid_end = visitor.end_date.strftime("%Y-%m-%dT%H:%M:00")
                        
            #             add_res = person_instance.add(visitor, user_type, valid_begin, valid_end, host, auth)
            #             print(add_res)
            #             a_status = add_res['statusCode'] or None

            #             if a_status != 1:
            #                 if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
            #                     edit_res = person_instance.update(visitor, user_type, valid_begin, valid_end, host, auth)
            #                     print(edit_res)
            #                     e_status = edit_res['statusCode'] or None

            #                     if e_status != 1:
            #                         return JsonResponse({
            #                             'error': True,
            #                             'data': "Check in failed during editing person into FRA. Please try again. Thank you.",
            #                         })
            #                 else:
            #                     return JsonResponse({
            #                         'error': True,
            #                         'data': "Check in failed during adding person into FRA. Please try again. Thank you.",
            #                     })

            #             # Step 2: Add card for employee,visitor of the building, Tenant & Building owner only (Not applicable to visitor check in)
            #             # test card
            #             card_instance = Card()
            #             search_card_res = card_instance.search(visitor.code, host, auth)
            #             print(search_card_res)
            #             c_status = search_card_res['CardInfoSearch']['totalMatches']
            #             print( search_card_res['CardInfoSearch']['totalMatches'] )

            #             if c_status == 0:
            #                 print("Card not found")
            #                 add_card = card_instance.add(visitor.code, host, auth)
            #                 print(add_card)
            #                 ac_status = add_card['statusCode']

            #                 if ac_status != 1:
            #                     return JsonResponse({
            #                         'error': True,
            #                         'data': "Check in failed during adding person Card information. Please try again. Thank you.",
            #                     })

            #             print("Card information added")

            #             # Push Step 3: Add Picture Data, Check FPID returned - ONLY RUN THIS WHEN PHOTO IS NOT NONE
            #             if visitor.photo:
            #                 face_data_instance = FaceData()
            #                 face_add_response = face_data_instance.face_data_add(1, visitor.code, visitor.name, faceURL, host, auth)
            #                 print(face_add_response)

            #                 f_status = face_add_response['statusCode']
            #                 error_msg = face_add_response['subStatusCode']
                            
            #                 if f_status != 1:
            #                     # if add face failed, edit person face from FRA using FPID
            #                     if add_res['subStatusCode'] == 'deviceUserAlreadyExist':
            #                         # if face_add_response['subStatusCode'] == 'deviceUserAlreadyExistFace':
            #                         edit_face = face_data_instance.face_data_update(1, visitor.code, visitor.name, faceURL, host, auth)
            #                         print(edit_face)
            #                         fe_status = edit_face['statusCode'] or None

            #                         if fe_status != 1:
            #                             return JsonResponse({
            #                                 'error': True,
            #                                 'data': "Check in failed during editing person face into FRA. Please try again. Thank you.",
            #                             })
            #                     else:
            #                         print('face failed to be upload')
            #                         # search & delete user instance in FRA
            #                         search_res = person_instance.search(visitor.code, host, auth)
            #                         print(search_res)

            #                         # delete_res = person_instance.delete(visitor_update.code, host, auth)
            #                         # print(delete_res)

            #                         # return JsonResponse({
            #                         #     'error': True,
            #                         #     'data': f"Check in failed during face validation. Please try again by updating your face photo here. Thank you.",
            #                         # })

            #             # Step 4: Get All past checked in visitor with status True 
            #             get_checked_in_visitor = Visitor.objects.filter(is_checkin = True)
            #             # Get & loop all past visitor code - compare code to FRA & delete all visitor from FRA
            #             for visitor in get_checked_in_visitor:
            #                 # delete every code if exist in FRA
            #                 if visitor.end_date <= datetime.now() or visitor.contact_no == visitor.contact_no:
            #                     print("deleting all end date visitor")
            #                     del_res = person_instance.delete(visitor.code, host, auth)
            #                     print(del_res)

            #             visitor.is_checkin = True
            #             visitor.save()

            #             return JsonResponse({
            #                 'error': False
            #             })

            #         except:
            #             # t = loader.get_template('templates/500.html')
            #             # template = loader.get_template('templates/500.html')
            #             # return HttpResponse(template)
            #             return JsonResponse({
            #                 'error': True,
            #                 'data': "Something went wrong during the check in process. Please try again. Thank you.",
            #             })
            # except:
            #     pass


            data = dict()
            data['updated'] = True
            return JsonResponse(data)

@login_required
@tenant_required
def home(request):
    context = {'segment': 'Tenant Home'}

    tenant = Tenant.objects.get(user=request.user)
    visitors = tenant.refs_tenant_visitor.all()
    staffs = tenant.refs_tenant_staff.all()

    # Total Staffs
    tot_staffs = staffs.count()
    # tot_staffs = Staff.objects.filter(tenant=tenant, is_active=True).count()
    context['tot_staffs'] = tot_staffs

    # Total Visits
    tot_visits = visitors.count()
    context['tot_visits'] = tot_visits

    # Today Visitor
    # date__today = datetime.today()
    from datetime import date
    today_visits = visitors.filter(tenant=tenant, start_date__date=date.today()).count()
    context['today_visits'] = today_visits

    # Pending Approval
    pending_staff = staffs.filter(tenant=tenant, is_approved=1).count()
    pending_visitor = visitors.filter(tenant=tenant, is_approved=1).count()
    tot_pending = pending_staff + pending_visitor
    context['tot_pending'] = tot_pending

    # Visitors Monthly Chart
    # visitor = Visitor.objects.filter(tenant=tenant)
    visitor = visitors.annotate(month=TruncMonth('start_date')).values('month').annotate(total=Count('id'))
    labels = []
    data = []

    for item in visitor:
        date = item['month']

        if (datetime.strftime(date, '%Y') == datetime.strftime(datetime.now(), '%Y')):
            get_month = datetime.strftime(item['month'], '%B')
            labels.append(get_month)
            data.append(item['total'])

    context["labels"] = json.dumps(labels)
    context["data"] = json.dumps(data)

    # Staffs Monthly Chart
    # staff = staffs.annotate(month=TruncMonth('start_date')).values('month').annotate(total=Count('id'))
    # labelsS = []
    # dataS = []

    # for item in staff:
    #     date = item['month']

    #     if (datetime.strftime(date, '%Y') == datetime.strftime(datetime.now(), '%Y')):
    #         get_month = datetime.strftime(item['month'], '%B')
    #         labelsS.append(get_month)
    #         dataS.append(item['total'])

    # context["labelsS"] = json.dumps(labelsS)
    # context["dataS"] = json.dumps(dataS)

    return render(request, 'dashboard/home2.html', context)
