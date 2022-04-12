from django import forms
from django.forms.widgets import Input, NumberInput, PasswordInput, RadioSelect, SelectMultiple, TextInput, FileInput, Select, SelectDateWidget, DateInput, Textarea, EmailInput
from django.db import transaction

from datetime import datetime, timezone
from accounts.models import Tenant
from cms.forms import BootstrapHelperForm
from .models import Staff, Visitor

class VisitorKioskRegistrationForm(BootstrapHelperForm, forms.ModelForm):

    tenant = forms.ModelChoiceField(
        label=u'Select Host',
        empty_label=u'Select Host or Tenant:',
        queryset=Tenant.objects.all(),
        widget=forms.Select
    )

    class Meta:
        model = Visitor
        fields = ('photo', 'name', 'identification_no', 'contact_no', 'tenant', 'start_date', 'end_date', 'remarks',)

        labels = {
            'photo': 'Face Picture. Take your best possible selfie. [ Important ]',
            'identification_no': 'Identification No',
            'tenant': 'Select Host',
            'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera', 'required': 'required'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'start_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'end_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
        }

        def __init__(self, *args, **kwargs):
            super(VisitorRegistrationForm, self).__init__(*args, **kwargs)
            self.fields['start_date'].input_formats = ('%Y-%m-%dT%H:%M',)
            self.fields['end_date'].input_formats = ('%Y-%m-%dT%H:%M',)

class VisitorUpdateRegistrationForm(BootstrapHelperForm, forms.ModelForm):
    
    tenant = forms.ModelChoiceField(
        label=u'Select Host',
        empty_label=u'Select Host or Tenant:',
        queryset=Tenant.objects.all(),
        widget=forms.Select
    )

    class Meta:
        model = Visitor
        fields = ('photo', 'name', 'identification_no', 'contact_no', 'tenant', 'start_date', 'end_date', 'remarks',)

        labels = {
            'photo': 'Face Picture. Take your best possible selfie. [ Important ]',
            'identification_no': 'Identification No',
            'tenant': 'Select Host',
            'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'start_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'end_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
        }

        def __init__(self, *args, **kwargs):
            super(VisitorRegistrationForm, self).__init__(*args, **kwargs)
            self.fields['start_date'].input_formats = ('%Y-%m-%dT%H:%M',)
            self.fields['end_date'].input_formats = ('%Y-%m-%dT%H:%M',)
    

class VisitorRegistrationForm(BootstrapHelperForm, forms.ModelForm):

    class Meta:
        model = Visitor
        fields = ('photo', 'name', 'identification_no', 'contact_no', 'start_date', 'end_date', 'remarks', )

        labels = {
            'photo': 'Face Picture. Take your best possible selfie. [ Important ]',
            'identification_no': 'Identification No',
            'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera', 'required': 'required'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'start_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'end_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
        }

    def __init__(self, *args, **kwargs):
        super(VisitorRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end_date'].input_formats = ('%Y-%m-%dT%H:%M',)


class VisitorCheckInForm(BootstrapHelperForm, forms.ModelForm):

    # start_date = forms.DateField(widget=DateInput(
    #     attrs={'class': 'form-control form_input' }, format='%Y-%m-%dT%H:%M'
    #     # attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'
    # ))
    
    class Meta:
        model = Visitor
        fields = ('photo', 'name', 'identification_no', 'contact_no', 'start_date', 'end_date', 'remarks', )

        labels = {
            'photo': 'Face Picture. Take your best possible selfie. [ Important ]',
            'identification_no': 'Identification No',
            'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            # 'start_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'end_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
        }

        def __init__(self, *args, **kwargs):
            super(VisitorRegistrationForm, self).__init__(*args, **kwargs)
            # self.fields['start_date'].widget.attrs['readonly'] = True
            # self.fields['start_date'].input_formats = ('%Y-%m-%dT%H:%M',),
            self.fields['end_date'].input_formats = ('%Y-%m-%dT%H:%M',)

class StaffRegistrationForm(forms.ModelForm):

    email = forms.EmailField(
        label = ("Email"),
        widget=forms.EmailInput(
            attrs={'class': 'form-control form_input', 'autocomplete': 'email'})
    )
    
    class Meta:
        model = Staff
        fields = ('photo', 'name', 'identification_no', 'contact_no', 'email', 'remarks', )

        labels = {
            'photo': 'Face Picture. Take your best possible selfie. [ Important ]',
            'identification_no': 'Identification No',
            'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera', 'required': 'required'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
        }
