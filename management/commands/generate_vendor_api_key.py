from django.core.management.base import BaseCommand

from ...models import VendorAPIKey


class Command(BaseCommand):
    help = "Generate a new vendor API key. The raw key is shown once only — copy it immediately."

    def add_arguments(self, parser):
        parser.add_argument(
            'name', type=str,
            help='Label for this key, e.g. "Acme Vendor - Sandbox"'
        )

    def handle(self, *args, **options):
        raw_key, key_hash = VendorAPIKey.generate_key()
        obj = VendorAPIKey.objects.create(
            name=options['name'],
            key_hash=key_hash,
            prefix=raw_key[:8],
        )
        self.stdout.write(self.style.SUCCESS(f"Created API key '{obj.name}'"))
        self.stdout.write(self.style.WARNING(f"Key (shown only once — copy now): {raw_key}"))
        self.stdout.write("To revoke later: set is_active=False on this VendorAPIKey row in Django admin.")