from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404

import requests

from .models import Visitor

@receiver(post_save, sender=Visitor, dispatch_uid='notification_visitor_registrations_post_save')
def notification_visitor_registrations_post_save(sender, instance=None, created=None, **kwargs):

    if not created:
        return

    create_message_notifications.delay(instance.id)


def create_message_notifications(message_id):
    visitor = get_object_or_404(Visitor, id=message_id)

    if not visitor:
        return

    