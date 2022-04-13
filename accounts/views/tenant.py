from django.contrib.auth import login
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView

import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from hikvision_api.api import initiate, Card, FaceData, Person

from sorl.thumbnail import get_thumbnail

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string, get_template

from cms.ajax_views import AjaxDetailView, AjaxUpdateView
from cms.views import CoreListView
from self_registration.utils import generate_ref_code, timedeltaObj

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
        return tenant.refs_tenant_visitor.all().order_by('-created_at')

@method_decorator([login_required, tenant_required], name='dispatch')
class TenantVisitorListFilter(ListView):
    model = Tenant
    template_name = 'accounts/tenant_visitor_list_filter.html'

    def get_queryset(self, *args, **kwargs):
        qs = self.kwargs['status']
        tenant = Tenant.objects.get(user=self.request.user)
        visitor = tenant.refs_tenant_visitor.all()

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
        staff = tenant.refs_tenant_staff.all()

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
        tenant.code = generate_ref_code()
        tenant.save()
    return HttpResponse("done")


@login_required
@tenant_required
def staff_approval(request, pk):
    staff = Staff.objects.get(pk=pk)
    if request.POST:
        # Cleanup string ID
        employeeNo = str(request.POST.get('employeeNo'))
        for ch in ['\\','`','*','_','{','}','[',']','(',')','>', '@', '#','+', ' ','-','.','!','$','\'']:
            if ch in employeeNo:
                employeeNo = employeeNo.replace(ch, "")

        if request.POST.get('pk') == '3':
            staff.is_active = False
            email_template = 'emailnew/staff_rejected.html'
        else:
            email_template = 'emailnew/staff_approve.html'
            staff.is_approved = request.POST.get('pk')
            staff.code = employeeNo.upper()
        staff.save()

        if staff.is_active and staff.is_approved:
            print('active - so update fra')
            # proceed push staff data to FRA as user here
            # Try Except push to FRA Logic with the updated info
            device = Device.objects.get(pk=staff.tenant.device.pk)
            host = str( str(request.scheme) + '://' + str(device.ip_addr) )
            absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
            
            initialize = initiate(device.device_username, device.device_password)
            auth = initialize['auth']

            if initialize['client'] and auth:
                if staff.photo:
                    img = get_thumbnail(staff.photo, '200x200', crop='center', quality=99)
                    faceURL = str( str(absolute_uri) + '/static' + str(img.url) )
                    print('push face url', faceURL)
                # if staff.code:
                #     pass
                
                # Try push Step 1 add person first, if failed reject check-in
                try:
                    print('here')
                    # Person Add - Step 1: Initiate instance,
                    person_instance = Person()
                    print(person_instance)
                    user_type = 'normal'
                    print(user_type)
                    # Person Add - Step 2: Manipulating date to match time local format --> "endTime":"2023-02-09T17:30:08",
                    # valid_end = visitor_update.end_date.strftime("%Y-%m-%dT%H:%M:00")
                    df = datetime.now()
                    valid_begin = df.strftime("%Y-%m-%dT%H:%M:00")
                    print('begin', valid_begin)
                    # valid_end = visitor_update.end_date.strftime("%Y-%m-%dT%H:%M:00")
                    
                    df_end = datetime.now()
                    df_end = df_end + relativedelta(years=1)
                    print('+1 year', df_end)
                    valid_end = df_end.strftime("%Y-%m-%dT%H:%M:00")
                    print('end', valid_end)
                    
                    add_res = person_instance.add(staff, user_type, valid_begin, valid_end, host, auth)
                    print(add_res)
                    a_status = add_res['statusCode'] or None

                    # Finger print upload

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
                    # test card
                    card_instance = Card()
                    search_card_res = card_instance.search(staff.code, host, auth)
                    print(search_card_res)
                    c_status = search_card_res['CardInfoSearch']['totalMatches']
                    print( search_card_res['CardInfoSearch']['totalMatches'] )

                    if c_status == 0:
                        print("Card not found")
                        # return JsonResponse({
                        #     'error': True,
                        #     'data': "Card detail not found. Please try again. Thank you.",
                        # })

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
                            return JsonResponse({
                                'error': True,
                                'data': f"Check in failed during face validation. Please try again. You can always update your selfie picture here. Thank you.",
                            })

                    try:
                        # Sent Email - Approval Status
                        email_context = { 'code': staff.code }
                        html_email = render_to_string(email_template, email_context)
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

                except:
                    # raise e
                    return JsonResponse({
                        'error': True,
                        'data': "Something went wrong during the check in process. Please try again. Thank you.",
                    })

        data = dict()
        data['updated'] = True
        return JsonResponse(data)

@login_required
@tenant_required
def visitor_approval(request, pk):
    # staff = Staff.objects.get(pk=pk)
    visitor = Visitor.objects.get(pk=pk)

    user = User.objects.get(id=request.user.id)
    print(user)
    exit()

    if request.POST:
        if request.POST.get('pk') == '3':
            visitor.is_active = False
            email_template = 'emailnew/staff_rejected.html'
        else:
            email_template = 'emailnew/staff_approve.html'
        visitor.is_approved = request.POST.get('pk')
        visitor.save()

        email_context = {
            'code': visitor.code
        }

        try:
            html_email = render_to_string(email_template, email_context)
            email = send_mail(
                'VMS-Luzern: Staff Registration',
                html_email,
                'webmaster@localhost',
                [ visitor.email ],
                fail_silently=False
            )
        except Exception as e:
            raise e

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
    today_visits = Visitor.objects.filter(tenant=tenant, start_date__date=date.today()).count()
    context['today_visits'] = today_visits
    print( context['today_visits'] )

    # Pending Approval
    pending_staff = Staff.objects.filter(tenant=tenant, is_approved=1).count()
    pending_visitor = Visitor.objects.filter(tenant=tenant, is_approved=1).count()
    tot_pending = pending_staff + pending_visitor
    context['tot_pending'] = tot_pending

    # Visitors Monthly Chart
    visitor = Visitor.objects.filter(tenant=request.user.tenant)
    visitor = visitor.annotate(month=TruncMonth('start_date')).values('month').annotate(total=Count('id'))
    labels = []
    data = []

    for item in visitor:
        date = item['month']
        get_month = datetime.strftime(date, '%B')
        labels.append(get_month)
        data.append(item['total'])

    context["labels"] = json.dumps(labels)
    context["data"] = json.dumps(data)

    return render(request, 'dashboard/home2.html', context)
