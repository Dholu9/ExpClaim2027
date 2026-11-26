from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.html import format_html
from django.core.mail import send_mail
from django.db.models import Sum
from pytz import timezone as pytz_timezone
from Claim.models import ParentModel, ChildModel, ClaimStatus

class Command(BaseCommand):
    help = 'Send email with approved claims from yesterday, excluding today\'s claims'

    def handle(self, *args, **kwargs):
        # Define the timezone
        kolkata_tz = pytz_timezone('Asia/Kolkata')

        # Get the current time in Asia/Kolkata timezone
        now = timezone.now()  # This is in UTC
        kolkata_now = now.astimezone(kolkata_tz)
        
        # Calculate start and end of yesterday
        yesterday_start = kolkata_now - timezone.timedelta(days=1)
        yesterday_start = yesterday_start.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday_start + timezone.timedelta(days=1)

        # Calculate start of today
        today_start = kolkata_now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Filter claims with yesterday's date and approved status
        parent_claims_yesterday = ParentModel.objects.filter(
            StatusDateAccounts__range=(yesterday_start, yesterday_end)
        ).distinct()

        # Exclude today's claims
        parent_claims_yesterday = parent_claims_yesterday.exclude(
            StatusDateAccounts__gte=today_start
        )

        approved_claims_yesterday = parent_claims_yesterday.filter(
            claimstatus_set__accountstatus='Approved'
        ).distinct()

        if approved_claims_yesterday.exists():
            email_content = '''
            <table class="table table-striped">
                <thead style="background-color:rgb(207, 219, 224);">
                <tr>
                    <th scope="col"></th>
                    <th scope="col">ClaimNumber</th>
                    <th scope="col">DateofApproval</th>
                    <th scope="col">Associate Name</th>
                    <th scope="col">DTNumber</th>   
                    <th scope="col">Department</th>
                    <th scope="col">Manager</th>
                    <th scope="col">ExpenseDetails</th>
                    <th scope="col">TotalClaimAmount</th>
                    <th scope="col">ApprovedAmount</th>
                    <th scope="col">AccountStatus</th>
                    <th scope="col">Payment</th>
                </tr>
                </thead>
                <tbody>
            '''

            for claim in approved_claims_yesterday:
                child_claim = ChildModel.objects.filter(parent=claim).first()
                total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
                
                # Retrieve the approved status based on the related name
                claim_status = claim.claimstatus_set.filter(accountstatus='Approved').first()

                email_content += format_html('''
                <tr style="background-color:rgb(239, 244, 247);">  
                    <td><input type="checkbox" name="selected-claims" value="{}" class="claim-checkbox"></td>  
                    <td><a href="{}">{}</a></td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>        
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                </tr>
                ''',
                claim.ClaimNumber,
                '#',  # Replace with the actual URL or use a URL resolver
                claim.ClaimNumber,
                claim.StatusDateAccounts.strftime('%d-%m-%Y') if claim.StatusDateAccounts else 'N/A',
                claim.user.get_full_name() if claim.user else 'N/A',
                claim.DTNumber,
                claim.Department,
                claim.Manager,
                claim.ExpenseDetails,
                total_claim_amount,
                claim_status.approvedamount if claim_status else 0,
                claim_status.accountstatus if claim_status else 'N/A',
                claim_status.financestatus if claim_status and claim_status.financestatus == 'PaymentDone' else 'Pending'
                )

            total_claim_amount_sum = parent_claims_yesterday.aggregate(total_amount=Sum('child_models__TotalClaimAmount'))['total_amount'] or 0
            approved_amount_sum = approved_claims_yesterday.aggregate(total_approved_amount=Sum('claimstatus_set__approvedamount'))['total_approved_amount'] or 0

            email_content += '''
                </tbody>
                <tfoot>
                  <tr>
                      <td colspan="8" style="text-align: right; font-weight: bold;">Total:</td>
                      <td id="total-claim-amount" style="font-weight: bold;">{}</td>
                      <td id="approved-amount" style="font-weight: bold;">{}</td>
                      <td colspan="1"></td>
                  </tr>
                </tfoot>
            </table>
            '''.format(total_claim_amount_sum, approved_amount_sum)

            # Send the email
            send_mail(
                subject=f'All Claims Approved for {kolkata_now.strftime("%d-%m-%Y")}',
                message='',
                html_message=email_content,
                from_email='expense@deducetech.in',
                recipient_list=['mahima@deducetech.com'],
            )

            self.stdout.write(self.style.SUCCESS('Successfully sent daily email'))
        else:
            self.stdout.write(self.style.WARNING('No claims found for yesterday.'))