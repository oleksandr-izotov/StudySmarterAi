from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .services import SubscriptionService


@receiver(post_save, sender=User)
def assign_free_plan_on_registration(sender, instance, created, **kwargs):
    if created:
        SubscriptionService.assign_free_plan(instance)
