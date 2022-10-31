from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from accounts.models import Building, Floor, SecurityOption, User, Tenant, Device
from cms.forms import BootstrapHelperForm
from self_registration.utils import generate_ref_code, generate_ref_code2

class EnableSecurityForm(BootstrapHelperForm, forms.ModelForm):

    security = forms.BooleanField(
        label=("Enable/Disable High Security"),
    )

    class Meta:
        model = SecurityOption
        fields = ('security',)

class AdminCreationForm(BootstrapHelperForm, UserCreationForm):
    error_css_class = 'error'
    email = forms.EmailField(required=True, label='Email')
    password1 = forms.CharField(
        label=("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label=("Re-enter password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")
        help_texts = { k:"" for k in fields }

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_administrator = True
        user.save()
        return user

class TenantCreationForm(BootstrapHelperForm, UserCreationForm):
    error_css_class = 'error'
    email = forms.EmailField(required=True, label='Email')
    password1 = forms.CharField(
        label=("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label=("Re-enter password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    devices = forms.ModelChoiceField(
        label=("Block/Level"),
        empty_label=u'Select Block, Level:',
        queryset=Device.objects.all(),
        widget=forms.Select,
        required=True
    )

    company_name = forms.CharField(
        required=True
    )

    unit_no = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "company_name", "devices", "unit_no")
        help_texts = { k:"" for k in fields }

        # widgets = {
        #     'unit_no': forms.HiddenInput(),
        # }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_tenant = True
        user.save()
        tenant = Tenant()
        tenant.user = user
        device = self.cleaned_data.get('devices')
        tenant.device = device
        tenant.building = device.building.name
        tenant.floor = device.floor.name
        company_name = self.cleaned_data.get('company_name')
        tenant.company_name = company_name.upper()
        unit_no = self.cleaned_data.get('unit_no')
        tenant.unit_no = unit_no
        tenant.code = generate_ref_code2()
        tenant.save()
        return user

class TenantProfileUpdateForm(BootstrapHelperForm, forms.ModelForm):
    class Meta:
        model = Tenant
        # fields = '__all__'
        exclude = ('user', 'device', 'code', 'building', 'floor', )

        widgets = {
            # 'building': forms.Select(attrs={ 'placeholder': 'Select' }), 
            # 'floor': forms.Select(attrs={ 'placeholder': 'Select' }),
            'company_name': forms.TextInput(attrs={'style': 'text-transform:uppercase;'}),
            'registered_address':forms.TextInput(attrs={'style': 'text-transform:uppercase;'}),
        }

    # def __init__(self, *args, **kwargs):
    #     request = kwargs.pop('request')
    #     super().__init__(*args, **kwargs)

class DeviceForm(BootstrapHelperForm, forms.ModelForm):

    device_password = forms.CharField(
        label=("Device password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    floor = forms.ModelChoiceField(
        label=_("Level"),
        empty_label=u'Select Level:',
        queryset=Floor.objects.all(),
        widget=forms.Select,
        required=True
    )

    class Meta:
        model = Device
        fields = ('floor', 'device_id', 'name', 'ip_addr', 'device_username', 'device_password',)

        labels = {
            'ip_addr': 'IP Address (e.g 192.168.x.x)',
            'device_id': 'Device ID (Optional)'
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def save(self):
        device = super().save(commit=False)
        floor = self.cleaned_data.get('floor')
        device.building = floor.building
        device.save()
        return device

class BuildingForm(BootstrapHelperForm, forms.ModelForm):

    name = forms.CharField(
        label=_("Block"),
        required=True
    )

    class Meta:
        model = Building
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

class FloorForm(BootstrapHelperForm, forms.ModelForm):

    building = forms.ModelChoiceField(
        label=_("Block"),
        empty_label=u'Select Blocks Associated:',
        queryset=Building.objects.all(),
        widget=forms.Select,
        required=True,
    )

    name = forms.IntegerField(
        label=_("Level"),
        required=True
    )
    
    class Meta:
        model = Floor
        fields = ('building', 'name', )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)