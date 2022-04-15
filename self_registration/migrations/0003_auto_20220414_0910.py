# Generated by Django 3.2.12 on 2022-04-14 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('self_registration', '0002_alter_visitor_contact_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='qr_image',
            field=models.ImageField(blank=True, null=True, upload_to='staffs/qr'),
        ),
        migrations.AddField(
            model_name='visitor',
            name='qr_image',
            field=models.ImageField(blank=True, null=True, upload_to='visitors/qr'),
        ),
        migrations.AlterField(
            model_name='staff',
            name='is_approved',
            field=models.PositiveSmallIntegerField(choices=[(2, 'Approved'), (1, 'Pending Approval'), (3, 'Not Approved')], default=1, null=True),
        ),
        migrations.AlterField(
            model_name='visitor',
            name='is_approved',
            field=models.PositiveSmallIntegerField(choices=[(2, 'Approved'), (1, 'Pending Approval'), (3, 'Not Approved')], default=2, null=True),
        ),
    ]