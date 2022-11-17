from django import forms
from django.forms.widgets import Input, NumberInput, PasswordInput, RadioSelect, SelectMultiple, TextInput, FileInput, Select, SelectDateWidget, DateInput, Textarea, EmailInput
from django.db import transaction

from datetime import datetime, timezone
from accounts.models import Tenant
from cms.forms import BootstrapHelperForm
from .models import Staff, Visitor, PhotoValidation

class VisitorMobileRegistrationForm(BootstrapHelperForm, forms.ModelForm):
    
    # tenant = forms.ModelChoiceField(
    #     label=u'Select Host (Visiting Company)',
    #     empty_label=u'Select Visiting Company:',
    #     queryset=Tenant.objects.all().order_by('company_name'),
    #     widget=forms.Select,
    #     required=True
    # )

    class Meta:
        model = Visitor
        fields = ('photo', 'name', 'contact_no', 'email', 'start_date', 'end_date', 'remarks', )

        labels = {
            # 'identification_no': 'NRIC (e.g: last 3 digits and an alphabet)',
            'remarks': 'Remarks [ Optional ]',
            'email': 'Email (Optional if you want to be notified status & details)'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera', 'hidden':'True'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            # 'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'email': EmailInput(attrs={'class': 'form-control form_input'}),
            'start_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'end_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
        }

        def __init__(self, *args, **kwargs):
            super(VisitorRegistrationForm, self).__init__(*args, **kwargs)
            self.fields['start_date'].input_formats = ('%Y-%m-%dT%H:%M',)
            self.fields['end_date'].input_formats = ('%Y-%m-%dT%H:%M',)

class VisitorKioskRegistrationForm(BootstrapHelperForm, forms.ModelForm):

    # tenant = forms.ModelChoiceField(
    #     label=u'Select Host (Visiting Company)',
    #     empty_label=u'Select Visiting Company:',
    #     queryset=Tenant.objects.all().order_by('company_name'),
    #     widget=forms.Select,
    #     required=True
    # )

    class Meta:
        model = Visitor
        fields = ('name', 'contact_no', 'email', 'start_date', 'end_date', 'remarks',)
        # fields = ('photo', 'name', 'identification_no', 'contact_no', 'tenant', 'start_date', 'end_date', 'remarks',)

        labels = {
            # 'photo': 'Face Picture. Take your best possible selfie.',
            # 'identification_no': 'NRIC',
            'remarks': 'Remarks [ Optional ]',
            'email': 'Email (Optional if you want to be notified status & details)'
        }

        widgets = {
            # 'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            # 'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'email': EmailInput(attrs={'class': 'form-control form_input'}),
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
        label=u'Select Host (Visiting Company)',
        empty_label=u'Select Visiting Company:',
        queryset=Tenant.objects.all().order_by('company_name'),
        widget=forms.Select,
        required=True
    )

    class Meta:
        model = Visitor
        fields = ('photo', 'name', 'contact_no', 'tenant', 'start_date', 'end_date', 'remarks',)

        labels = {
            'photo': 'Face Picture. Take your best possible selfie.',
            'identification_no': 'NRIC.',
            'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            # 'identification_no': TextInput(attrs={'class': 'form-control form_input', 'placeholder':"e.g: last 3 digits and an alphabet"}),
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
        fields = ('photo', 'name', 'contact_no', 'email', 'start_date', 'end_date', 'remarks', )

        labels = {
            'photo': 'Face Picture. Take your best possible selfie.',
            # 'identification_no': 'NRIC (e.g: last 3 digits and an alphabet)',
            'remarks': 'Remarks [ Optional ]',
            'email': 'Email (Optional if you want to be notified status & details)'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera', 'hidden': 'TRUE'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            # 'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'email': EmailInput(attrs={'class': 'form-control form_input'}),
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
        fields = ('photo', 
                # 'name', 
                # 'identification_no', 
                # 'contact_no', 
                # 'start_date', 
                'end_date',
                # 'remarks', 
            )

        labels = {
            'photo': 'Face Picture. Take your best possible selfie.',
            # 'identification_no': 'Identification No',
            # 'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera'}),
            # 'name': TextInput(attrs={'class': 'form-control form_input'}),
            # 'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            # 'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            # 'contact_no': forms.HiddenInput(),
            # 'start_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            'end_date': DateInput(attrs={'class': 'form-control form_input', 'type': 'datetime-local' }, format='%Y-%m-%dT%H:%M'),
            # 'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
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
        fields = ('photo', 'name', 'contact_no', 'email', 'remarks', )

        labels = {
            'photo': 'Face Picture. Take your best possible selfie [ Optional ]',
            # 'identification_no': 'NRIC (e.g: last 3 digits and an alphabet)',
            'remarks': 'Remarks [ Optional ]'
        }

        widgets = {
            'photo': FileInput(attrs={'class': 'form-control form_input', 'accept': 'image/*', 'capture': 'camera', 'hidden':'TRUE'}),
            'name': TextInput(attrs={'class': 'form-control form_input'}),
            # 'identification_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': TextInput(attrs={'class': 'form-control form_input'}),
            'contact_no': forms.HiddenInput(),
            'remarks': Textarea( attrs={'class': 'form-control form_input mb-4', 'rows':6, 'cols':15} ),
        }


class HostForm(BootstrapHelperForm, forms.ModelForm):
    
    tenant = forms.ModelChoiceField(
        label=u'Select Host (Visiting Company)',
        empty_label=u'Select Visiting Company:',
        queryset=Tenant.objects.all().order_by('company_name'),
        widget=forms.Select,
        required=True
    )

    class Meta:
        model = Visitor
        fields = ('tenant',)