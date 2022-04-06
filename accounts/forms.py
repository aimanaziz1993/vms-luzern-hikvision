from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from accounts.models import Building, Floor, SecurityOption, User, Tenant, Device
from cms.forms import BootstrapHelperForm
from self_registration.utils import generate_ref_code

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
        empty_label=u'Select Devices Associated to the Tenant Floor:',
        queryset=Device.objects.all(),
        widget=forms.Select,
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "devices")
        help_texts = { k:"" for k in fields }

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
        tenant.code = generate_ref_code()
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
        empty_label=u'Select Floor:',
        queryset=Floor.objects.all(),
        widget=forms.Select,
        required=True
    )

    class Meta:
        model = Device
        fields = ('floor', 'name', 'ip_addr', 'device_id', 'is_default', 'device_username', 'device_password',)

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

    class Meta:
        model = Building
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

class FloorForm(BootstrapHelperForm, forms.ModelForm):

    building = forms.ModelChoiceField(
        empty_label=u'Select Building/Blocks Associated to the Floor:',
        queryset=Building.objects.all(),
        widget=forms.Select,
        required=True
    )
    
    class Meta:
        model = Floor
        fields = ('building', 'name', )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)