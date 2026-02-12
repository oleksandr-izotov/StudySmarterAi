from django.core.management.base import BaseCommand
from apps.subscriptions.services import SubscriptionService


class Command(BaseCommand):
    help = 'Initialize default subscription plans'

    def handle(self, *args, **options):
        self.stdout.write('Initializing subscription plans...')
        SubscriptionService.get_or_create_default_plans()
        self.stdout.write(self.style.SUCCESS('Successfully initialized subscription plans'))
