import threading

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ...models import ParentModel, ClaimStatus



APPROVED = "Approved"          # must match your ClaimStatus.status value
SKIP_STATUSES = ["Rejected"]   # existing claims with these statuses are left untouched


class Command(BaseCommand):
    help = "Auto-approve all existing claims whose Manager is Sudha G Rao"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Show what would be approved without saving anything")
        parser.add_argument("--send-emails", action="store_true",
                            help="Also send notification emails (off by default)")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        send_emails = options["send_emails"]

        claims = ParentModel.objects.filter(Manager__iexact="Sudha G Rao")
        # use Manager__istartswith="Sudha G Rao" if the stored name is longer, e.g. "Sudha G Rao K"

        approved_count = 0
        skipped_count = 0

        for claim in claims:
            existing = ClaimStatus.objects.filter(claim=claim).first()

            if existing and (existing.status == APPROVED or existing.status in SKIP_STATUSES):
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would approve: {claim.ClaimNumber}")
                approved_count += 1
                continue

            with transaction.atomic():
                claim_status, _ = ClaimStatus.objects.get_or_create(claim=claim)
                claim_status.approvedby = "Sudha G Rao"
                claim_status.status = APPROVED
                claim_status.comments = "Auto-approved as manager is Sudha G Rao"
                claim_status.save()

                claim.StatusDate = timezone.now().date()
                claim.save()

          

            approved_count += 1
            self.stdout.write(self.style.SUCCESS(f"Approved: {claim.ClaimNumber}"))

        self.stdout.write(self.style.SUCCESS(
            f"Done. Approved: {approved_count}, Skipped: {skipped_count}"
        ))