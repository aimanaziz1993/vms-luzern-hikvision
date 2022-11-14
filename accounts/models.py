from audioop import reverse
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.urls import reverse_lazy


class User(AbstractUser):
    is_administrator = models.BooleanField(default=False)
    is_tenant = models.BooleanField(default=False)

class SecurityOption(models.Model):
    security = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

class Building(models.Model):
    name = models.CharField(max_length=50)
    status = models.BooleanField(default=True)

    def __str__(self):
        return 'Blk. {}'.format(self.name)

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)

class Floor(models.Model):
    name = models.CharField(max_length=50)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)

    def save(self, *args, **kwargs):

        if self.name == '1' or self.name == '2' or self.name == '3' or self.name == '4' or self.name == '5' or self.name == '6' or self.name == '7' or self.name == '8' or self.name == '9':
            self.name = f'#0{self.name}'
        else:
            self.name = f'#{self.name}'
        super().save(*args, **kwargs)
        

    def __str__(self):
        return 'Blk. {} {}'.format(self.building.name, self.name)

class Device(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, unique=True)
    ip_addr = models.GenericIPAddressField(unique=True)
    device_id = models.IntegerField(blank=True, null=True)
    device_ver = models.CharField(max_length=100, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    device_username = models.CharField(max_length=50, default="")
    device_password = models.CharField(max_length=100, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}, ({})'.format(self.floor, self.name)

class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.PROTECT)
    building = models.CharField(max_length=50, null=True, blank=True)
    floor = models.CharField(max_length=50, null=True, blank=True)
    unit_no = models.CharField(max_length=20, null=True, blank=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    registered_address = models.CharField(max_length=100, null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    contact_no = models.CharField(max_length=20, null=True, blank=True)
    code = models.CharField(max_length=12, blank=True, null=True)

    def __str__(self):
        if self.company_name and self.unit_no:
            self.company_name = self.company_name.title()
            return f"{self.company_name}, Blk. {self.building} {self.floor}-{self.unit_no}"
        else:
            return f"Blk. {self.building} {self.floor}-{self.unit_no}"

    def save(self, *args, **kwargs):
        if self.unit_no == '1' or self.unit_no == '2' or self.unit_no == '3' or self.unit_no == '4' or self.unit_no == '5' or self.unit_no == '6' or self.unit_no == '7' or self.unit_no == '8' or self.unit_no == '9':
            self.unit_no = f'0{self.unit_no}'
        else:
            self.unit_no = f'{self.unit_no}'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        userid = self.user.pk
        return reverse_lazy('tenants:tenant-update', kwargs={'pk': userid})
    
    @property
    def generate_url_preview_visitors(self):
        return f"/self-register/visitor/{self.code}/"

    @property
    def generate_url_preview_staffs(self):
        return f"/self-register/staff/{self.code}/"


@receiver(post_delete, sender=Tenant)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user:
        instance.user.delete()
    




