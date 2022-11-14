from django.contrib.auth import login
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView
from django.core.files.base import ContentFile

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string, get_template

from accounts.decorators import superuser_required, administrator_required
from cms.ajax_views import AjaxCreateView, AjaxDeleteView, AjaxDetailView, AjaxUpdateView
from cms.views import CoreListView
from self_registration.models import Staff, Visitor

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

from ..models import Building, Device, Floor, SecurityOption, Tenant, User
from ..forms import AdminCreationForm, BuildingForm, DeviceForm, EnableSecurityForm, FloorForm, TenantCreationForm

@method_decorator([login_required, superuser_required], name='dispatch')
class AdminCreationView(CreateView):
    model = User
    form_class = AdminCreationForm
    template_name = 'accounts/create_admin.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'administrator'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "New Administrator Account created.")
        return redirect('home')

@method_decorator([login_required, administrator_required], name='dispatch')
class BuildingCreate(AjaxCreateView):
    model = Building
    form_class = BuildingForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "New Building Added.")
        return super().form_valid(form)

@method_decorator([login_required, administrator_required], name='dispatch')
class BuildingDelete(AjaxDeleteView):
    model = Building

@method_decorator([login_required, administrator_required], name='dispatch')
class FloorCreate(AjaxCreateView):
    model = Floor
    form_class = FloorForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "New Floor Added.")
        return super().form_valid(form)

@method_decorator([login_required, administrator_required], name='dispatch')
class FloorDelete(AjaxDeleteView):
    model = Floor

@method_decorator([login_required, administrator_required], name='dispatch')
class TenantList(CoreListView):
    model = Tenant

@method_decorator([login_required, administrator_required], name='dispatch')
class TenantDetail(AjaxDetailView):
    model = Tenant

    def get_context_data(self, **kwargs):
        context = super(TenantDetail, self).get_context_data(**kwargs)
        context['visitors'] = Visitor.objects.filter(tenant=self.get_object())
        print(context)
        return context

@method_decorator([login_required, administrator_required], name='dispatch')
class TenantCreate(AjaxCreateView):
    model = Tenant
    form_class = TenantCreationForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "New Tenant Created.")
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

@method_decorator([login_required, administrator_required], name='dispatch')
class TenantDelete(AjaxDeleteView):
    model = Tenant

@method_decorator([login_required, administrator_required], name='dispatch')
class DeviceList(CoreListView):
    model = Device

@method_decorator([login_required, administrator_required], name='dispatch')
class DeviceDetail(AjaxDetailView):
    model = Device

@method_decorator([login_required, administrator_required], name='dispatch')
class DeviceCreate(AjaxCreateView):
    model = Device
    form_class = DeviceForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Device successfully added.")
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

@method_decorator([login_required, administrator_required], name='dispatch')
class DeviceUpdate(AjaxUpdateView):
    model = Device
    form_class = DeviceForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Device successfully updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

@method_decorator([login_required, administrator_required], name='dispatch')
class DeviceDelete(AjaxDeleteView):
    model = Device

@method_decorator([login_required, administrator_required], name='dispatch')
class VisitorList(CoreListView):
    model = Visitor
    template_name = 'accounts/admin_visitor_list.html'

    ordering = ['-created_at']

@method_decorator([login_required, administrator_required], name='dispatch')
class AdminVisitorDetail(AjaxDetailView):
    model = Visitor

@method_decorator([login_required, administrator_required], name='dispatch')
class AdminVisitorDelete(AjaxDeleteView):
    model = Visitor
    template_name = 'accounts/admin_visitor_confirm_delete.html'

@method_decorator([login_required, administrator_required], name='dispatch')
class AdminStaffList(CoreListView):
    model = Staff
    template_name = 'accounts/admin_staff_list.html'

    ordering = ['-tenant_id']

@method_decorator([login_required, administrator_required], name='dispatch')
class AdminStaffDetail(AjaxDetailView):
    model = Staff

@method_decorator([login_required, administrator_required], name='dispatch')
class AdminStaffDelete(AjaxDeleteView):
    model = Staff
    template_name = 'accounts/admin_staff_confirm_delete.html'

    def post(self, *args, **kwargs):
        if self.request.is_ajax():
            self.object = self.get_object()
            # search FRA for user
            device = Device.objects.get(pk=self.object.tenant.device.pk)
            host = str( str(self.request.scheme) + '://' + str(device.ip_addr) )
            
            initialize = initiate(device.device_username, device.device_password)
            auth = initialize['auth']

            if self.object.is_approved == 2:
                if initialize['client'] and auth:
                    # Search User in FRA
                    person_instance = Person()
                    search_res = person_instance.search(self.object.code, host, auth)
                    print(search_res)

                    if search_res.status_code != 400:
                        s_status = search_res['UserInfoSearch']['responseStatusStrg']

                        # if s_status == 'NO MATCH':
                        #     messages.error(self.request, "Object Not Deleted")
                        #     self.object.delete()
                        #     return HttpResponseBadRequest()

                        if s_status == 'OK':
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
                self.object.delete()
                data = dict()
                data['form_is_valid'] = True
                messages.success(self.request, "Object Deleted Successfully")
                return JsonResponse(data)
        else:
            pass
            # return self.delete(*args, **kwargs)

@login_required
@administrator_required
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
                    # from_email='notification.vms@blivracle.com',
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
                    df_end = datetime.now()
                    df_end = df_end + relativedelta(years=1)
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
@administrator_required
def visitor_approval(request, pk):
    visitor = Visitor.objects.get(pk=pk)

    if request.POST:
        if request.POST.get('pk') == '3':
            visitor.is_active = False
            visitor.is_approved = request.POST.get('pk')
            # email_template = 'emailnew/staff_rejected.html'
        else:
            # email_template = 'emailnew/staff_approve.html'
            visitor.is_approved = request.POST.get('pk')
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

@login_required
@administrator_required
def home(request):
    global security_session
    context = {'segments': 'Administrator Home'}

    security_exist = True
    security_session = SecurityOption.objects.first()

    if security_session:
        security_exist = True
    else:
        security_exist = False

    if security_exist:
        if security_session.security:
            security = True
            request.session['security'] = security

    context['security'] = security_session

    # Building List
    buildings = Building.objects.all()
    context['buildings'] = buildings

    # Building List
    floors = Floor.objects.all()
    context['floors'] = floors

    # Local IP
    import sys
    ip = sys.argv[-1]
    context["local_ip"] = ip

    return render(request, 'dashboard/home2.html', context)

@login_required
@administrator_required
def change_security(request):

    try:
        o,created = SecurityOption.objects.get_or_create(
            pk=1, 
        )
        if created:
            o.security = True
            o.save()
        else:
            o.security = not o.security
            o.save()
        # obj = SecurityOption.objects.get(pk = request.POST.dict().get('pk'))
        # obj.security = not obj.security
        # obj.save()

        response = HttpResponse('security changed')
        response.set_cookie('security', o.security)
        return response
    except SecurityOption.DoesNotExist:
        obj = SecurityOption(security=False)
        obj.save()
        response = HttpResponse('security changed')
        response.set_cookie('security', obj.security)
        return response

