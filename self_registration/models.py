from turtle import ondrag
from django.db import models
from django.forms import ValidationError
from accounts.models import User, Tenant
from datetime import datetime, timezone
from PIL import Image

from .utils import generate_ref_code, generate_ref_code2

def image_max_size(width=None, height=None):

    def validator(image):
        img = Image.open(image)
        fw, fh = img.size
        if fw > width or fh > height:
            raise ValidationError(
                "Photo exceeds maximum file size allowed"
            )
        
    return validator

class Visitor(models.Model):
    PENDING_APPROVAL = 1
    APPROVED = 2
    NOT_APPROVED = 3
    APPROVE_CHOICE = {
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (NOT_APPROVED, 'Not Approved'),
    }

    name = models.CharField(max_length=120)
    identification_no = models.CharField(max_length=100, null=True)
    contact_no = models.CharField(max_length=20, null=True, blank=True)
    # photo  = models.ImageField(default="", blank=True, null=True, validators=[image_max_size(300,300)])
    photo  = models.ImageField(default="", upload_to='visitors', blank=True, null=True)
    email = models.EmailField(max_length=50, blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=12, blank=True, unique=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_checkin = models.BooleanField(default=False)
    is_approved = models.PositiveSmallIntegerField(choices=APPROVE_CHOICE, default=APPROVED, null=True)
    # appointment = models.ManyToManyField(Tenant, related_name='refs_tenant_visitor', through='VisitLog')
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, blank=True, null=True, related_name='refs_tenant_visitor')
    is_active = models.BooleanField(default=True)
    qr_image = models.ImageField(upload_to='visitors/qr', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}-{}'.format(self.name, self.code)

    def get_tenant_profiles(self):
        pass

    def clean(self):
        if self.start_date is not None and self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValidationError("Ending Time must end after it starts.")

            # if self.start_date < datetime.now():
            #     raise ValidationError("Appointment Time must starts in future. Not in the past.")

    def save(self, *args, **kwargs):
        if self.code == "":
            code = generate_ref_code()
            # code = id_generator()
            self.code = code
        super().save(*args, **kwargs)

class Staff(models.Model):
    # Staff Approval
    PENDING_APPROVAL = 1
    APPROVED = 2
    NOT_APPROVED = 3
    APPROVE_CHOICE = {
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (NOT_APPROVED, 'Not Approved'),
    }
    
    name = models.CharField(max_length=120)
    identification_no = models.CharField(max_length=100, null=True)
    contact_no = models.CharField(max_length=20, null=True)
    photo  = models.ImageField(default="", upload_to='staffs', blank=True, null=True)
    email = models.EmailField(max_length=50, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=12, blank=True, unique=True)
    employee_no = models.CharField(max_length=12, blank=True, null=True)
    is_approved = models.PositiveSmallIntegerField(choices=APPROVE_CHOICE, default=PENDING_APPROVAL, null=True)
    is_active = models.BooleanField(default=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, blank=True, null=True, related_name='refs_tenant_staff')
    # appointment = models.ManyToManyField(Tenant, related_name='refs_tenant_staff')
    qr_image = models.ImageField(upload_to='staffs/qr', null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}-{}'.format(self.name, self.code)

    def save(self, *args, **kwargs):
        if self.code == "":
            code = generate_ref_code2()
            self.code = code
        super().save(*args, **kwargs)


class PhotoValidation(models.Model):
    photo  = models.ImageField(default="", upload_to='validated_photo', blank=True, null=True)
    code = models.CharField(max_length=12, blank=True, unique=True)

    def __str__(self):
        return '{}'.format(self.code)

    def save(self, *args, **kwargs):
        if self.code == "":
            code = generate_ref_code()
            # code = id_generator()
            self.code = code
        super().save(*args, **kwargs)

# class Delivery
