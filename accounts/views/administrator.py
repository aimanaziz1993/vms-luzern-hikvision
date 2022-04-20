from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, TemplateView, ListView

from accounts.decorators import superuser_required, administrator_required
from cms.ajax_views import AjaxCreateView, AjaxDeleteView, AjaxDetailView, AjaxUpdateView
from cms.views import CoreListView
from self_registration.models import Visitor

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
class FloorCreate(AjaxCreateView):
    model = Floor
    form_class = FloorForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "New Floor Added.")
        return super().form_valid(form)

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

    # from hikvision_api.api import initiate, Event
    # initialize = initiate('admin', 'P@55w0rd')
    # auth = initialize['auth']

    # if initialize['client'] and auth:
    #     host = str( str(request.scheme) + '://' + str('192.168.200.44') )
    #     event_instance = Event()
    #     res = event_instance.search(host, auth)
    #     # print(res)
    #     events = []
    #     for item in res['AcsEvent']['InfoList']:
    #         if item['cardNo'] != '' or item['employeeNoString'] != '':
    #             # print(item)
    #             # change date string to date time
    #             events.append(item)
    #             print(events)
    # context['events'] = events
    # print(context['events'])

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

