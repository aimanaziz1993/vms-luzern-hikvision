from django.contrib.auth import login
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView

import json
from datetime import datetime

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.mail import send_mail
from django.template.loader import render_to_string, get_template

from cms.ajax_views import AjaxDetailView, AjaxUpdateView
from cms.views import CoreListView
from self_registration.utils import generate_ref_code, timedeltaObj

from ..forms import TenantCreationForm, TenantProfileUpdateForm
from ..models import Tenant, User
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
        if request.POST.get('pk') == '3':
            staff.is_active = False
            email_template = 'email/staff_rejected.html'
        else:
            email_template = 'email/staff_approve.html'
        staff.is_approved = request.POST.get('pk')
        staff.save()

        email_context = {
            'code': staff.code
        }

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
            email_template = 'email/staff_rejected.html'
        else:
            email_template = 'email/staff_approve.html'
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

    # Visitors Monthly Chart
    # visitor = Visitor.objects.filter(appointment=request.user.id)
    # visitor = visitor.annotate(month=TruncMonth('start_date')).values('month').annotate(total=Count('id'))
    labels = []
    data = []

    # for item in visitor:
    #     date = item['month']
    #     get_month = datetime.strftime(date, '%B')
    #     labels.append(get_month)
    #     data.append(item['total'])

    context["labels"] = json.dumps(labels)
    context["data"] = json.dumps(data)

    return render(request, 'dashboard/home2.html', context)
