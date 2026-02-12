from django.core.management.base import BaseCommand
from apps.prompts.services import AIService

class Command(BaseCommand):
    help = 'Tests the AI integration by sending a simple prompt'

    def handle(self, *args, **options):
        self.stdout.write("Testing AI Integration...")
        
        service = AIService()
        self.stdout.write(f"Configured Providers: {[p.__class__.__name__ for p in service.providers]}")
        
        try:
            self.stdout.write("Sending request 'Tell me a short joke about Python'...")
            response = service.generate("Tell me a short joke about Python")
            self.stdout.write(self.style.SUCCESS(f"Success! Response:\n{response}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed: {e}"))
