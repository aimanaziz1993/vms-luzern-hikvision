from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from accounts.models import User
from accounts.decorators import superuser_required
from cms.views import CoreListView

@method_decorator([login_required, superuser_required], name='dispatch')
class UserList(CoreListView):
    model = User

def home(request):

    if request.user.is_authenticated:
        if request.user.is_tenant:
            return redirect('tenants:home_view')
        elif request.user.is_administrator:
            return redirect('administrators:home_view')
    
    return render(request, 'dashboard/home2.html')


