from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.utils.encoding import smart_str
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db import IntegrityError
from django.contrib import messages
from .models import ParentModel,ChildModel,ClaimStatus,UserProfile,Project,Subproject,VendorDetailModel,VendorParentModel,VendorClaimStatus,PODetailModel,POChildModel
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.db.models import Max
from datetime import datetime,timedelta
from datetime import date, timedelta
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Sum
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.template.loader import get_template
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from xhtml2pdf import pisa
import pandas as pd
from io import BytesIO
import json
import os
import io
import csv
import threading


def index(request):
    if request.method == "POST":
        last_name = request.POST.get('last_name')
        last_name = last_name.upper()
        password = request.POST.get('password')
        user = authenticate(request, last_name=last_name, password=password)         

       
        if user is not None:
            login(request, user)

            is_manager = request.user.first_name in ['Mahima Shrivastava', 'Brajesh Shrivastava']
          

            if is_manager:
               
                return redirect('managementview')

            if user.groups.filter(name='Manager').exists():
                return redirect('demo')            
            elif user.groups.filter(name='Management').exists(): 
                return redirect('managementview')
            elif user.groups.filter(name='Accounts').exists(): 
                return redirect('accountsview')            
            elif user.groups.filter(name='Finance').exists(): 
                return redirect('generatereportoptimized')
            else:
                return redirect('entereddata')
        else:
            messages.error(request, 'Error Logging In. Please Try Again.')
            return redirect('index')
    else:
        return render(request, "index.html")
    

def logout_user(request):
    logout(request) 
     
    return redirect('index') 


from django.contrib.auth.models import User, Group
from django.utils import timezone
import pandas as pd

def upload_users(request):
    duplicate_usernames = []

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')

        if excel_file:
            try:
                # Read the Excel file into a DataFrame
                df = pd.read_excel(excel_file)

                # Ensure the required groups exist
                Anil_group, created = Group.objects.get_or_create(name='Anil')
                Siddraju_group, created = Group.objects.get_or_create(name='Siddaraju')

                created_users = []  # To store users for bulk creation later if needed

                for index, row in df.iterrows():
                    # Ensure required columns exist in the row
                    if 'Username' not in row or 'Lead' not in row or 'Email' not in row:
                        continue  # Skip invalid rows

                    # Remove spaces from the "Username" field and merge the words
                    username = ''.join(row['Username'].split())  # Remove spaces and join the words
                    lead = row['Lead']

                    # Check if the username already exists
                    if User.objects.filter(username=username).exists():
                        duplicate_usernames.append(username)
                        continue  # Skip this user if the username already exists

                    # Create the user instance
                    user = User(
                        username=username,
                        first_name=row['Username'],
                        last_name=row.get('DTNumber', ''),  # Use `.get()` to avoid key errors
                        email=row['Email'],
                        is_staff=True,
                        is_active=True,
                        date_joined=timezone.now()
                    )
                    user.set_password(row['Password'])  # Hash the password

                    # Save the user to the database first to get the id
                    user.save()

                    # Assign user to the appropriate group based on the lead
                    if lead == 'Anil Kumar':
                        user.groups.add(Anil_group)
                    elif lead == 'Bharath S R':
                        user.groups.add(Siddraju_group)
                    # No need for `else` if there are no other conditions

                    created_users.append(user)

                # Bulk create users after all have been saved
                # (optional, this can be removed if you only want to create users one by one)
                # User.objects.bulk_create(created_users)

                if duplicate_usernames:
                    return JsonResponse({'success': False, 'duplicates': duplicate_usernames})
                else:
                    return JsonResponse({'success': True, 'count': len(df) - len(duplicate_usernames)})

            except Exception as e:
                return JsonResponse({'success': False, 'message': f"Error processing file: {str(e)}"})

        else:
            return JsonResponse({'success': False, 'message': "No file uploaded."})

    return render(request, 'info.html')


def change_last_name(request):
    if request.method == 'POST':
        old_last_name = request.POST.get('old_last_name')
        new_last_name = request.POST.get('new_last_name')

        # Fetch users with the old last name
        users = User.objects.filter(last_name=old_last_name)
        
        if users.exists():
            users.update(last_name=new_last_name)  # Update last name for all matching users
            return JsonResponse({'success': True, 'message': f"DT Number updated from '{old_last_name}' to '{new_last_name}'"})
        else:
            return JsonResponse({'success': False, 'message': "No users found with the specified DT Number."})

    return JsonResponse({'success': False, 'message': "Invalid request."})



def newclaim(request):
    user=request.user
    first_name = user.first_name
    last_name = user.last_name

    full_name = f"{first_name}" 
    email = user.email

    is_hr = request.user.groups.filter(name='HR').exists()
    is_it = request.user.groups.filter(name='IT').exists()
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_finance = request.user.groups.filter(name='Finance').exists()

    projects = Project.objects.all()
    subprojects = Subproject.objects.all()
    
    return render(request, "userclaims.html",{'full_name': full_name, 'email': email,'last_name':last_name,'projects':projects,'subprojects':subprojects,'is_hr':is_hr,'is_it':is_it,'is_admin':is_admin,"is_finance":is_finance}) 

def addclaim(request):
    
    return render(request, "userclaims.html")  

def claims(request):
    users = User.objects.all()
    user_count_list = []

    for user in users:
        approved_counts = ParentModel.objects.filter(user=user, claimstatus_set__accountstatus='Accepted').count()
        submitted_counts = ParentModel.objects.filter(user=user,claimstatus_set__status='Approved').exclude(claimstatus_set__accountstatus='Accepted').count()
        paymentdue_counts = ParentModel.objects.filter(user=user, claimstatus_set__accountstatus='Accepted').filter(user=user, claimstatus_set__financestatus='').count()

        user_count_list.append({'username': user.username, 'approved_count': approved_counts, 'submitted_count': submitted_counts,'paymentdue_counts': paymentdue_counts})
        
    user_count_list.sort(key=lambda x: x['submitted_count'], reverse=True)

    data = {
        'user_count_list': user_count_list,
    }

    return render(request, "claims.html", data)


def teams(request):
    users = User.objects.all()
    user_count_list = []

    for user in users:
        approved_counts = ParentModel.objects.filter(user=user, claimstatus_set__status='Approved').count()
        submitted_counts = ParentModel.objects.filter(user=user).exclude(claimstatus_set__status='Approved').count()
        accountsrejected = ParentModel.objects.filter(user=user,claimstatus_set__accountstatus='Rejected').count()
     

        user_count_list.append({'username': user.username, 'approved_count': approved_counts, 'submitted_count': submitted_counts, 'accountsrejectedcount':accountsrejected})


    user_count_list.sort(key=lambda x: x['submitted_count'], reverse=True)

    data = {
        'user_count_list': user_count_list,
    }

    return render(request, "teams.html", data)



def associate(request):
    return render(request, "associate.html")  

# @login_required
# def demo(request):
#     allowed_managers = ['Sanjay MS', 'Prabhakara Reddy G V', 'Mahima Shrivastava', 'Brajesh Shrivastava', 'Sudha G Rao', 'Bharath S R']

#     # Check if the user is a manager or Siddraju accessing Prabhakara Reddy G V's page
#     is_manager = request.user.first_name in allowed_managers or (
#         request.user.first_name == 'Bharath S R' and 'Prabhakara Reddy G V' in allowed_managers
#     )

#     if is_manager:
#         parentclaimdata = ParentModel.objects.filter(Manager__in=allowed_managers).order_by('-ClaimNumber').order_by('-claimstatus_set__status')

#         total_claim_amounts = []

#         for claim in parentclaimdata:
#             child_claim = ChildModel.objects.filter(parent=claim).first()
#             total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
#             total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

#         data = {
#             'parentclaimdata': parentclaimdata,
#             'total_claim_amounts': total_claim_amounts,
#             'current_user': request.user.first_name,
#         }

#         return render(request, "info.html", data)
#     else:
#         return HttpResponse("You are not authorized to view this page.")
    

@login_required
def demo(request):
    allowed_managers = ['Accounts','Sanjay MS', 'Prabhakara Reddy G V', 'Mahima Shrivastava', 'Brajesh Shrivastava', 'Sudha G Rao', 'Bharath S R','manager','Vendor','me', 'AmitRathor', 'Anil Kumar', 'ND Mohan Kumar']

    is_manager = request.user.first_name in allowed_managers 
    excluded_claim_numbers = [877, 887, 1097,1118,1120,1156,1157]  
    if is_manager:
        parentclaimdata = ParentModel.objects.all()  

        if request.user.first_name == 'Bharath S R':         
            
            parentclaimdata = parentclaimdata.filter(skipmanager__in=['Bharath S R', 'Anil Kumar']).filter(claimstatus_set__status__isnull=True)

        elif request.user.first_name == 'Anil Kumar':
            parentclaimdata = parentclaimdata.filter(skipmanager__in=['Bharath S R', 'Anil Kumar']).filter(claimstatus_set__status__isnull=True) 
            

        elif request.user.first_name == 'Prabhakara Reddy G V':           

            parentclaimdata = parentclaimdata.filter(Manager=request.user.first_name) \
                                            .filter(claimstatus_set__status__isnull=True) \
                                            .exclude(ClaimNumber__in=excluded_claim_numbers).order_by('-ClaimNumber', '-claimstatus_set__status')
      
        else:        
            parentclaimdata = parentclaimdata.filter(Manager=request.user.first_name) \
                                 .filter(claimstatus_set__status__isnull=True) \
                                 .order_by('-ClaimNumber', '-claimstatus_set__status')  
            # parentclaimdata =  parentclaimdata.filter(ClaimNumber__in=[6614])
            
        total_claim_amounts = []

        skipmanager = None
        for claim in parentclaimdata:
            skipmanager = claim.skipmanager
            child_claim = ChildModel.objects.filter(parent=claim).first()
            total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
            total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

        last_names = User.objects.values_list('last_name', flat=True).distinct()
        uploaded_files = ExcelFile.objects.all().order_by('-file_date', '-uploaded_at')

        

        data = {
            'parentclaimdata': parentclaimdata,
            'total_claim_amounts': total_claim_amounts,
            'current_user': request.user.first_name,
            'last_names':list(last_names),
            'skipmanager':skipmanager,
            'uploaded_files': uploaded_files,
        }

        return render(request, "info.html", data)
    else:
        return HttpResponse("You are not authorized to view this page.")


   
@login_required
def democustom(request):    
    
    parentclaimdata = ParentModel.objects.filter(Manager=request.user.first_name).order_by('-ClaimNumber').order_by('-claimstatus_set__status')

    total_claim_amounts = []

    for claim in parentclaimdata:
        child_claim = ChildModel.objects.filter(parent=claim).first()
        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

    data = {
        'parentclaimdata': parentclaimdata,
        'total_claim_amounts': total_claim_amounts,
    }


    return render(request, "infocustom.html", data)
    




def generate_pdf(html_content):
    response = HttpResponse(content_type='application/pdf')
    filename = "claims.pdf"
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(smart_str(filename))

    # Specify the page size and orientation (landscape)
    pdf = pisa.CreatePDF(
        html_content,  # HTML content to convert to PDF
        dest=response,
        pagesize="A4 landscape",  # Specify the desired page size and orientation
    )

    

    if not pdf.err:
        return response
    else:
        return HttpResponse("PDF generation error: %s" % pdf.err)

import time

def get_filtered_claims(data):
    year = data.get('year')
    month = data.get('month')
    start = data.get('startdate')
    end = data.get('enddate')
    project = data.get('project_name')
    user_id = (data.get('user_id') or '').strip()
    user_name = (data.get('user_name') or '').strip()

    qs = (ParentModel.objects
          .select_related('user')
          .prefetch_related('claimstatus_set'))

    if start and end:
        qs = qs.filter(StatusDate__date__range=(start, end))
    else:
        if year:
            qs = qs.filter(StatusDate__year=year)
        if month:
            qs = qs.filter(StatusDate__month=month)

    if project:
        qs = qs.filter(Project=project)

    if user_id:
        # A suggestion was actually picked -> exact, unambiguous match
        qs = qs.filter(user_id=user_id)
    elif user_name:
        # User typed a name but never picked a suggestion -> best-effort match
        qs = qs.filter(
            Q(user__first_name__icontains=user_name) |
            Q(user__last_name__icontains=user_name)
        )

    return qs

# def generate_excel(request):
#     if request.method == 'POST':
#         try:
#             selected_claims_data = json.loads(request.body.decode('utf-8'))

#             # Extract the selected claims data and create a DataFrame
#             df = pd.DataFrame(selected_claims_data['selectedClaims'])

#             # Get the current timestamp
#             current_timestamp = int(time.time())

#             # Create a formatted date string from the timestamp
#             date_string = time.strftime("%Y%m%d_%H%M%S", time.gmtime(current_timestamp))

#             # Combine date and claim numbers for the filename
#             filename = f'selected_claims_{date_string}.xlsx'

#             # Create an in-memory output file
#             output = BytesIO()

#             # Use the ExcelWriter to write the DataFrame to the BytesIO object
#             with pd.ExcelWriter(output, engine='openpyxl') as writer:
#                 df.to_excel(writer, index=False)

#             # Create the HTTP response with the Excel file
#             response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#             response['Content-Disposition'] = f'attachment; filename={filename}'

#             return response

#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'error': 'Invalid JSON data'})

#     return JsonResponse({'success': False, 'error': 'Invalid request method'})



def selected_claims_view(request):
    try:
        if request.method == 'POST':
            selected_claim_numbers = request.POST.get('selected-claims', '').split(',')
            selected_claim_numbers = [claim_number for claim_number in selected_claim_numbers if claim_number.isdigit()]

            print('selected_claim_numbers:', selected_claim_numbers)

            # Update the 'accountselect' field for selected claims in the ClaimStatus model
            ClaimStatus.objects.filter(claim__ClaimNumber__in=selected_claim_numbers).update(accountselect="Selected")

            selected_claims = ParentModel.objects.filter(ClaimNumber__in=selected_claim_numbers)
            print('selected claims:', selected_claims)

            total_claim_amounts = []
            for claim in selected_claims:
                child_claim = ChildModel.objects.filter(parent=claim).first()
                total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
                total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

            context = {
                'selected_claims': selected_claims,
                'total_claim_amounts': total_claim_amounts,
            }

            template_path = 'viewreport.html'
            template = get_template(template_path)
            html = template.render(context)

            return generate_excel(selected_claims)
    except AttributeError as e:
        print(f"Ignoring AttributeError: {e}")
        # Handle the exception as needed, e.g., log it or return an error response

    return redirect('generatereport')



def managementview(request):
    # Filter claims based on account status and order by status and ClaimNumber
    singleclaims = ParentModel.objects.filter(
        claimstatus_set__managementstatus=''
    ).order_by('-claimstatus_set__status', '-ClaimNumber')

    claim_number = request.GET.get('ClaimNumber')
    if claim_number:
        singleclaims = singleclaims.exclude(ClaimNumber=claim_number)

    claims_to_display = singleclaims

    total_claim_amounts = []


    for claim in claims_to_display:
        child_claim = ChildModel.objects.filter(parent=claim).first()
        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

    data = {
        'singleclaims': singleclaims,
        'claims_to_display': claims_to_display,
        'total_claim_amounts': total_claim_amounts,
    }

    return render(request, "managementview.html", data)



@login_required
def managementreview(request, ClaimNumber):

    claim = get_object_or_404(ParentModel, ClaimNumber=ClaimNumber)
    user = claim.user 
    first_name = user.first_name
    last_name = user.last_name

    if request.method == 'POST':
        managementcomments = request.POST.get('managementcomments')        
        managementstatus = request.POST.get('managementstatus')
        claim_status, created = ClaimStatus.objects.get_or_create(claim=claim)           
        claim_status.managementstatus = managementstatus
        claim_status.managementcomments = managementcomments
        claim_status.save()

        to_email= ['sudha@deducetech.com']

        sendmailmanagement(to_email, ClaimNumber, managementstatus,managementcomments)

        return redirect('managementview')

    childclaimdata = ChildModel.objects.filter(parent=claim)    
    total_claim_amount = childclaimdata.first().TotalClaimAmount    
    accountscomments = claim.claimstatus_set.values_list('accountscomments', flat=True).first()
    is_custom3 = claim.claimstatus_set.filter(managementstatus='Approved').exists()

   
    data = {
        
        'parentclaimdata': claim,
        'childclaimdata': childclaimdata,
        'total_claim_amount':total_claim_amount,
        'accountscomments':accountscomments,
        'first_name':first_name,
        'last_name':last_name,
        'is_custom3':is_custom3,

    }
    return render(request, "managementreview.html", data)

@login_required
def approvedclaims(request):
    user_count_list = []
    approvedclaims = ParentModel.objects.filter(claimstatus_set__managementstatus='Approved')
    
    claim_number = request.GET.get('ClaimNumber')
    if claim_number:
        selectedclaims = selectedclaims.exclude(ClaimNumber=claim_number)
    
    total_claim_amounts = []

    for claim in approvedclaims:     
        child_claim = ChildModel.objects.filter(parent=claim).first()
        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

    user_count_list.append({'approvedclaims': approvedclaims, 'total_claim_amounts': total_claim_amounts})

    data = {
        'approvedclaims': approvedclaims,
        'total_claim_amounts': total_claim_amounts,
    }

    return render(request, "approvedclaims.html", data)



@login_required
def approvedclaimsaccounts(request):

    user_count_list = []
    parentclaimdata = []

    try:
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=30)

        # Same-row conditions on ClaimStatus must be in ONE filter() call,
        # otherwise Django may match them against different related rows.
        parentclaimdata = (
            ParentModel.objects
            .filter(
                StatusDate__date__range=(start_date, end_date),
                claimstatus_set__status='Approved',
                claimstatus_set__accountstatus='Approved',
            )
            .select_related("user")
            .prefetch_related(
                Prefetch("claimstatus_set", queryset=ClaimStatus.objects.order_by("-id")),
                "child_models",
            )
            .distinct()  # the join on claimstatus_set can produce duplicates
            .order_by("-ClaimNumber")
        )

        # Attach computed values using prefetched data (no extra queries per claim)
        for claim in parentclaimdata:
            statuses = list(claim.claimstatus_set.all())  # already ordered by -id

            claim.total_claim_amount = sum(
                (child.TotalClaimAmount or 0) for child in claim.child_models.all()
            )

            claim.approvedby = next(
                (s.approvedby for s in statuses if s.status == "Approved" and s.approvedby),
                "N/A",
            )

            claim.current_status = statuses[0] if statuses else None

    except Exception as e:
        print(f"An error occurred: {e}")

    last_names = User.objects.values_list('last_name', flat=True).distinct()

    data = {
        'user_count_list': user_count_list,
        'parentclaimdata': parentclaimdata,
        'last_names': list(last_names),
    }

    return render(request, "approvedclaimsaccounts.html", data)



@login_required
def approvedclaimsmanager(request):
    user_count_list = []
    user = request.user
    first_name = user.first_name

    if first_name == 'Anil Kumar':   
        approvedclaims = ParentModel.objects.filter(
          
            claimstatus_set__approvedby=first_name,  # Filter by the current user's first name
           
        ).order_by('-ClaimNumber')
    elif first_name == 'Bharath S R':
        approvedclaims = ParentModel.objects.filter(
            
            claimstatus_set__approvedby=first_name,  # Filter by the current user's first name
           
        ).order_by('-ClaimNumber')

        # approvedclaims = ParentModel.objects.filter(
        #     claimstatus_set__status='Approved').filter( # Filter by Approved status
        #     Q(skipmanager=first_name) | Q(skipmanager='')  # This is an OR condition
        #         ).order_by('-ClaimNumber')
    else:
        approvedclaims = ParentModel.objects.filter(
            claimstatus_set__status='Approved',  # Use claimstatus_set for related name
            claimstatus_set__approvedby=first_name,  # Filter by the current user's first name
           
        ).order_by('-ClaimNumber')

    total_claim_amounts = []

    for claim in approvedclaims:     
        child_claim = ChildModel.objects.filter(parent=claim).first()
        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

    user_count_list.append({'approvedclaims': approvedclaims, 'total_claim_amounts': total_claim_amounts})

    data = {
        'approvedclaims': approvedclaims,
        'total_claim_amounts': total_claim_amounts,
    }

    return render(request, "approvedclaimsmanager.html", data)

@login_required
def rejectedclaimsmanager(request):
    user_count_list = []
    user = request.user
    first_name = user.first_name

    if first_name == 'Anil Kumar':   
        rejectedclaims = ParentModel.objects.filter(
            claimstatus_set__status='Rejected',  # Use claimstatus_set for related name
            claimstatus_set__approvedby=first_name,  # Filter by the current user's first name           
        ).order_by('-ClaimNumber')
    elif first_name == 'Bharath S R':   
        rejectedclaims = ParentModel.objects.filter(
            claimstatus_set__status='Rejected',  # Use claimstatus_set for related name           
        ).order_by('-ClaimNumber')
    elif first_name == 'Sudha G Rao':
        rejectedclaims = ParentModel.objects.filter(
            claimstatus_set__status='Rejected',  # Use claimstatus_set for related name
                       
        ).order_by('-ClaimNumber')
    else:
        rejectedclaims = ParentModel.objects.filter(
            claimstatus_set__status='Rejected',  # Use claimstatus_set for related name
            claimstatus_set__approvedby=first_name,  # Filter by the current user's first name           
        ).order_by('-ClaimNumber')

    total_claim_amounts = []

    for claim in rejectedclaims:     
        child_claim = ChildModel.objects.filter(parent=claim).first()
        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

    user_count_list.append({'rejectedclaims': rejectedclaims, 'total_claim_amounts': total_claim_amounts})

    data = {
        'rejectedclaims': rejectedclaims,
        'total_claim_amounts': total_claim_amounts,
    }

    return render(request, "rejectedclaimsmanager.html", data)


# def generatereport(request):
#     user_count_list = []
#     approvedclaims = ParentModel.objects.filter(claimstatus_set__status='Approved')
#     print(approvedclaims)
#     total_claim_amounts = []
#     parentclaimdata = ParentModel.objects.filter(claimstatus_set__status='Approved').order_by('-ClaimNumber').order_by('claimstatus_set__status', 'claimstatus_set__accountstatus')
#     for claim in approvedclaims:
#         StatusDate = claim.StatusDate
#         child_claim = ChildModel.objects.filter(parent=claim).first()
#         total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
#         total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))
    
#     try:
#         user_count_list.append({'approvedclaims': approvedclaims,'StatusDate':StatusDate})
#         print(user_count_list)
#     except:
#         StatusDate=None


#     data = {
#         'user_count_list': user_count_list,
#         'parentclaimdata':parentclaimdata,
#         'StatusDate':StatusDate,
#         'total_claim_amounts':total_claim_amounts,
#     }
#     return render(request, "generatereport.html",data)




def demo2(request, ClaimNumber):
    user=request.user
    parentclaimdata = ParentModel.objects.filter(user=user,ClaimNumber=ClaimNumber).order_by('-ClaimNumber')

    data = {
        'user': user,
        'parentclaimdata': parentclaimdata
    }
    return render(request, "info.html", data)


@login_required
def entereddata(request):
    user = request.user

    parentclaimdata = (
        ParentModel.objects
        .filter(user=user)
        .select_related('user')
        .prefetch_related(
            Prefetch(
                'claimstatus_set',
                queryset=ClaimStatus.objects.order_by('pk'),
                to_attr='status_list',
            )
        )
        .order_by('-ClaimNumber')
    )

    # Attach the claim's ClaimStatus row (or None) so the template can use n.latest_status
    for claim in parentclaimdata:
        claim.latest_status = claim.status_list[0] if claim.status_list else None

    data = {
        'user': user,
        'parentclaimdata': parentclaimdata,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    return render(request, "dataentered.html", data)



@login_required
def entereddata2(request, ClaimNumber):

    parentclaimdata = ParentModel.objects.get(ClaimNumber=ClaimNumber)

    user = parentclaimdata.user 
    first_name = user.first_name
    last_name = user.last_name

    childclaimdata = ChildModel.objects.filter(parent=parentclaimdata)
    is_custom = parentclaimdata.claimstatus_set.filter(status='Approved').exists()
    
    total_claim_amount = childclaimdata.first().TotalClaimAmount    
    accountscomments = parentclaimdata.claimstatus_set.values_list('accountscomments', flat=True).first()
    paymentcomments = parentclaimdata.claimstatus_set.values_list('financecomments', flat=True).first()
    commentskip = parentclaimdata.claimstatus_set.values_list('commentskip', flat=True).first()

    excel_file_url = None
    excel_file_name = None
    if parentclaimdata.excelfile:
        excel_file_url = parentclaimdata.excelfile.url
        excel_file_name = os.path.basename(parentclaimdata.excelfile.name)

   
    data = {
        
        'parentclaimdata': parentclaimdata,
        'childclaimdata': childclaimdata,
        'total_claim_amount':total_claim_amount,
        'accountscomments':accountscomments,
        'paymentcomments':paymentcomments,
        'first_name':first_name,
        'last_name':last_name,
        'is_custom':is_custom,
        'commentskip':commentskip,
        'excel_file_url':excel_file_url,
        'excel_file_name':excel_file_name

    }
    return render(request, "dataentered2.html", data)

@login_required
def entereddatacustom(request, ClaimNumber):

    parentclaimdata = ParentModel.objects.get(ClaimNumber=ClaimNumber) 

    user = parentclaimdata.user 
    first_name = user.first_name
    last_name = user.last_name

    childclaimdata = ChildModel.objects.filter(parent=parentclaimdata)
    
    total_claim_amount = childclaimdata.first().TotalClaimAmount    
    accountscomments = parentclaimdata.claimstatus_set.values_list('accountscomments', flat=True).first()
    paymentcomments = parentclaimdata.claimstatus_set.values_list('financecomments', flat=True).first()
    is_custom = parentclaimdata.claimstatus_set.filter(status='Approved').exists()

   
    data = {
        
        'parentclaimdata': parentclaimdata,
        'childclaimdata': childclaimdata,
        'total_claim_amount':total_claim_amount,
        'accountscomments':accountscomments,
        'paymentcomments':paymentcomments,
        'first_name':first_name,
        'last_name':last_name,
        'is_custom':is_custom,


    }
    return render(request, "dataenteredcustom.html", data)

import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render


@login_required
def entereddata3(request, ClaimNumber):
    parentclaimdata = get_object_or_404(ParentModel, ClaimNumber=ClaimNumber)
    childclaimdata = ChildModel.objects.filter(parent=parentclaimdata)

    first_child = childclaimdata.first()
    total_claim_amount = first_child.TotalClaimAmount if first_child else 0

    statuses = parentclaimdata.claimstatus_set.all()

    managementcomments = statuses.values_list('managementcomments', flat=True).first()
    comments = statuses.values_list('comments', flat=True).first()

    management_row = statuses.filter(managementstatus='Approved').first()
    managementstatus = management_row.managementstatus if management_row else None

    # Latest accounts review row (used to prefill the form)
    saved_review = (
        statuses
        .filter(accountstatus='Approved')
        .order_by('-id')
        .first()
    )
    already_reviewed = saved_review is not None
    is_custom2 = already_reviewed  # kept for backward compatibility with the template

    excel_file_url = None
    excel_file_name = None
    if parentclaimdata.excelfile:
        excel_file_url = parentclaimdata.excelfile.url
        excel_file_name = os.path.basename(parentclaimdata.excelfile.name)

    user = parentclaimdata.user
    first_name = user.first_name
    last_name = user.last_name

    data = {
        'parentclaimdata': parentclaimdata,
        'childclaimdata': childclaimdata,
        'total_claim_amount': total_claim_amount,
        'first_name': first_name,
        'last_name': last_name,
        'managementcomments': managementcomments,
        'comments': comments,
        'managementstatus': managementstatus,
        'is_custom2': is_custom2,
        'saved_review': saved_review,          # new
        'already_reviewed': already_reviewed,  # new
        'excel_file_url': excel_file_url,
        'excel_file_name': excel_file_name,
    }
    return render(request, "accountsshow.html", data)


@login_required
def entereddata4(request, ClaimNumber):
   
    parentclaimdata = ParentModel.objects.get(ClaimNumber=ClaimNumber)
    childclaimdata = ChildModel.objects.filter(parent=parentclaimdata)
    total_claim_amount = childclaimdata.first().TotalClaimAmount
    managementcomments = parentclaimdata.claimstatus_set.values_list('managementcomments', flat=True).first() 
    claim_status_objects = parentclaimdata.claimstatus_set.filter(managementstatus='Approved')
    is_custom2 = parentclaimdata.claimstatus_set.filter(accountstatus='Approved').exists()
    if claim_status_objects.exists():
        managementstatus = claim_status_objects.first().managementstatus
       
    else:
        managementstatus = None
  
    user = parentclaimdata.user 
    first_name = user.first_name
    last_name = user.last_name

   
    data = {
        
        'parentclaimdata': parentclaimdata,
        'childclaimdata': childclaimdata,
        'total_claim_amount':total_claim_amount,
        'first_name':first_name,
        'last_name':last_name,
        'managementcomments':managementcomments,
        'managementstatus':managementstatus,
        'is_custom2':is_custom2,
    }
    return render(request, "financeshow.html", data)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import transaction, IntegrityError
from django.db.models import Max
from django.core.files.storage import default_storage
from django.contrib import messages
from datetime import datetime

from decimal import Decimal, InvalidOperation

# (keep your existing imports: transaction, IntegrityError, JsonResponse, messages,
#  redirect, render, Max, timezone, datetime, threading, default_storage,
#  ValidationError, login_required, models, helpers, etc.)


def parse_amount(value, row_no):
    """Convert a posted amount to Decimal. Raises ValueError (never silently returns 0)."""
    value = (value or "").strip()
    if not value:
        raise ValueError(f"Row {row_no}: claim amount is required.")
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"Row {row_no}: '{value}' is not a valid amount.")
    if amount <= 0:
        raise ValueError(f"Row {row_no}: claim amount must be greater than 0.")
    return amount.quantize(Decimal("0.01"))


def parse_date(value, row_no, label):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Row {row_no}: invalid {label} date.")


@login_required
def saverecord(request):

    # -------- GET request --------
    if request.method != "POST":
        ClaimNumber = (ParentModel.objects.aggregate(max_claim=Max('ClaimNumber'))['max_claim'] or 100) + 1
        context = {
            'ClaimNumber': ClaimNumber,
            'ClaimAmounts': [],
            'Remarks': [],
            'file_names': [],
        }
        return render(request, "dataentered.html", context)

    # -------- POST: Excel validation --------
    excelfile = request.FILES.get('excelfile')
    if not excelfile:
        return JsonResponse({'error': 'Excel file is required'}, status=400)
    try:
        validate_excel_file(excelfile)
    except ValidationError as e:
        return JsonResponse({'error': e.message}, status=400)

    user = request.user
    auto_approved = False
    saved_files = []  # track files so they can be cleaned up if the transaction fails

    try:
        # -------- Read child rows first and validate BEFORE touching the DB --------
        ReceiptNumbers = request.POST.getlist('ReceiptNumber')
        ReceiptDates = request.POST.getlist('ReceiptDate')
        ReceiptDates1 = request.POST.getlist('ReceiptDate1')
        ExpenseHeads = request.POST.getlist('ExpenseHead')
        ClaimAmounts = request.POST.getlist('ClaimAmounts')
        Remarks = request.POST.getlist('Remarks')
        BillAttachments = request.FILES.getlist('BillAttachment')

        # Row 0 is the hidden template row in the form, so skip it.
        # Real rows start at index 1; their files are BillAttachments[0], [1], ...
        rows = []
        for i in range(1, len(ReceiptNumbers)):
            row_no = i  # human-friendly row number

            amount = parse_amount(ClaimAmounts[i] if i < len(ClaimAmounts) else "", row_no)
            from_date = parse_date(ReceiptDates[i] if i < len(ReceiptDates) else "", row_no, "From")
            to_date = parse_date(ReceiptDates1[i] if i < len(ReceiptDates1) else "", row_no, "To")

            if from_date and to_date and from_date > to_date:
                raise ValueError(f'Row {row_no}: "From" date cannot be later than "To" date.')

            rows.append({
                'ReceiptNumber': ReceiptNumbers[i],
                'ReceiptDate': from_date or datetime.now().date(),
                'ReceiptDate1': to_date or from_date or datetime.now().date(),
                'ExpenseHead': ExpenseHeads[i] if i < len(ExpenseHeads) else '',
                'ClaimAmount': amount,
                'Remarks': Remarks[i] if i < len(Remarks) else '',
                'file': BillAttachments[i - 1] if (i - 1) < len(BillAttachments) else None,
            })

        if not rows:
            raise ValueError("Please add at least one claim row.")

        # Total is calculated on the server, never trusted from the browser
        TotalClaimAmount = sum((r['ClaimAmount'] for r in rows), Decimal("0.00"))

        with transaction.atomic():

            # -------- Generate ClaimNumber safely --------
            last = ParentModel.objects.select_for_update().order_by('-ClaimNumber').first()
            ClaimNumber = (last.ClaimNumber if last else 100) + 1

            # -------- Basic Details --------
            DateofCreation = request.POST.get('DateofCreation') or timezone.now().date()
            Department = request.POST.get('Department')
            ExpenseDetails = request.POST.get('ExpenseDetails')

            # -------- Manager Logic --------
            if user.groups.filter(name='Anil').exists():
                Manager = "Anil Kumar"
                skipmanager = "Anil Kumar"
            elif user.groups.filter(name='Siddraju').exists():
                Manager = "Bharath S R"
                skipmanager = "Bharath S R"
            else:
                Manager = request.POST.get('Manager')
                skipmanager = ""

            # -------- Project Logic --------
            if user.groups.filter(name='IT').exists():
                Project1, Subproject1 = 'IT', ''
            elif user.groups.filter(name='HR').exists():
                Project1, Subproject1 = 'HR', ''
            elif user.groups.filter(name='Admin').exists():
                Project1, Subproject1 = 'Admin', ''
            elif user.groups.filter(name='Finance').exists():
                Project1, Subproject1 = 'Finance', ''
            else:
                project = Project.objects.get(id=request.POST.get('Project'))
                Project1 = project.project_title
                Subproject1 = request.POST.get('Subproject')

            # -------- Save Parent --------
            en1 = ParentModel.objects.create(
                user=user,
                ClaimNumber=ClaimNumber,
                DTNumber=user.last_name,
                DateofCreation=DateofCreation,
                Department=Department,
                Manager=Manager,
                skipmanager=skipmanager,
                ExpenseDetails=ExpenseDetails,
                Project=Project1,
                Subproject=Subproject1,
                excelfile=excelfile,
                # If your ParentModel has a total field, store it here too:
                # TotalClaimAmount=TotalClaimAmount,
            )
            parent_id = en1.id

            # -------- Auto-approve if manager is Sudha --------
            auto_approved = (Manager or "").strip() == "Sudha G Rao"
            if auto_approved:
                ClaimStatus.objects.update_or_create(
                    claim=en1,
                    defaults={
                        "approvedby": "Sudha G Rao",
                        "status": "Approved",
                        "comments": "Auto-approved as manager is Sudha G Rao",
                    },
                )
                en1.StatusDate = timezone.now().date()
                en1.save()

            # -------- Save child rows --------
            for r in rows:
                file_name = None
                if r['file']:
                    file_name = default_storage.save(r['file'].name, r['file'])
                    saved_files.append(file_name)

                ChildModel.objects.create(
                    parent_id=parent_id,
                    ReceiptNumber=r['ReceiptNumber'],
                    ReceiptDate=r['ReceiptDate'],
                    ReceiptDate1=r['ReceiptDate1'],   # requires this field on ChildModel
                    BillAttachment=file_name,
                    ExpenseHead=r['ExpenseHead'],
                    ClaimAmount=r['ClaimAmount'],      # ClaimAmount should be a DecimalField
                    TotalClaimAmount=TotalClaimAmount,  # TotalClaimAmount should be a DecimalField
                    Remarks=r['Remarks'],
                )

            # -------- Send approval email only after DB commit succeeds --------
            if auto_approved and user.email != 'prabhakara@deducetech.com':
                transaction.on_commit(lambda: threading.Thread(
                    target=send_email_in_background,
                    args=([user.email], ClaimNumber, "Approved", user,
                          "Auto-approved as manager is Sudha"),
                ).start())

        if auto_approved:
            messages.success(request, "Claim submitted and auto-approved!")
        else:
            messages.success(request, "Claim submitted successfully!")
        return redirect('entereddata')

    except ValueError as e:
        # Validation problems (bad amount, bad dates, no rows)
        for f in saved_files:
            default_storage.delete(f)
        messages.error(request, str(e))
        return redirect('entereddata')

    except IntegrityError:
        for f in saved_files:
            default_storage.delete(f)
        messages.error(request, "Duplicate ClaimNumber detected. Please try again.")
        return redirect('entereddata')



import os

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

# from .models import ParentModel, ClaimStatus, Project

EXCEL_ALLOWED_EXTENSIONS = {'.xls', '.xlsx', '.xlsm', '.csv'}
EXCEL_MAX_SIZE = 5 * 1024 * 1024  # 5MB


def validate_excel_file(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in EXCEL_ALLOWED_EXTENSIONS:
        raise ValidationError("Receipt Details must be an Excel/CSV file (.xls, .xlsx, .xlsm, .csv).")
    if f.size > EXCEL_MAX_SIZE:
        raise ValidationError("Excel file is too large (max 5MB).")


@login_required
@require_POST
def create_claim_parent(request):
    # -------- Excel file --------
    excelfile = request.FILES.get('excelfile')
    if not excelfile:
        return JsonResponse({'error': 'Excel file is required'}, status=400)
    try:
        validate_excel_file(excelfile)
    except ValidationError as e:
        return JsonResponse({'error': e.message}, status=400)

    user = request.user

    try:
        with transaction.atomic():
            last = ParentModel.objects.select_for_update().order_by('-ClaimNumber').first()
            ClaimNumber = (last.ClaimNumber if last else 100) + 1

            # JS sends '' when there is no DateofCreation field, so fall back to today
            DateofCreation = request.POST.get('DateofCreation') or timezone.now().date()
            Department = request.POST.get('Department')
            ExpenseDetails = request.POST.get('ExpenseDetails')

            # -------- Manager logic --------
            if user.groups.filter(name='Anil').exists():
                Manager = "Anil Kumar"
                skipmanager = "Anil Kumar"
            elif user.groups.filter(name='Siddraju').exists():
                Manager = "Bharath S R"
                skipmanager = "Bharath S R"
            else:
                Manager = request.POST.get('Manager')
                skipmanager = ""

            # -------- Project logic --------
            if user.groups.filter(name='IT').exists():
                Project1, Subproject1 = 'IT', ''
            elif user.groups.filter(name='HR').exists():
                Project1, Subproject1 = 'HR', ''
            elif user.groups.filter(name='Admin').exists():
                Project1, Subproject1 = 'Admin', ''
            elif user.groups.filter(name='Finance').exists():
                Project1, Subproject1 = 'Finance', ''
            else:
                project = Project.objects.get(id=request.POST.get('Project'))
                Project1 = project.project_title
                Subproject1 = request.POST.get('Subproject') or ''

            # -------- Save parent (file goes to MEDIA_ROOT/<upload_to>, path goes in DB) --------
            en1 = ParentModel.objects.create(
                user=user,
                ClaimNumber=ClaimNumber,
                DTNumber=user.last_name,
                DateofCreation=DateofCreation,
                Department=Department,
                Manager=Manager,
                skipmanager=skipmanager,
                ExpenseDetails=ExpenseDetails,
                Project=Project1,
                Subproject=Subproject1,
                excelfile=excelfile,
            )

            # -------- Auto-approve --------
            if (Manager or "").strip() == "Sudha G Rao":
                ClaimStatus.objects.update_or_create(
                    claim=en1,
                    defaults={
                        "approvedby": "Sudha G Rao",
                        "status": "Approved",
                        "comments": "Auto-approved as manager is Sudha G Rao",
                    },
                )
                en1.StatusDate = timezone.now().date()
                en1.save()

        return JsonResponse({'parent_id': en1.id, 'excelfile': en1.excelfile.name})

    except IntegrityError:
        return JsonResponse({'error': 'Duplicate ClaimNumber. Please try again.'}, status=409)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def add_claim_receipt(request):
    """
    Step 2 of the async submission flow — called once PER receipt row.
    Each call handles exactly one file, so no single request has to
    carry the full upload weight of the whole claim. If one receipt
    fails, only that one needs retrying, not the entire submission.
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST required'}, status=405)

    parent_id = request.POST.get('parent_id')
    if not parent_id:
        return JsonResponse({'error': 'parent_id required'}, status=400)

    ReceiptNumber = request.POST.get('ReceiptNumber')
    ReceiptDate   = request.POST.get('ReceiptDate')
    ReceiptDate1  = request.POST.get('ReceiptDate1')          # ← NEW
    ExpenseHead   = request.POST.get('ExpenseHead')
    ClaimAmount   = request.POST.get('ClaimAmount')
    Remark        = request.POST.get('Remarks')
    TotalClaimAmount_str = request.POST.get('TotalClaimAmount')
    bill_attachment = request.FILES.get('BillAttachment')

    file_name = None
    if bill_attachment:
        file_name = default_storage.save(bill_attachment.name, bill_attachment)

    if ReceiptDate:
        ReceiptDate = datetime.strptime(ReceiptDate, '%Y-%m-%d').date()
    else:
        ReceiptDate = datetime.now().date()

    if ReceiptDate1:                                          # ← NEW
        ReceiptDate1 = datetime.strptime(ReceiptDate1, '%Y-%m-%d').date()
    else:
        ReceiptDate1 = None                                   # ← NEW

    try:
        ClaimAmount = int(ClaimAmount)
    except (TypeError, ValueError):
        ClaimAmount = 0

    TotalClaimAmount = int(float(TotalClaimAmount_str)) if TotalClaimAmount_str else None

    ChildModel.objects.create(
        parent_id=parent_id,
        ReceiptNumber=ReceiptNumber,
        ReceiptDate=ReceiptDate,
        ReceiptDate1=ReceiptDate1,                            # ← NEW
        BillAttachment=file_name,
        ExpenseHead=ExpenseHead,
        ClaimAmount=ClaimAmount,
        TotalClaimAmount=TotalClaimAmount,
        Remarks=Remark
    )

    return JsonResponse({'status': 'ok'})

























def replace_bill_attachment(request, child_claim_id):
    child_claim = get_object_or_404(ChildModel, id=child_claim_id)
    ClaimNumber = request.GET.get('ClaimNumber')

    if request.method == 'POST' and 'new_bill_attachment' in request.FILES:
        # Delete the existing attachment
        if child_claim.BillAttachment:
            default_storage.delete(child_claim.BillAttachment.name)
            child_claim.BillAttachment.delete()

        # Save the new attachment
        new_bill_attachment = request.FILES['new_bill_attachment']
        child_claim.BillAttachment = new_bill_attachment
        child_claim.save()

        return redirect('showclaim', ClaimNumber=child_claim.parent.ClaimNumber)

    return render(request, 'replace_bill_attachment.html', {'child_claim': child_claim})

def delete_child_form(request, child_claim_id):
    child_claim = get_object_or_404(ChildModel, id=child_claim_id)
    try:
       
        ChildModel.objects.filter(id=child_claim_id).delete()

        
        return redirect('showclaim', ClaimNumber=child_claim.parent.ClaimNumber)
    except Exception as e:
        # Return an error response
        return JsonResponse({'error': f'Error: {e}'}, status=500)


EXCEL_ALLOWED_EXTENSIONS = {'.xls', '.xlsx', '.xlsm', '.csv'}
EXCEL_MAX_SIZE = 5 * 1024 * 1024  # 5MB
EXCEL_DEFAULT_NAME = 'default.xlsx'  # the model's default; never delete this one


def validate_excel_file(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in EXCEL_ALLOWED_EXTENSIONS:
        raise ValidationError("Receipt Details must be an Excel/CSV file (.xls, .xlsx, .xlsm, .csv).")
    if f.size > EXCEL_MAX_SIZE:
        raise ValidationError("Excel file is too large (max 5MB).")


def updaterecord(request, ClaimNumber):
    user = request.user
    try:
        claim = get_object_or_404(ParentModel, ClaimNumber=ClaimNumber)

        if request.method == "POST":

            # -------- Excel file (optional on edit: only if a new one was chosen) --------
            new_excel = request.FILES.get('excelfile')
            if new_excel:
                try:
                    validate_excel_file(new_excel)
                except ValidationError as e:
                    error_message = e.message
                    error_message += '<br><br><a href="javascript:history.go(-1)">Go Back</a>'
                    return HttpResponse(error_message, status=400)

            month_mapping = {
                'Jan.': 'January', 'Feb.': 'February', 'Mar.': 'March',
                'Apr.': 'April', 'May.': 'May', 'Jun.': 'June',
                'Jul.': 'July', 'Aug.': 'August', 'Sep.': 'September',
                'Oct.': 'October', 'Nov.': 'November', 'Dec.': 'December',
            }

            raw_date = request.POST.get('DateofCreation') or ''
            for abbreviated, full in month_mapping.items():
                raw_date = raw_date.replace(abbreviated, full)

            try:
                DateofCreation = datetime.strptime(raw_date, '%B %d, %Y').date()
            except ValueError:
                DateofCreation = None

            Department = request.POST.get('Department')
            Manager = request.POST.get('Manager')
            ExpenseDetails = request.POST.get('ExpenseDetails')

            if request.user.groups.filter(name='IT').exists():
                project, subproject = 'IT', ''
            elif request.user.groups.filter(name='HR').exists():
                project, subproject = 'HR', ''
            elif request.user.groups.filter(name='Admin').exists():
                project, subproject = 'Admin', ''
            elif request.user.groups.filter(name='Finance').exists():
                project, subproject = 'Finance', ''
            else:
                project = request.POST.get('Project')
                subproject = request.POST.get('Subproject')

            claim.DateofCreation = DateofCreation
            claim.ExpenseDetails = ExpenseDetails
            claim.Department = Department
            claim.Manager = Manager
            claim.Project = project
            claim.Subproject = subproject

            # -------- Replace the Excel file --------
            old_excel_name = claim.excelfile.name if claim.excelfile else None
            if new_excel:
                claim.excelfile = new_excel   # saved to MEDIA on claim.save(), path stored in DB

            claim.save()

            # delete the OLD file from disk only after the new one is saved
            if new_excel and old_excel_name \
                    and old_excel_name != claim.excelfile.name \
                    and os.path.basename(old_excel_name) != EXCEL_DEFAULT_NAME:
                try:
                    default_storage.delete(old_excel_name)
                except Exception:
                    pass  # an undeletable old file must not break the update

            # -------- Update existing child rows --------
            ReceiptNumbers  = request.POST.getlist('ReceiptNumber')
            ReceiptDates    = request.POST.getlist('ReceiptDate')
            ReceiptDates1   = request.POST.getlist('ReceiptDate1')
            ExpenseHeads    = request.POST.getlist('ExpenseHead')
            ClaimAmounts    = request.POST.getlist('ClaimAmount')
            Remarks         = request.POST.getlist('Remarks')
            TotalClaimAmount = request.POST.get('TotalClaimAmount')

            childclaims = ChildModel.objects.filter(parent=claim).order_by('id')

            for i, childclaim in enumerate(childclaims):
                if i < len(ReceiptNumbers):
                    ReceiptNumber = ReceiptNumbers[i]
                    ReceiptDate_str  = ReceiptDates[i]  if i < len(ReceiptDates)  else ''
                    ReceiptDate1_str = ReceiptDates1[i] if i < len(ReceiptDates1) else ''
                    ExpenseHead = ExpenseHeads[i] if i < len(ExpenseHeads) else ''
                    ClaimAmount = ClaimAmounts[i] if i < len(ClaimAmounts) else '0'
                    Remark = Remarks[i] if i < len(Remarks) else ''

                    try:
                        ReceiptDate = datetime.strptime(ReceiptDate_str, '%Y-%m-%d').date() if ReceiptDate_str else None
                    except ValueError:
                        ReceiptDate = None

                    try:
                        ReceiptDate1 = datetime.strptime(ReceiptDate1_str, '%Y-%m-%d').date() if ReceiptDate1_str else None
                    except ValueError:
                        ReceiptDate1 = None

                    childclaim.ReceiptNumber = ReceiptNumber
                    childclaim.ReceiptDate    = ReceiptDate
                    childclaim.ReceiptDate1   = ReceiptDate1
                    childclaim.ExpenseHead    = ExpenseHead
                    childclaim.ClaimAmount    = ClaimAmount
                    childclaim.Remarks        = Remark
                    childclaim.TotalClaimAmount = TotalClaimAmount
                    childclaim.save()

            # -------- Add new child rows --------
            ReceiptNumbersNew  = request.POST.getlist('ReceiptNumberNew')
            ReceiptDatesNew    = request.POST.getlist('ReceiptDateNew')
            ReceiptDatesNew1   = request.POST.getlist('ReceiptDateNew1')
            ExpenseHeadsNew    = request.POST.getlist('ExpenseHeadNew')
            ClaimAmountsNew    = request.POST.getlist('ClaimAmountNew')
            RemarksNew         = request.POST.getlist('RemarksNew')
            BillAttachmentsNew = request.FILES.getlist('BillAttachmentNew')

            if BillAttachmentsNew:
                BillAttachmentsNew.insert(0, '')

            file_names = []

            for idx, ReceiptNumberNew in enumerate(ReceiptNumbersNew):
                if not ReceiptNumberNew:
                    continue

                ReceiptDateNew_str  = ReceiptDatesNew[idx]  if idx < len(ReceiptDatesNew)  else ''
                ReceiptDateNew1_str = ReceiptDatesNew1[idx] if idx < len(ReceiptDatesNew1) else ''
                ExpenseHeadNew      = ExpenseHeadsNew[idx]  if idx < len(ExpenseHeadsNew)  else ''
                ClaimAmountNew      = ClaimAmountsNew[idx]  if idx < len(ClaimAmountsNew)  else '0'
                RemarksNew_val      = RemarksNew[idx]       if idx < len(RemarksNew)       else ''
                BillAttachmentNew   = BillAttachmentsNew[idx] if idx < len(BillAttachmentsNew) else None

                if BillAttachmentNew:
                    file_name = default_storage.save(BillAttachmentNew.name, BillAttachmentNew)
                else:
                    file_name = None
                file_names.append(file_name)

                try:
                    ReceiptDateNew = datetime.strptime(ReceiptDateNew_str, '%Y-%m-%d').date() if ReceiptDateNew_str else None
                except ValueError:
                    ReceiptDateNew = None

                try:
                    ReceiptDateNew1 = datetime.strptime(ReceiptDateNew1_str, '%Y-%m-%d').date() if ReceiptDateNew1_str else None
                except ValueError:
                    ReceiptDateNew1 = None

                ChildModel.objects.create(
                    parent=claim,
                    ReceiptNumber=ReceiptNumberNew,
                    ReceiptDate=ReceiptDateNew,
                    ReceiptDate1=ReceiptDateNew1,
                    ExpenseHead=ExpenseHeadNew,
                    ClaimAmount=ClaimAmountNew,
                    Remarks=RemarksNew_val,
                    BillAttachment=file_name,
                )

            # -------- Update claim status --------
            claim_status, created = ClaimStatus.objects.get_or_create(claim=claim)
            if user.groups.filter(name='Anil').exists() or user.groups.filter(name='Siddraju').exists():
                claim_status.tlstatus = "ReSubmitted"
            else:
                claim_status.status = "ReSubmitted"
            claim_status.save()

            return redirect('entereddata')

        # GET fallback
        context = {
            'ClaimNumber': ClaimNumber,
            'ClaimAmounts': [],
            'Remarks': [],
        }
        messages.success(request, "Claim submitted successfully!")
        return render(request, "dataentered.html", context)

    except IntegrityError:
        error_message = "Error: Please Change ReceiptNumber"
        error_message += '<br><br><a href="javascript:history.go(-1)">Go Back</a>'
        return HttpResponse(error_message, status=400)
    

def showclaim(request, ClaimNumber):
    user = request.user
    first_name = user.first_name
    last_name = user.last_name
    parentclaimdata = get_object_or_404(ParentModel, user=user, ClaimNumber=ClaimNumber)
    childclaimdata = ChildModel.objects.filter(parent=parentclaimdata)    

    if childclaimdata.exists():
        total_claim_amount = childclaimdata.first().TotalClaimAmount
    else:
        total_claim_amount = None

    if user.groups.filter(name='Anil').exists() or user.groups.filter(name='Siddraju').exists():   
        is_rejected = parentclaimdata.claimstatus_set.filter(tlstatus='Rejected').exists()
    else:
        is_rejected = parentclaimdata.claimstatus_set.filter(status='Rejected').exists()

    bill_attachments = [child.BillAttachment.name for child in childclaimdata]  
    comments = parentclaimdata.claimstatus_set.values_list('comments', flat=True).first()
    skipcomments = parentclaimdata.claimstatus_set.values_list('commentskip', flat=True).first()

    is_hr = request.user.groups.filter(name='HR').exists()
    is_it = request.user.groups.filter(name='IT').exists()
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_finance = request.user.groups.filter(name='Finance').exists()

    projects = Project.objects.all()
    subprojects = Subproject.objects.all()
    selectedproject = parentclaimdata.Project    
    selectedsubproject = parentclaimdata.Subproject
   
    
    data = {
        'user': user,
        'ClaimNumber': ClaimNumber,       
        'parentclaimdata': parentclaimdata,
        'childclaimdata': childclaimdata,
        'is_rejected': is_rejected,
        'bill_attachments': bill_attachments,
        'total_claim_amount': total_claim_amount,
        'comments': comments,
        'skipcomments':skipcomments,
        'first_name':first_name,
        'last_name':last_name,
        'selectedproject':selectedproject,
        'selectedsubproject':selectedsubproject,
        'projects':projects,
        'subprojects':subprojects,
        'is_hr':is_hr,
        'is_it':is_it,
        'is_admin':is_admin,
        'is_finance':is_finance
    }    
    return render(request, "savedform.html", data)


def send_email_in_background(to_email, claim_number, status, user, comments):
    # Send email to the user
    sendmailuser(to_email, claim_number, status, user, comments)
    
    # Send email to the account
    account_email = ['sudha@deducetech.com']
    sendmailaccounts(account_email, claim_number, status, user, comments)

@login_required
def review_claim(request, ClaimNumber):
    claim = get_object_or_404(ParentModel, ClaimNumber=ClaimNumber)
    childclaimdata = ChildModel.objects.filter(parent=claim)

    if request.method == 'POST':   
        new_status = request.POST.get('status')                                                                     
        comments = request.POST.get('comments', '')  
        user = request.user
        first_name = user.first_name
    
        if first_name in ["Anil Kumar", "Bharath S R"]:
            claim.Manager = "Prabhakara Reddy G V"
            claim.save()     
        claim_status, created = ClaimStatus.objects.get_or_create(claim=claim)

        claim_status.approvedby = first_name
        claim_status.comments = comments
        claim_status.status = new_status
        
        claim_status.save()

        # Update status date
        claim.StatusDate = timezone.now().date()
        claim.save()

      
        user_email = [claim.user.email]
      
        if 'prabhakara@deducetech.com' in user_email:        
            return redirect('demo')

        # Create a thread for sending emails to both user and account
        email_thread = threading.Thread(target=send_email_in_background, 
                                        args=(user_email, ClaimNumber, new_status, claim.user, comments))
        email_thread.start()

        return redirect('demo')

    context = {
        'parentclaimdata': claim,
        'childclaimdata': childclaimdata,
        'current_user': request.user.first_name,
    }

    return render(request, "teams.html", context)

def sendmailuser(to_email, claim_number, status,user,comments):
    claim = get_object_or_404(ParentModel, ClaimNumber=claim_number)
    subject = f'Claim {status} - Claim Number: {claim_number}'
  

    message = render_to_string('email.html', {'claim': claim, 'status':status,'claim_number':claim_number,'user':user,'comments':comments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass

def sendmailaccounts(to_email, claim_number, status,user,comments):
    claim = get_object_or_404(ParentModel, ClaimNumber=claim_number)
    subject = f'Claim {status} - Claim Number: {claim_number}'  

    message = render_to_string('emailtosudha.html', {'claim': claim, 'status':status,'claim_number':claim_number,'user':user,'comments':comments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass

def sendmailpayment(to_email, claim_number, new_financestatus, paymentcomments,user):
    claim = get_object_or_404(ParentModel, ClaimNumber=claim_number)
    subject = f'Claim {new_financestatus} - Claim Number: {claim_number}'
  

    message = render_to_string('emailpayment.html', {'claim': claim, 'new_financestatus':new_financestatus,'claim_number':claim_number,'user':user,'paymentcomments':paymentcomments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass  


def send_approval_rejection_email(to_email, claim_number, new_accountstatus,accountscomments):
    claim = get_object_or_404(ParentModel, ClaimNumber=claim_number)
    subject = f'Claim {new_accountstatus} - Claim Number: {claim_number}'
    manager_name = claim.Manager

    message = render_to_string('emailmanager.html', {'claim': claim, 'new_accountstatus':new_accountstatus,'manager_name':manager_name,'claim_number':claim_number,'accountscomments':accountscomments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:       
        pass 

def send_mail_mahima(to_email2, claim_number, new_accountstatus,accountscomments):
    claim = get_object_or_404(ParentModel, ClaimNumber=claim_number)
    subject = f'Claim {new_accountstatus} - Claim Number: {claim_number}'
   

    message = render_to_string('emailtomahima.html', {'claim': claim, 'new_accountstatus':new_accountstatus,'claim_number':claim_number,'accountscomments':accountscomments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email2:
        send_mail(subject, plain_message, from_email, to_email2, html_message=message)
    else:       
        pass 


def sendmailmanagement(to_email, claim_number, managementstatus,managementcomments):
    claim = get_object_or_404(ParentModel, ClaimNumber=claim_number)
    subject = f'Claim {managementstatus} - Claim Number: {claim_number}'
    

    message = render_to_string('emailaccounts.html', {'claim': claim, 'managementstatus':managementstatus,'claim_number':claim_number,'managementcomments':managementcomments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass 


def sendmailvendormanager(to_email, claim_number, financestatus,financecomments):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=claim_number)
    subject = f'Claim {financestatus} - Claim Number: {claim_number}'
    

    message = render_to_string('sendmailvendormanager.html', {'claim': claim, 'financestatus':financestatus,'claim_number':claim_number,'financecomments':financecomments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'



    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass 


def sendmailvendorfinance(to_email, claim_number):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=claim_number)
    subject = f'Claim Submitted - Claim Number: {claim_number}'    

    message = render_to_string('sendmailvendorfinance.html', {'claim': claim,'claim_number':claim_number})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass 

from django.shortcuts import render
from django.db.models import Q, Sum
from .models import ParentModel, ChildModel, ClaimStatus
from django.contrib.auth.models import User

@login_required
def accountsview(request):

    monthdata = ParentModel.objects.none()
    selected_month = None
    selected_year = None
    selected_project = None
    user_count_list = []
    StatusDate = None

    # Claims that are Approved by the approver but not yet reviewed by accounts
    # (accountstatus blank) or Rejected by accounts.
    approvedclaims = (
            ClaimStatus.objects
            .filter(status='Approved', accountstatus='')
            .values_list('claim_id', flat=True)
            .distinct()
        )

    if request.method == 'POST':
        # Filter button pressed: use the submitted filters.
        selected_month   = request.POST.get('month')
        selected_year    = request.POST.get('year')
        selected_project = request.POST.get('project_name')

        try:
            if selected_month:
                selected_month = int(selected_month)
            if selected_year:
                selected_year = int(selected_year)

            monthdata = build_claim_queryset(request.POST)

        except ValueError as e:
            print(f"Value error: {e}")
            selected_month = None
            selected_year = None
            monthdata = ParentModel.objects.none()
        except Exception as e:
            print(f"Error in filtering: {e}")
            monthdata = ParentModel.objects.none()
    else:
        # First time the page opens: show the pending claims (same rule as above).
        try:
            monthdata = (
                ParentModel.objects
                .filter(id__in=approvedclaims)
                .order_by('-ClaimNumber')
            )
        except Exception as e:
            print(f"Error loading initial claims: {e}")
            monthdata = ParentModel.objects.none()

    total_claim_amounts = []
    projects = Project.objects.all()
    subprojects = Subproject.objects.all()

    # Build user_count_list from the data being shown (monthdata)
    for claim in monthdata:
        StatusDate = claim.StatusDate
        child_claim = ChildModel.objects.filter(parent=claim).first()

        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

        user_count_list.append({
            'approvedclaim': claim,
            'StatusDate': StatusDate,
            'total_claim_amount': total_claim_amount
        })

    dt_numbers = (
        User.objects
        .exclude(last_name="")
        .values_list("last_name", flat=True)
        .distinct()
    )
    uploaded_files = ExcelFile.objects.all().order_by('-file_date', '-uploaded_at')

    context = {
        'monthdata': monthdata,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_project': selected_project,
        'user_count_list': user_count_list,
        'parentclaimdata': approvedclaims,
        'StatusDate': StatusDate,
        'total_claim_amounts': total_claim_amounts,
        'projects': projects,
        'subprojects': subprojects,
        "dt_numbers": dt_numbers,
        'uploaded_files': uploaded_files,
    }

    return render(request, "accountsview.html", context)


@login_required
def accountsviewrejected(request):

    monthdata = ParentModel.objects.none()
    selected_month = None
    selected_year = None
    selected_project = None
    user_count_list = []
    StatusDate = None

    # Claims that are Approved by the approver but not yet reviewed by accounts
    # (accountstatus blank) or Rejected by accounts.
    approvedclaims = (
            ClaimStatus.objects
            .filter(accountstatus='Rejected')           
            .distinct()
            .order_by('-id')
        )

   
   

    context = {
        'monthdata': monthdata,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_project': selected_project,
        'user_count_list': user_count_list,
        'parentclaimdata': approvedclaims,
        'StatusDate': StatusDate,
     
    }

    return render(request, "rejectedclaimsaccounts.html", context)



from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone


def _to_decimal(value):
    try:
        return Decimal(value) if value not in (None, '') else Decimal('0')
    except InvalidOperation:
        return None


from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

# from .models import ParentModel, ChildModel, ClaimStatus   # keep your existing imports


def _to_decimal(value, label=None):
    """
    Convert a form value to Decimal.

    - Blank / missing  -> Decimal('0')
    - Invalid / NaN / Infinity -> None
    `label` is optional so existing calls with or without it both work.
    """
    if value is None or str(value).strip() == '':
        return Decimal('0')
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not result.is_finite():
        return None
    return result


@login_required
def accountsreview(request, ClaimNumber):
    parentclaimdata = get_object_or_404(ParentModel, ClaimNumber=ClaimNumber)

    if request.method != 'POST':
        return redirect('accountsview')

    accountstatus = request.POST.get('accountstatus', '').strip()
    accountscomments = request.POST.get('accountscomments', '').strip()
    hold = _to_decimal(request.POST.get('holdamounthr'), 'Hold amount')
    reject = _to_decimal(request.POST.get('rejectamounthr'), 'Rejected amount')
    advance = _to_decimal(request.POST.get('advancededuct'), 'Advance deduct')

    if accountstatus != 'Approved' or not accountscomments:
        messages.error(request, "Status and comments are required.")
        return redirect('entereddata3', ClaimNumber=ClaimNumber)

    if (
        hold is None or reject is None or advance is None
        or hold < 0 or reject < 0 or advance < 0
    ):
        messages.error(
            request,
            "Hold, rejected and advance deduct amounts must be valid, non-negative numbers."
        )
        return redirect('entereddata3', ClaimNumber=ClaimNumber)

    # Same total your detail page shows (first child row)
    first_child = ChildModel.objects.filter(parent=parentclaimdata).first()
    total_claim_amount = (first_child.TotalClaimAmount if first_child else None) or Decimal('0')

    if hold + reject + advance > total_claim_amount:
        messages.error(
            request,
            "Hold + Rejected + Advance Deduct cannot exceed the Total Claim Amount."
        )
        return redirect('entereddata3', ClaimNumber=ClaimNumber)

    # Recalculate on the server; don't trust the readonly field from the browser
    approvedamount = total_claim_amount - hold - reject - advance

    with transaction.atomic():
        statuses = parentclaimdata.claimstatus_set.select_for_update()

        # Update the existing row: the manager-approved one the claim was listed under
        status_row = (
            statuses.filter(status='Approved').order_by('-id').first()
            or statuses.order_by('-id').first()
        )

        if status_row is None:
            status_row = ClaimStatus(claim=parentclaimdata)

        status_row.accountstatus = accountstatus
        status_row.accountscomments = accountscomments
        status_row.holdamounthr = hold
        status_row.rejectamounthr = reject
        status_row.advancededuct = advance
        status_row.approvedamount = approvedamount

        # If nothing is on hold or rejected, it goes straight through to finance
        if hold == 0 and reject == 0 and advance == 0:
            status_row.financestatus = 'Approved'
            status_row.payableamount = approvedamount
        else:
            # Hold/reject exist, so finance has to review it
            status_row.financestatus = ''
            status_row.payableamount = None

        status_row.save()

        # NOTE: parentclaimdata.StatusDateAccounts is intentionally NOT updated here.

    messages.success(request, f"Claim {ClaimNumber} updated.")
    return redirect('approvedclaimsaccounts')

@login_required
def update_expense_head(request, ClaimNumber):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

    try:
        data = json.loads(request.body)
        child_id = data.get("child_id")
        expensehead = (data.get("expensehead") or "").strip()

        if not expensehead:
            return JsonResponse({"status": "error", "message": "Expense Head cannot be empty."}, status=400)

        # The bill row must belong to THIS claim, so no other claim's row can be edited
        child = get_object_or_404(ChildModel, pk=child_id, parent__ClaimNumber=ClaimNumber)

        max_len = getattr(ChildModel._meta.get_field("ExpenseHead"), "max_length", None)
        if max_len and len(expensehead) > max_len:
            return JsonResponse(
                {"status": "error", "message": f"Maximum {max_len} characters allowed."},
                status=400,
            )

        child.ExpenseHead = expensehead
        child.save(update_fields=["ExpenseHead"])   # only this field is touched

        return JsonResponse({"status": "success", "expensehead": child.ExpenseHead})

    except Http404:
        return JsonResponse({"status": "error", "message": "Bill row not found for this claim."}, status=404)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    

@login_required
def update_expense_details(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

    try:
        data = json.loads(request.body)
        claim_number = str(data.get("claim_number", "")).strip()
        expensedetails = (data.get("expensedetails") or "").strip()

        if not claim_number:
            return JsonResponse({"status": "error", "message": "Claim number missing."}, status=400)
        if not expensedetails:
            return JsonResponse({"status": "error", "message": "Expense details cannot be empty."}, status=400)

        claim = get_object_or_404(ParentModel, ClaimNumber=claim_number)

        max_len = getattr(ParentModel._meta.get_field("ExpenseDetails"), "max_length", None)
        if max_len and len(expensedetails) > max_len:
            return JsonResponse(
                {"status": "error", "message": f"Maximum {max_len} characters allowed."},
                status=400,
            )

        claim.ExpenseDetails = expensedetails
        claim.save(update_fields=["ExpenseDetails"])   # only this column is touched

        return JsonResponse({"status": "success", "expensedetails": claim.ExpenseDetails})

    except Http404:
        return JsonResponse({"status": "error", "message": "Claim not found."}, status=404)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# from .models import ParentModel, ChildModel, Project, Subproject


@login_required
def generatereportfinaceview(request):
    monthdata = ParentModel.objects.none()
    selected_month = None
    selected_year = None
    selected_project = None
    selected_user_id = None
    selected_user_name = None
    start_date = None
    end_date = None

    try:
        if request.method == 'POST':
            selected_month = request.POST.get('month') or None
            selected_year = request.POST.get('year') or None
            selected_project = request.POST.get('project_name') or None
            selected_user_id = request.POST.get('user_id') or None
            selected_user_name = request.POST.get('user_name') or None
            start_date = request.POST.get('startdate') or None
            end_date = request.POST.get('enddate') or None

            # Convert year/month to integers
            if selected_year:
                selected_year = int(selected_year)

            if selected_month:
                selected_month = int(selected_month)

       

            qs = (
                ParentModel.objects
                .filter(claimstatus_set__accountstatus='Approved')
                .distinct()
            )

            # ---------------------------------------------------------
            # DATE RANGE
            # ---------------------------------------------------------

            if start_date and end_date:
                start_date_obj = datetime.strptime(
                    start_date,
                    '%Y-%m-%d'
                ).date()
                end_date_obj = datetime.strptime(
                    end_date,
                    '%Y-%m-%d'
                ).date()
                qs = qs.filter(
                    StatusDate__date__range=(
                        start_date_obj,
                        end_date_obj
                    )
                )

            else:
                # -----------------------------------------------------
                # YEAR
                # -----------------------------------------------------
                if selected_year:
                    qs = qs.filter(
                        StatusDate__year=selected_year
                    )
                # -----------------------------------------------------
                # MONTH
                # -----------------------------------------------------
                if selected_month:
                    qs = qs.filter(
                        StatusDate__month=selected_month
                    )
            # ---------------------------------------------------------
            # PROJECT
            # ---------------------------------------------------------

            if selected_project:
                qs = qs.filter(
                    Project=selected_project
                )

            # ---------------------------------------------------------
            # NAME / USER
            # ---------------------------------------------------------

            if selected_user_id:
                qs = qs.filter(
                    user_id=selected_user_id
                )

            elif selected_user_name:
                qs = qs.filter(
                    user__first_name__icontains=selected_user_name
                )

            # ---------------------------------------------------------
            # FINAL QUERY
            # ---------------------------------------------------------

            monthdata = (
                qs
                .order_by('-ClaimNumber')
            )

        # =============================================================
        # ADD FIRST CHILD AMOUNT TO EACH CLAIM
        # =============================================================

        claims = list(monthdata)

        child_amounts = {}

        if claims:

            children = (
                ChildModel.objects
                .filter(parent__in=claims)
                .order_by('id')
            )

            for child in children:

                if child.parent_id not in child_amounts:
                    child_amounts[child.parent_id] = (
                        child.TotalClaimAmount
                    )

        # Attach amount to each claim
        for claim in claims:

            claim.total_claim_amount = child_amounts.get(
                claim.pk,
                0
            )

        # =============================================================
        # CONTEXT
        # =============================================================

        context = {

            'monthdata': claims,

            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_project': selected_project,

            'selected_user_id': selected_user_id,
            'selected_user_name': selected_user_name,

            'start_date': start_date,
            'end_date': end_date,

            'projects': Project.objects.all(),
            'subprojects': Subproject.objects.all(),
        }

        return render(
            request,
            'financeview.html',
            context
        )

    except (ValueError, TypeError) as e:

        print(f"Filter error: {e}")

        context = {
            'monthdata': [],
            'selected_month': None,
            'selected_year': None,
            'selected_project': None,
            'selected_user_id': None,
            'selected_user_name': None,
            'start_date': None,
            'end_date': None,
            'projects': Project.objects.all(),
            'subprojects': Subproject.objects.all(),
        }

        return render(
            request,
            'financeview.html',
            context
        )

    except Exception as e:

        print(f"General error: {e}")

        context = {
            'monthdata': [],
            'selected_month': None,
            'selected_year': None,
            'selected_project': None,
            'selected_user_id': None,
            'selected_user_name': None,
            'start_date': None,
            'end_date': None,
            'projects': Project.objects.all(),
            'subprojects': Subproject.objects.all(),
        }

        return render(
            request,
            'financeview.html',
            context
        )

# Add to the imports at the top of views.py if not already there:
#   from datetime import timedelta
#   from django.utils import timezone


def financeview(request):
    user_count_list = []
    total_claim_amounts = []
    StatusDate = None
    parentclaimdata = ParentModel.objects.none()

    try:
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=45)

        # ONLY approved + last 30 days.
        # Both claimstatus_set conditions are in ONE filter() call so they apply
        # to the same ClaimStatus row. distinct() removes duplicate parents
        # created by the join.
        base_qs = (
            ParentModel.objects
            .filter(
                StatusDate__date__range=(start_date, end_date),
                claimstatus_set__status='Approved',
                claimstatus_set__accountstatus='Approved',
            )
            .select_related("user")
            .prefetch_related("claimstatus_set", "child_models", "splits")
            .distinct()
            .order_by('-ClaimNumber')
        )

        approvedclaims = base_qs
        parentclaimdata = base_qs

        for claim in approvedclaims:
            StatusDate = claim.StatusDate
            children = sorted(claim.child_models.all(), key=lambda c: c.pk)
            child_claim = children[0] if children else None
            total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
            total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

        user_count_list.append({'approvedclaims': approvedclaims, 'StatusDate': StatusDate})

    except Exception as e:
        print(f"An error occurred: {e}")
        StatusDate = None

    data = {
        'user_count_list': user_count_list,
        'parentclaimdata': parentclaimdata,
        'StatusDate': StatusDate,
        'total_claim_amounts': total_claim_amounts,
    }

    return render(request, "financeview.html", data)


from django.views.decorators.csrf import csrf_exempt

from .api_auth import require_api_key


import json
from datetime import datetime

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .api_auth import require_api_key


@csrf_exempt
@require_api_key
def financeview_api(request):
    """
    POST /financeview-api/
    Body (JSON): {"date": "2026-08-01"}

    Returns every approved claim whose ApprovedDt (StatusDate) matches
    the given date, with all the fields the financeview page (and the
    download_excel_latest report) shows:

      - Parent columns (Emp ID, Claim No, Emp Name, Department, Manager,
        Project, Sub Project, Details, Claim Date, Reviewer, Total Claim
        Amount, bank details)
      - HR columns (Hold/Rejected/Approved amounts, HR remarks, HR status,
        Verified by / on)
      - Finance columns (Hold/Release/Rejected/Payable/Paid, Finance
        status, Paid on) — from ClaimStatus at the claim level
      - Children[] — one entry per ChildModel row
      - Splits[]   — one entry per ClaimSplit row
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if request.method != "POST":
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    date_str = payload.get('date') or payload.get('ApprovedDt')
    if not date_str:
        return JsonResponse(
            {'error': "'date' is required in the JSON payload, format YYYY-MM-DD"},
            status=400,
        )

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse(
            {'error': "Invalid date format — expected YYYY-MM-DD"},
            status=400,
        )

    claims = (
        ParentModel.objects
        .filter(claimstatus_set__accountstatus='Approved', StatusDate=target_date)
        .select_related('user')
        .prefetch_related('claimstatus_set', 'child_models', 'splits')
        .order_by('-ClaimNumber')
    )

    # ---- helpers ----
    def _num(val, default=0):
        if val is None:
            return default
        try:
            return round(float(val), 2)
        except (TypeError, ValueError):
            return default

    def _dt(val, fmt='%Y-%m-%d'):
        if not val:
            return None
        try:
            return val.strftime(fmt)
        except Exception:
            return str(val)

    def _dur(d1, d2):
        """Mirror the Excel view's fmt_duration: 'dd-mm-YYYY - dd-mm-YYYY'."""
        left  = _dt(d1, '%d-%m-%Y') if d1 else "—"
        right = _dt(d2, '%d-%m-%Y') if d2 else "—"
        if left == "—" and right == "—":
            return ""
        return f"{left} - {right}"

    def _month(dt):
        return _dt(dt, '%b-%Y') or ""

    def _profile_bank(user):
        """Safely read bank fields off the user's profile (may not exist)."""
        prof = getattr(user, 'userprofileb', None) if user else None
        if prof is None:
            return None, None, None, None
        return (
            getattr(prof, 'bankname',      None),
            getattr(prof, 'accountnumber', None),
            getattr(prof, 'ifsccode',      None),
            getattr(prof, 'nameasperbank', None),
        )

    def _reviewer_from_approvedby(approvedby):
        """Split 'First Last' from approvedby; look up User by name for DT No."""
        if not approvedby:
            return "", ""
        reviewer_name = str(approvedby).strip()
        reviewer_dt   = ""
        parts = reviewer_name.split()
        if len(parts) >= 2:
            u_first = parts[0]
            u_last  = " ".join(parts[1:])
            match = (
                User.objects
                .filter(first_name__iexact=u_first, last_name__iexact=u_last)
                .order_by("id")
                .first()
            )
            if match:
                reviewer_dt = match.last_name or ""
        return reviewer_name, reviewer_dt

    results = []
    for sl_no, claim in enumerate(claims, start=1):
        user    = getattr(claim, 'user', None)
        profile = getattr(user, 'userprofileb', None) if user else None

        statuses = list(claim.claimstatus_set.all().order_by('id'))
        children = list(claim.child_models.all().order_by('id'))
        splits   = list(claim.splits.all().order_by('pk'))
        status   = statuses[0] if statuses else None

        # ---- Reviewer (mirrors Excel logic) ----
        reviewer_name, reviewer_dt = _reviewer_from_approvedby(
            status.approvedby if status else None
        )

        # ---- Total Claim Amount = sum of children's ClaimAmount ----
        total_claim_amount = sum(
            (getattr(c, 'ClaimAmount', 0) or 0) for c in children if c is not None
        )
        if not total_claim_amount and statuses:
            total_claim_amount = sum(
                (getattr(s, 'approvedamount', 0) or 0) for s in statuses
            )

        # ---- Bank fields ----
        bank_name, acct_no, ifsc, beneficiary = _profile_bank(user)

        # ---- HR / finance fields from ClaimStatus ----
        hr_status          = status.accountstatus    if status else 'Pending'
        hr_hold            = status.holdamounthr     if status else None
        hr_rejected        = status.rejectamounthr   if status else None
        hr_approved        = status.approvedamount   if status else None
        hr_remarks         = status.accountscomments if status else None

        finance_status     = (status.financestatus  if status else None) or 'Pending'
        finance_remarks    = status.financecomments if status else None
        hold_fin           = status.holdamountfin   if status else None
        release_hold       = status.releasehold     if status else None
        rejected_fin       = status.rejectamountfin if status else None
        payable_amount     = status.payableamount   if status else None
        paid_amt           = status.paid            if status else None
        paid_on            = status.paidon          if status else None

        nature_of_expense  = (status.NatureOfExpense    if status else None) or claim.NatureOfExpense
        accounting_loc     = (status.AccountingLocation if status else None) or claim.AccountingLocation

        # ---- Children[] (mirrors apply_child_fields) ----
        child_items = []
        for ch in children:
            month_src = ch.ReceiptDate or claim.DateofCreation
            child_items.append({
                'id':               ch.id,
                'Item':             ch.ExpenseHead,
                'ClaimPeriod':      _dur(ch.ReceiptDate, ch.ReceiptDate1),
                'ClaimedForMonth':  _month(month_src),
                'ReceiptNumber':    ch.ReceiptNumber,
                'ReceiptDate':      _dt(ch.ReceiptDate),
                'ReceiptDate1':     _dt(ch.ReceiptDate1),
                'ClaimAmount':      _num(ch.ClaimAmount),
                'TotalClaimAmount': _num(ch.TotalClaimAmount),
                'Remarks':          ch.Remarks,
                'BillAttachment':   ch.BillAttachment.url if ch.BillAttachment else None,
                'CreatedAt':        _dt(ch.created_at, '%Y-%m-%d %H:%M'),
            })

        # ---- Splits[] (mirrors apply_split_fields) ----
        split_items = []
        for sp in splits:
            split_items.append({
                'id':                 sp.pk,
                'HoldAmountFinance':  _num(sp.holdamountfin),
                'HoldReleaseAmount':  _num(sp.releasehold),
                'RejectedAmount':     _num(sp.rejectamountfin),
                'FinanceRemarks':     sp.financecomments,
                'FinanceStatus':      sp.financestatus,
                'PayableAmount':      _num(sp.payableamount),
                'Paid':               _num(sp.paid),
                'PaidOn':             _dt(sp.paidon),
                'NatureOfExpense':    sp.NatureOfExpense,
                'AccountingLocation': sp.AccountingLocation,
                'CreatedOn':          _dt(sp.created_on),
            })

        results.append({
            # ---- Identity / parent ----
            'SlNo':                  sl_no,
            'EmpID':                 claim.DTNumber,
            'ClaimNo':               claim.ClaimNumber,
            'EmpName':               user.first_name if user else None,
            'Department':            claim.Department,
            'Manager':               claim.Manager,
            'Project':               claim.Project,
            'SubProject':            claim.Subproject,
            'Details':               claim.ExpenseDetails,
            'ClaimDate':             _dt(claim.DateofCreation),
            'ClaimStatus':           status.status if status else None,
            'ReviewerName':          reviewer_name,
            'ReviewerDTNo':          reviewer_dt,
            'AppliedAcceptedDate':   _dt(claim.StatusDate),
            'DateofSubmission':      _dt(claim.DateofSubmission),

            # ---- Amounts / HR ----
            'TotalClaimAmount':      _num(total_claim_amount),
            'HoldAmountHR':          _num(hr_hold),
            'RejectedAmountHR':      _num(hr_rejected),
            'ApprovedAmount':        _num(hr_approved),
            'AdvanceForDeduction':   None,
            'FinalApprovedAmount':   _num(hr_approved),
            'HRRemarks':             hr_remarks,
            'HRStatus':              hr_status,
            'VerifiedBy':            'Sudha G Rao',
            'VerifiedOn':            _dt(claim.StatusDate),

            # ---- Finance (claim-level; per-split values are in Splits[]) ----
            'HoldAmountFinance':     _num(hold_fin),
            'HoldReleaseAmount':     _num(release_hold),
            'RejectedAmount':        _num(rejected_fin),
            'FinanceRemarks':        finance_remarks,
            'FinanceStatus':         finance_status,
            'PayableAmount':         _num(payable_amount),
            'Paid':                  _num(paid_amt),
            'PaidOn':                _dt(paid_on),

            # ---- Bank ----
            'BankName':              bank_name,
            'AccountNumber':         acct_no,
            'IFSCCode':              ifsc,
            'BeneficiaryName':       beneficiary,

            # ---- Classification ----
            'NatureOfExpense':       nature_of_expense,
            'WorkingLocation':       None,
            'AccountingLocation':    accounting_loc,

            # ---- Nested lists ----
            'Children':              child_items,
            'Splits':                split_items,
        })

    return JsonResponse({'count': len(results), 'results': results})


def paymentreview(request, ClaimNumber):
    claim = get_object_or_404(ParentModel, ClaimNumber=ClaimNumber)

    if request.method == 'POST':
        
        new_financestatus = request.POST.get('financestatus')  
        paymentcomments = request.POST.get('paymentcomments')       

        claim_status, created = ClaimStatus.objects.get_or_create(claim=claim) 
        claim_status.financestatus = new_financestatus   
        claim_status.paymentcomments = paymentcomments
        claim_status.save()
                                                        

        to_email = [claim.user.email]

        sendmailpayment(to_email, ClaimNumber, new_financestatus, paymentcomments,claim.user)

        return redirect('accountsview')

    return render(request, "accountsview.html") 


from django.db.models import Prefetch, Sum
from django.utils import timezone

def generatereport(request):
    # Preload related ClaimStatus and ChildModel in one go
    today = timezone.now().date()
    two_months_ago = today - timedelta(days=30)  # approx 2 months

    # Filter only claims approved within the last 2 months (using StatusDateAccounts)
    approvedclaims = ParentModel.objects.filter(
        claimstatus_set__status='Approved'
       
    )

    # Parent claim data for accounts approved in last 2 months
    parentclaimdata = ParentModel.objects.filter(
        claimstatus_set__accountstatus='Approved',
       
    ).order_by('-ClaimNumber')

    projects = Project.objects.all()
    subprojects = Subproject.objects.all()

    # Instead of looping, use annotation to calculate total claim amounts
    total_claim_amounts = (
    ChildModel.objects
    .values("parent__ClaimNumber")
    .annotate(total_amount=Sum("TotalClaimAmount"))
    .order_by()
    )

    # Convert to list of tuples instead of dict
    total_claim_amounts = [
        (item["parent__ClaimNumber"], item["total_amount"] or 0)
        for item in total_claim_amounts
    ]


    # Build user_count_list only once
    user_count_list = [{
        'approvedclaims': approvedclaims,
        'StatusDateAccounts': approvedclaims.first().StatusDateAccounts if approvedclaims.exists() else None
    }]

    data = {
        'user_count_list': user_count_list,
        'parentclaimdata': parentclaimdata,
        'StatusDateAccounts': approvedclaims.first().StatusDateAccounts if approvedclaims.exists() else None,
        'total_claim_amounts': total_claim_amounts,  # dict: {ClaimNumber: total}
        'projects': projects,
        'subprojects': subprojects,
    }

    return render(request, "generatereport.html", data)

@login_required
def generatereportoptimized(request):
    try:
        monthdata = []
        selected_month = None
        selected_year = None
        selected_project = None
        user_count_list = []
        StatusDate = None

        if request.method == 'POST':
            selected_month = request.POST.get('month')
            selected_year = request.POST.get('year')
            selected_project = request.POST.get('project_name')
            start_date = request.POST.get('startdate')
            end_date = request.POST.get('enddate')
            user_id = (request.POST.get('user_id') or '').strip()
            user_name = (request.POST.get('user_name') or '').strip()

            try:
                if selected_month:
                    selected_month = int(selected_month)
                if selected_year:
                    selected_year = int(selected_year)

                qs = ParentModel.objects.filter(claimstatus_set__accountstatus='Approved')

                if start_date and end_date:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    qs = qs.filter(StatusDate__date__range=(start_date_obj, end_date_obj))
                else:
                    if selected_year:
                        qs = qs.filter(StatusDate__year=selected_year)
                    if selected_month:
                        qs = qs.filter(StatusDate__month=selected_month)

                if selected_project:
                    qs = qs.filter(Project=selected_project)

                if user_id:
                    qs = qs.filter(user_id=user_id)
                elif user_name:
                    qs = qs.filter(
                        Q(user__first_name__icontains=user_name) |
                        Q(user__last_name__icontains=user_name)
                    )

                # Only run the query if at least one filter was actually provided
                if any([selected_year, selected_month, selected_project,
                        start_date and end_date, user_id, user_name]):
                    monthdata = qs
                else:
                    monthdata = []

            except ValueError as e:
                print(f"Value error: {e}")
                selected_month = None
                selected_year = None
                monthdata = []
            except Exception as e:
                print(f"Error in filtering: {e}")
                monthdata = []

        approvedclaims = ParentModel.objects.filter(claimstatus_set__accountstatus='Approved').order_by('ClaimNumber')

        total_claim_amounts = []
        projects = Project.objects.all()
        subprojects = Subproject.objects.all()

        for claim in monthdata:
            StatusDate = claim.StatusDate
            child_claim = ChildModel.objects.filter(parent=claim).first()
            total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
            total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))
            user_count_list.append({
                'approvedclaim': claim,
                'StatusDate': StatusDate,
                'total_claim_amount': total_claim_amount
            })

        context = {
            'monthdata': monthdata,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_project': selected_project,
            'user_count_list': user_count_list,
            'parentclaimdata': approvedclaims,
            'StatusDate': StatusDate,
            'total_claim_amounts': total_claim_amounts,
            'projects': projects,
            'subprojects': subprojects,
        }

        return render(request, 'generatereportoptimized.html', context)

    except Exception as e:
        print(f"General error: {e}")
        return render(request, 'generatereportoptimized.html')
    


from datetime import datetime


def build_claim_queryset(data):
    """
    Shared filter for the page view (request.POST) and the download views
    (request.GET). Every filter is optional and they combine with AND:
      - name only
      - name + year / month / dates / project
      - any other combination without a name

    UserName column = user.first_name, so the name is matched on first_name only.
    """
    year       = (data.get('year') or '').strip()
    month      = (data.get('month') or '').strip()
    start_date = (data.get('startdate') or '').strip()
    end_date   = (data.get('enddate') or '').strip()
    project    = (data.get('project_name') or '').strip()
    user_id    = (data.get('user_id') or '').strip()
    user_name  = (data.get('user_name') or '').strip()

    qs = ParentModel.objects.filter(claimstatus_set__accountstatus='Approved')
    has_filter = False

    # ---- Date / period (same priority as before: range > year+month > year)
    if start_date and end_date:
        start_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_obj   = datetime.strptime(end_date, '%Y-%m-%d').date()
        qs = qs.filter(StatusDate__date__range=(start_obj, end_obj))
        has_filter = True
    elif year and month:
        qs = qs.filter(StatusDate__year=int(year), StatusDate__month=int(month))
        has_filter = True
    elif year:
        qs = qs.filter(StatusDate__year=int(year))
        has_filter = True

    # ---- Project
    if project:
        qs = qs.filter(Project=project)
        has_filter = True

    # ---- Name (UserName column = user.first_name)
    if user_id.isdigit():
        qs = qs.filter(user_id=int(user_id))        # picked from suggestions
        has_filter = True
    elif user_name:
        qs = qs.filter(user__first_name__icontains=user_name)   # typed only
        has_filter = True

    if not has_filter:
        return ParentModel.objects.none()

    # distinct() because the claimstatus join can repeat a claim
    return qs.select_related('user').distinct()


@login_required
def generatereportfinance(request):

    monthdata = ParentModel.objects.none()
    selected_month = None
    selected_year = None
    selected_project = None
    user_count_list = []
    StatusDate = None

    if request.method == 'POST':
        selected_month   = request.POST.get('month')
        selected_year    = request.POST.get('year')
        selected_project = request.POST.get('project_name')

        try:
            if selected_month:
                selected_month = int(selected_month)
            if selected_year:
                selected_year = int(selected_year)

            monthdata = build_claim_queryset(request.POST)

        except ValueError as e:
            print(f"Value error: {e}")
            selected_month = None
            selected_year = None
            monthdata = ParentModel.objects.none()
        except Exception as e:
            print(f"Error in filtering: {e}")
            monthdata = ParentModel.objects.none()

    # Get all approved claims for the summary (regardless of current filtering)
    approvedclaims = ParentModel.objects.filter(
        claimstatus_set__accountstatus='Approved'
    ).order_by('ClaimNumber')

    total_claim_amounts = []
    projects = Project.objects.all()
    subprojects = Subproject.objects.all()

    # Build user_count_list from the FILTERED data (monthdata)
    for claim in monthdata:
        StatusDate = claim.StatusDate
        child_claim = ChildModel.objects.filter(parent=claim).first()

        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

        user_count_list.append({
            'approvedclaim': claim,
            'StatusDate': StatusDate,
            'total_claim_amount': total_claim_amount
        })

    dt_numbers = (
        User.objects
        .exclude(last_name="")
        .values_list("last_name", flat=True)
        .distinct()
    )
    uploaded_files = ExcelFile.objects.all().order_by('-file_date', '-uploaded_at')

    context = {
        'monthdata': monthdata,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_project': selected_project,
        'user_count_list': user_count_list,
        'parentclaimdata': approvedclaims,
        'StatusDate': StatusDate,
        'total_claim_amounts': total_claim_amounts,
        'projects': projects,
        'subprojects': subprojects,
        "dt_numbers": dt_numbers,
        'uploaded_files': uploaded_files,
    }

    return render(request, "generatereportfinance.html", context)
    

from django.http import HttpResponse
from django.db.models import Sum
from openpyxl import Workbook
from openpyxl.styles import Font

from .models import ParentModel

import json

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import UserProfileB



import traceback

import json
import traceback

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import UserProfileB


@login_required
def update_bank_details(request):

    try:

        if request.method != "POST":
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Invalid request method."
                },
                status=400
            )

        data = json.loads(request.body)

        dtnumber = data.get("dtnumber", "").strip()

        try:
            selected_user = User.objects.get(
                last_name=dtnumber
            )

        except User.DoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "DT number not found."
                },
                status=404
            )

        profile, created = UserProfileB.objects.get_or_create(
            user=selected_user
        )

        profile.nameasperbank = data.get("nameasperbank", "")
        profile.dtnumber = dtnumber
        profile.bankname = data.get("bankname", "")
        profile.accountnumber = data.get("accountnumber", "")
        profile.ifsccode = data.get("ifsccode", "")

        profile.save()

        return JsonResponse(
            {
                "status": "success",
                "message": (
                    "Bank details created successfully."
                    if created
                    else "Bank details updated successfully."
                )
            }
        )

    except Exception as e:
        traceback.print_exc()

        return JsonResponse(
            {
                "status": "error",
                "message": str(e)
            },
            status=500
        )

from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, OuterRef, Subquery, Sum
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
import logging
from decimal import Decimal

from .models import ParentModel, ClaimSplit  # adjust import path

logger = logging.getLogger(__name__)


# NOTE: make sure ClaimSplit is imported at the top of this views file, e.g.
# from .models import ParentModel, ChildModel, ClaimStatus, ClaimSplit

from django.db.models import Q


def apply_claim_date_filters(qs, year="", month="", startdate="", enddate=""):
    """
    Date filters match a claim when EITHER:
      - the claim's StatusDate is in the range, OR
      - any of its ClaimSplit rows has last_updated in the range.
    All split conditions sit in one Q, so ONE split must satisfy them together.
    """
    claim_q = Q()
    split_q = Q()

    if year:
        claim_q &= Q(StatusDate__year=year)
        split_q &= Q(splits__last_updated__year=year)
    if month:
        claim_q &= Q(StatusDate__month=int(month))
        split_q &= Q(splits__last_updated__month=int(month))
    if startdate:
        claim_q &= Q(StatusDate__date__gte=startdate)
        split_q &= Q(splits__last_updated__date__gte=startdate)
    if enddate:
        claim_q &= Q(StatusDate__date__lte=enddate)
        split_q &= Q(splits__last_updated__date__lte=enddate)

    if not claim_q:                      # no date filter chosen
        return qs
    return qs.filter(claim_q | split_q).distinct()


@login_required
def download_excel_latest(request):
    from collections import defaultdict
    from django.contrib.auth import get_user_model
    User = get_user_model()

    year      = request.GET.get("year") or ""
    month     = request.GET.get("month") or ""
    startdate = request.GET.get("startdate") or ""
    enddate   = request.GET.get("enddate") or ""
    project   = request.GET.get("project_name") or ""
    user_id   = (request.GET.get("user_id") or "").strip()
    user_name = (request.GET.get("user_name") or "").strip()

    try:
        # Only claims whose ClaimStatus is Approved by both approver and accounts.
        # Both conditions are in ONE filter() so they match the SAME ClaimStatus row.
        # The relation name is "claimstatus_set" (the related_name on the FK).
        claims = (
            ParentModel.objects
            .filter(
                claimstatus_set__status="Approved",
                claimstatus_set__accountstatus="Approved",
            )
            .select_related("user")
            .prefetch_related("claimstatus_set", "child_models")
            .distinct()
            .order_by("-ClaimNumber")
        )

        # Date filters: claim StatusDate OR any split's last_updated
        claims = apply_claim_date_filters(claims, year, month, startdate, enddate)

        # --- Alternative: select strictly by StatusDate (as in your snippet) ---
        # Use this INSTEAD of apply_claim_date_filters above if you want that.
        # startdate / enddate must be date objects or "YYYY-MM-DD" strings.
        # if startdate and enddate:
        #     claims = claims.filter(StatusDate__date__range=(startdate, enddate))

        if project:
            claims = claims.filter(Project=project)

        # Name filter (UserName column = user.first_name)
        if user_id.isdigit():
            claims = claims.filter(user_id=int(user_id))                    # picked from suggestions
        elif user_name:
            claims = claims.filter(user__first_name__icontains=user_name)   # typed only

        # Evaluate now, then load every ClaimSplit of these claims in ONE query,
        # using the ClaimSplit.claim foreign key.
        claims = list(claims)
        claim_ids = [c.pk for c in claims]

        splits_by_claim = defaultdict(list)
        for sp in ClaimSplit.objects.filter(claim_id__in=claim_ids).order_by("claim_id", "id"):
            splits_by_claim[sp.claim_id].append(sp)

        logger.info(
            "download_excel_latest: %s claims, %s claims with splits",
            len(claims), len(splits_by_claim),
        )
    except Exception:
        logger.exception("download_excel_latest: failed to build queryset")
        return HttpResponse("Could not build the claim report. Check server logs.", status=500)

    wb = Workbook()
    ws = wb.active
    ws.title = "Claims Report"

    headers = [
        "Sl.No.", "Emp ID", "Claim No.", "Emp Name", "Item",
        "Department", "Manager", "Project", "Sub Project", "Claim Period",
        "Claimed for the month", "Details", "Claim Date", "Claim Status",
        "Current Reviewer Name", "Current Reviewer DT No", "Applied/Accepted Date",
        "Total Claim Amount", "Hold Amount By HR", "Rejected Amount HR",
        "Approved Amount", "Advance if any for deduction", "Final Appr.Amt",
        "HR Remarks", "HR Status", "Verified by", "Verified on",
        "Hold Amount Finance", "Hold Release Amount", "Rejected Amount",
        "Finance Remarks", "Finance Status", "Payable Amount",
        "Paid", "Paid on", "Bank Name", "Account Number", "IFSC Code",
        "Beneficiary Name", "Nature Of Expense", "Working Location",
        "Accounting Location",
        "Split No.", "Split Created On",          # cols 43, 44
    ]

    # "Approved Amount" (col 21, 0-based index 20) is removed from the Excel output.
    # The row lists are still built with all 44 slots; the column is dropped when writing.
    DROP_IDX = 20
    visible_headers = headers[:DROP_IDX] + headers[DROP_IDX + 1:]

    for col_num, header in enumerate(visible_headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)

    # Columns (1-based) that hold claim-level values, identical on every row of a
    # claim. Only these are merged. Item, period, month, the finance columns,
    # location columns and the split columns can differ per row, so stay unmerged.
    #
    # NOTE: column 18 (Total Claim Amount) can now differ per split row. Because
    # merge_identical_runs only merges runs of IDENTICAL values, it is safe to keep
    # it here: equal values merge, different split totals stay separate.
    MERGE_COLS = {
        1, 2, 3, 4, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 22, 23, 24, 25, 26, 27, 36, 37, 38, 39,
    }
    # Column 21 (Approved Amount) is no longer written, so drop it from the merge
    # set and shift every later column one place to the left.
    MERGE_COLS = {(c - 1 if c > DROP_IDX + 1 else c) for c in MERGE_COLS if c != DROP_IDX + 1}

    # 0-based list indexes
    IDX_TOTAL = 17
    IDX_NATURE, IDX_WORKING, IDX_ACCOUNTING = 39, 40, 41
    IDX_SPLIT_NO, IDX_SPLIT_CREATED = 42, 43

    def safe(obj, name, default=""):
        if obj is None:
            return default
        v = getattr(obj, name, default)
        return default if v is None else v

    def fmt_date(value):
        if not value:
            return ""
        try:
            return value.strftime("%d-%m-%Y")
        except Exception:
            return str(value)

    def fmt_duration(d1, d2):
        left  = fmt_date(d1) if d1 else "—"
        right = fmt_date(d2) if d2 else "—"
        if left == "—" and right == "—":
            return ""
        return f"{left} - {right}"

    def month_label(dt):
        if not dt:
            return ""
        try:
            return dt.strftime("%b-%Y")
        except Exception:
            return ""

    MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

    def month_span_label(start, end):
        """
        12-10-2026 to 11-12-2026 -> "Oct-Nov-Dec-2026"
        15-12-2026 to 10-02-2027 -> "Dec-2026-Jan-Feb-2027"
        one date / same month    -> "Oct-2026"
        """
        if not start and not end:
            return ""
        start = start or end
        end = end or start

        # accept date or datetime
        if hasattr(start, "date") and callable(start.date):
            start = start.date()
        if hasattr(end, "date") and callable(end.date):
            end = end.date()

        try:
            if end < start:          # bad range: fall back to the From month
                end = start

            months = []
            y, m = start.year, start.month
            while (y, m) <= (end.year, end.month):
                months.append((y, m))
                m += 1
                if m == 13:
                    y, m = y + 1, 1
        except Exception:
            return ""

        parts = []
        for idx, (y, m) in enumerate(months):
            parts.append(MONTH_ABBR[m - 1])
            # print the year after the last month of each year
            if idx == len(months) - 1 or months[idx + 1][0] != y:
                parts.append(str(y))
        return "-".join(parts)

    def parent_values(claim, user, profile, sl_no, total_claim_amount,
                      reviewer_name, reviewer_dt):
        return [
            sl_no,                                                # 1  Sl.No.
            safe(user, "last_name"),                              # 2  Emp ID
            claim.ClaimNumber,                                    # 3  Claim No.
            safe(user, "first_name"),                             # 4  Emp Name
            "",                                                   # 5  Item            (child)
            claim.Department,                                     # 6  Department
            claim.Manager,                                        # 7  Manager
            claim.Project,                                        # 8  Project
            claim.Subproject,                                     # 9  Sub Project
            "",                                                   # 10 Claim Period    (child)
            "",                                                   # 11 Claimed month   (child)
            claim.ExpenseDetails,                                 # 12 Details
            fmt_date(claim.DateofCreation),                       # 13 Claim Date
            "",                                                   # 14 Claim Status        (status)
            reviewer_name,                                        # 15 Reviewer Name
            reviewer_dt,                                          # 16 Reviewer DT No
            fmt_date(claim.StatusDate),                           # 17 Applied/Accepted
            total_claim_amount,                                   # 18 Total Claim Amount
            "",                                                   # 19 Hold Amount By HR   (status)
            "",                                                   # 20 Rejected Amount HR  (status)
            "",                                                   # 21 Approved Amount     (status)
            "",                                                   # 22 Advance             (status)
            "",                                                   # 23 Final Appr.Amt      (status)
            "",                                                   # 24 HR Remarks          (status)
            "",                                                   # 25 HR Status           (status)
            "Sudha G Rao",                                        # 26 Verified by
            fmt_date(claim.StatusDate),                           # 27 Verified on
            "",                                                   # 28 Hold Amount Finance  (finance/split)
            "",                                                   # 29 Hold Release Amount  (finance/split)
            "",                                                   # 30 Rejected Amount      (finance/split)
            "",                                                   # 31 Finance Remarks      (finance/split)
            "",                                                   # 32 Finance Status       (finance/split)
            "",                                                   # 33 Payable Amount       (finance/split)
            "",                                                   # 34 Paid                 (finance/split)
            "",                                                   # 35 Paid on              (finance/split)
            safe(profile, "bankname"),                            # 36 Bank Name
            safe(profile, "accountnumber"),                       # 37 Account Number
            safe(profile, "ifsccode"),                            # 38 IFSC Code
            safe(profile, "nameasperbank"),                       # 39 Beneficiary Name
            safe(claim, "NatureOfExpense"),                       # 40 Nature Of Expense
            safe(claim, "WorkingLocation"),                       # 41 Working Location
            safe(claim, "AccountingLocation"),                    # 42 Accounting Location
            "",                                                   # 43 Split No.
            "",                                                   # 44 Split Created On
        ]

    def apply_child_fields(values, child, claim):
        if child is None:
            return values
        values[4]  = safe(child, "ExpenseHead")                                    # 5  Item
        values[9]  = fmt_duration(getattr(child, "ReceiptDate", None),
                                  getattr(child, "ReceiptDate1", None))            # 10 Claim Period

        # 11 Claimed month: every month covered by the duration
        d1 = getattr(child, "ReceiptDate", None)
        d2 = getattr(child, "ReceiptDate1", None)
        if d1 or d2:
            values[10] = month_span_label(d1, d2)
        else:
            values[10] = month_label(claim.DateofCreation)
        return values

    def apply_status_fields(values, status):
        if status is None:
            return values
        values[13] = safe(status, "status")               # 14 Claim Status
        values[18] = safe(status, "holdamounthr", 0)      # 19 Hold Amount By HR
        values[19] = safe(status, "rejectamounthr", 0)    # 20 Rejected Amount HR
        values[20] = safe(status, "approvedamount", 0)    # 21 Approved Amount
        values[21] = safe(status, "advancededuct", 0)     # 22 Advance if any for deduction
        values[22] = safe(status, "approvedamount", 0)    # 23 Final Appr.Amt
        values[23] = safe(status, "accountscomments")     # 24 HR Remarks
        values[24] = safe(status, "accountstatus")        # 25 HR Status

        # Nature / Working / Accounting location are saved on ClaimStatus
        if safe(status, "NatureOfExpense"):
            values[IDX_NATURE] = status.NatureOfExpense
        if safe(status, "WorkingLocation"):
            values[IDX_WORKING] = status.WorkingLocation
        if safe(status, "AccountingLocation"):
            values[IDX_ACCOUNTING] = status.AccountingLocation
        return values

    def apply_finance_fields(values, status):
        """Parent-claim finance columns, always read from ClaimStatus (claims without splits)."""
        if status is None:
            return values
        values[27] = safe(status, "holdamountfin", 0)                                    # 28 Hold Amount Finance
        values[28] = safe(status, "releasehold", 0)                                      # 29 Hold Release Amount
        values[29] = safe(status, "rejectamountfin", safe(status, "rejectamounthr", 0))  # 30 Rejected Amount
        values[30] = safe(status, "financecomments")                                     # 31 Finance Remarks
        values[31] = safe(status, "financestatus")                                       # 32 Finance Status
        values[32] = safe(status, "payableamount", 0)                                    # 33 Payable Amount
        values[33] = safe(status, "paid", 0)                                             # 34 Paid
        values[34] = fmt_date(safe(status, "paidon", None))                              # 35 Paid on
        return values

    def apply_split_fields(values, split, split_no, fallback_total):
        """Finance columns, total amount and split columns read from one ClaimSplit row."""
        values[27] = safe(split, "holdamountfin", 0)        # 28 Hold Amount Finance
        values[28] = safe(split, "releasehold", 0)          # 29 Hold Release Amount
        values[29] = safe(split, "rejectamountfin", 0)      # 30 Rejected Amount
        values[30] = safe(split, "financecomments")         # 31 Finance Remarks
        values[31] = safe(split, "financestatus")           # 32 Finance Status
        values[32] = safe(split, "payableamount", 0)        # 33 Payable Amount
        values[33] = safe(split, "paid", 0)                 # 34 Paid
        values[34] = fmt_date(safe(split, "paidon", None))  # 35 Paid on

        # 18 Total Claim Amount: the split's own total.
        # CHANGE "TotalClaimAmount" if your ClaimSplit field has a different name
        # (e.g. "amount", "splitamount"). Falls back to the claim's total if missing.
        values[IDX_TOTAL] = safe(split, "TotalClaimAmount", fallback_total)

        # 21 Approved Amount (not written to Excel) and 23 Final Appr.Amt:
        # the split's own approved amount (0 when empty), not the ClaimStatus one.
        values[20] = safe(split, "approvedamount", 0)       # 21 Approved Amount
        values[22] = safe(split, "approvedamount", 0)       # 23 Final Appr.Amt

        # Split-level locations override the claim/status-level ones
        if safe(split, "NatureOfExpense"):
            values[IDX_NATURE] = split.NatureOfExpense
        if safe(split, "WorkingLocation"):
            values[IDX_WORKING] = split.WorkingLocation
        if safe(split, "AccountingLocation"):
            values[IDX_ACCOUNTING] = split.AccountingLocation

        values[IDX_SPLIT_NO]      = split_no                                  # 43 Split No.
        values[IDX_SPLIT_CREATED] = fmt_date(safe(split, "created_on", None)) # 44 Split Created On
        return values

    def merge_identical_runs(ws, row_start, row_end, col_idx):
        if row_end <= row_start:
            return
        run_start = row_start
        run_value = ws.cell(row=row_start, column=col_idx).value

        for r in range(row_start + 1, row_end + 2):
            current = ws.cell(row=r, column=col_idx).value if r <= row_end else object()
            if current == run_value:
                continue
            if (r - 1) > run_start and run_value not in (None, ""):
                try:
                    ws.merge_cells(
                        start_row=run_start, start_column=col_idx,
                        end_row=r - 1,       end_column=col_idx,
                    )
                except Exception:
                    logger.exception(
                        "download_excel_latest: merge failed col=%s rows=%s..%s",
                        col_idx, run_start, r - 1,
                    )
            run_start = r
            run_value = current if r <= row_end else None

    # ---- DT No lookup: match full name to User.first_name, return User.last_name ----
    dt_cache = {}

    def lookup_dt_no(name):
        name = " ".join(str(name or "").split())   # trim + collapse extra spaces
        if not name:
            return ""
        if name in dt_cache:
            return dt_cache[name]

        result = (
            User.objects
            .filter(first_name__iexact=name)
            .values_list("last_name", flat=True)
            .first()
        ) or ""

        dt_cache[name] = result
        return result

    row = 2
    sl_no = 1
    try:
        for claim in claims:
            user = getattr(claim, "user", None)
            profile = getattr(user, "userprofileb", None) if user else None

            # Sort in Python so the prefetched data is used (no extra query per claim)
            children = sorted(claim.child_models.all(), key=lambda c: c.pk)
            statuses = sorted(claim.claimstatus_set.all(), key=lambda s: s.pk)
            all_splits = splits_by_claim.get(claim.pk, [])   # ClaimSplit rows for THIS claim

            # Keep the original split number (position among ALL splits of the claim),
            # but only splits whose finance status is Hold.
            hold_splits = [
                (n, sp) for n, sp in enumerate(all_splits, start=1)
                if str(safe(sp, "financestatus")).strip().lower() == "hold"
            ]

            # Claim has splits but none is on Hold -> do not show it at all
            if all_splits and not hold_splits:
                continue

            # Prefer the status row that is Approved by both approver and accounts
            # (this is the row that made the claim pass the filter above).
            approved_statuses = [
                s for s in statuses
                if s.status == "Approved" and s.accountstatus == "Approved"
            ]
            first_status = (
                approved_statuses[0] if approved_statuses
                else (statuses[0] if statuses else None)
            )

            # ---- Current Reviewer: ClaimStatus.approvedby, else Manager ----
            reviewer_name = ""
            if first_status and first_status.approvedby:
                reviewer_name = str(first_status.approvedby).strip()

            manager_name = str(claim.Manager or "").strip()

            # DT No = User.last_name where User.first_name matches the name
            reviewer_dt = lookup_dt_no(reviewer_name) or lookup_dt_no(manager_name)

            # Total Claim Amount = TotalClaimAmount stored on the FIRST child row
            # (same value the table shows via child_models.first)
            first_child = children[0] if children else None
            total_claim_amount = getattr(first_child, "TotalClaimAmount", 0) or 0

            parent_row = parent_values(
                claim, user, profile, sl_no, total_claim_amount,
                reviewer_name, reviewer_dt,
            )

            block_rows = []

            if hold_splits:
                # --- Claim with splits: ONLY the Hold split rows ---
                # Finance columns, total amount, locations and split columns come
                # from ClaimSplit; parent item rows are not shown.
                for n, split in hold_splits:
                    vals = list(parent_row)                                  # parent-model details (dept, manager, project, bank ...)
                    vals = apply_child_fields(vals, first_child, claim)      # child-model details (Item, Claim Period, Claimed month)
                    vals = apply_status_fields(vals, first_status)
                    vals = apply_split_fields(vals, split, n, total_claim_amount)
                    vals[2] = f"{claim.ClaimNumber}_{n}"                     # 3  Claim No. -> CLM1001_1, CLM1001_2
                    block_rows.append(vals)
            else:
                # --- Claim without splits: unchanged behaviour ---
                # The first item row carries the parent's finance columns, read from
                # ClaimStatus. It goes on the first item row only, so it is not
                # double counted across items.
                for i, child in enumerate(children):
                    vals = list(parent_row)
                    vals = apply_child_fields(vals, child, claim)
                    vals = apply_status_fields(vals, first_status)
                    if i == 0:
                        vals = apply_finance_fields(vals, first_status)
                    block_rows.append(vals)

                # Fallback if the claim has no child rows and no splits
                if not block_rows:
                    if approved_statuses or statuses:
                        for status in (approved_statuses or statuses):
                            vals = apply_status_fields(list(parent_row), status)
                            vals = apply_finance_fields(vals, status)
                            block_rows.append(vals)
                    else:
                        block_rows.append(list(parent_row))

            start_row = row
            for values in block_rows:
                values = values[:DROP_IDX] + values[DROP_IDX + 1:]   # drop Approved Amount
                for col_idx, val in enumerate(values, start=1):
                    ws.cell(row=row, column=col_idx).value = val
                row += 1
            end_row = row - 1

            if end_row > start_row:
                for col_idx in sorted(MERGE_COLS):
                    merge_identical_runs(ws, start_row, end_row, col_idx)

            sl_no += 1

    except Exception:
        logger.exception("download_excel_latest: failed while writing rows")
        return HttpResponse("Could not write the claim report. Check server logs.", status=500)

    for column_cells in ws.columns:
        length = max(len(str(cell.value or "")) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = min(length + 3, 60)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Claims_Report.xlsx"'
    wb.save(response)

    return response

@login_required
def download_excel_latesthr(request):
    from collections import defaultdict
    from django.contrib.auth import get_user_model
    from django.db.models import OuterRef, Subquery
    User = get_user_model()

    # No date filters here: the report is based on claim status only.
    project   = request.GET.get("project_name") or ""
    user_id   = (request.GET.get("user_id") or "").strip()
    user_name = (request.GET.get("user_name") or "").strip()

    try:
        # Only claims whose CURRENT (latest) ClaimStatus row is Approved by the approver
        # and still pending with accounts (accountstatus blank).
        #
        # Why the latest row: a claim can have several ClaimStatus rows. Filtering across
        # the relation matches a claim if ANY row qualifies, so a claim with an old
        # Approved/blank row and a newer Rejected row was still being downloaded.
        latest_status = ClaimStatus.objects.filter(claim=OuterRef("pk")).order_by("-pk")

        claims = (
            ParentModel.objects
            .annotate(
                latest_status=Subquery(latest_status.values("status")[:1]),
                latest_accountstatus=Subquery(latest_status.values("accountstatus")[:1]),
            )
            .filter(latest_status="Approved", latest_accountstatus="")
            .select_related("user")
            .prefetch_related("claimstatus_set", "child_models")
            .order_by("-ClaimNumber")
        )

        if project:
            claims = claims.filter(Project=project)

        # Name filter (UserName column = user.first_name)
        if user_id.isdigit():
            claims = claims.filter(user_id=int(user_id))                    # picked from suggestions
        elif user_name:
            claims = claims.filter(user__first_name__icontains=user_name)   # typed only

        # Evaluate now, then load every ClaimSplit of these claims in ONE query,
        # using the ClaimSplit.claim foreign key.
        claims = list(claims)
        claim_ids = [c.pk for c in claims]

        splits_by_claim = defaultdict(list)
        for sp in ClaimSplit.objects.filter(claim_id__in=claim_ids).order_by("claim_id", "id"):
            splits_by_claim[sp.claim_id].append(sp)

        logger.info(
            "download_excel_latesthr: %s claims, %s claims with splits",
            len(claims), len(splits_by_claim),
        )
    except Exception:
        logger.exception("download_excel_latesthr: failed to build queryset")
        return HttpResponse("Could not build the claim report. Check server logs.", status=500)

    wb = Workbook()
    ws = wb.active
    ws.title = "Claims Report"

    headers = [
        "Sl.No.", "Emp ID", "Claim No.", "Emp Name", "Item",
        "Department", "Manager", "Project", "Sub Project", "Claim Period",
        "Claimed for the month", "Details", "Claim Date", "Claim Status",
        "Current Reviewer Name", "Current Reviewer DT No", "Applied/Accepted Date",
        "Total Claim Amount", "Hold Amount By HR", "Rejected Amount HR",
        "Approved Amount", "Advance if any for deduction", "Final Appr.Amt",
        "HR Remarks", "HR Status", "Verified by", "Verified on",
        "Hold Amount Finance", "Hold Release Amount", "Rejected Amount",
        "Finance Remarks", "Finance Status", "Payable Amount",
        "Paid", "Paid on", "Bank Name", "Account Number", "IFSC Code",
        "Beneficiary Name", "Nature Of Expense", "Working Location",
        "Accounting Location",
        "Split No.", "Split Created On",          # cols 43, 44
    ]

    # "Approved Amount" (col 21, 0-based index 20) is removed from the Excel output.
    # The row lists are still built with all 44 slots; the column is dropped when writing.
    DROP_IDX = 20
    visible_headers = headers[:DROP_IDX] + headers[DROP_IDX + 1:]

    for col_num, header in enumerate(visible_headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)

    # Columns (1-based) that hold claim-level values, identical on every row of a
    # claim. Only these are merged. Item, period, month, the finance columns,
    # location columns and the split columns can differ per row, so stay unmerged.
    MERGE_COLS = {
        1, 2, 3, 4, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 22, 23, 24, 25, 26, 27, 36, 37, 38, 39,
    }
    # Column 21 (Approved Amount) is no longer written, so drop it from the merge
    # set and shift every later column one place to the left.
    MERGE_COLS = {(c - 1 if c > DROP_IDX + 1 else c) for c in MERGE_COLS if c != DROP_IDX + 1}

    # 0-based list indexes
    IDX_NATURE, IDX_WORKING, IDX_ACCOUNTING = 39, 40, 41
    IDX_SPLIT_NO, IDX_SPLIT_CREATED = 42, 43

    def safe(obj, name, default=""):
        if obj is None:
            return default
        v = getattr(obj, name, default)
        return default if v is None else v

    def fmt_date(value):
        if not value:
            return ""
        try:
            return value.strftime("%d-%m-%Y")
        except Exception:
            return str(value)

    def fmt_duration(d1, d2):
        left  = fmt_date(d1) if d1 else "—"
        right = fmt_date(d2) if d2 else "—"
        if left == "—" and right == "—":
            return ""
        return f"{left} - {right}"

    def month_label(dt):
        if not dt:
            return ""
        try:
            return dt.strftime("%b-%Y")
        except Exception:
            return ""

    MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

    def month_span_label(start, end):
        """
        12-10-2026 to 11-12-2026 -> "Oct-Nov-Dec-2026"
        15-12-2026 to 10-02-2027 -> "Dec-2026-Jan-Feb-2027"
        one date / same month    -> "Oct-2026"
        """
        if not start and not end:
            return ""
        start = start or end
        end = end or start

        # accept date or datetime
        if hasattr(start, "date") and callable(start.date):
            start = start.date()
        if hasattr(end, "date") and callable(end.date):
            end = end.date()

        try:
            if end < start:          # bad range: fall back to the From month
                end = start

            months = []
            y, m = start.year, start.month
            while (y, m) <= (end.year, end.month):
                months.append((y, m))
                m += 1
                if m == 13:
                    y, m = y + 1, 1
        except Exception:
            return ""

        parts = []
        for idx, (y, m) in enumerate(months):
            parts.append(MONTH_ABBR[m - 1])
            # print the year after the last month of each year
            if idx == len(months) - 1 or months[idx + 1][0] != y:
                parts.append(str(y))
        return "-".join(parts)

    def parent_values(claim, user, profile, sl_no, total_claim_amount,
                      reviewer_name, reviewer_dt):
        return [
            sl_no,                                                # 1  Sl.No.
            safe(user, "last_name"),                              # 2  Emp ID
            claim.ClaimNumber,                                    # 3  Claim No.
            safe(user, "first_name"),                             # 4  Emp Name
            "",                                                   # 5  Item            (child)
            claim.Department,                                     # 6  Department
            claim.Manager,                                        # 7  Manager
            claim.Project,                                        # 8  Project
            claim.Subproject,                                     # 9  Sub Project
            "",                                                   # 10 Claim Period    (child)
            "",                                                   # 11 Claimed month   (child)
            claim.ExpenseDetails,                                 # 12 Details
            fmt_date(claim.DateofCreation),                       # 13 Claim Date
            "",                                                   # 14 Claim Status        (status)
            reviewer_name,                                        # 15 Reviewer Name
            reviewer_dt,                                          # 16 Reviewer DT No
            fmt_date(claim.StatusDate),                           # 17 Applied/Accepted
            total_claim_amount,                                   # 18 Total Claim Amount
            "",                                                   # 19 Hold Amount By HR   (status)
            "",                                                   # 20 Rejected Amount HR  (status)
            "",                                                   # 21 Approved Amount     (status)
            "",                                                   # 22 Advance             (status)
            "",                                                   # 23 Final Appr.Amt      (status)
            "",                                                   # 24 HR Remarks          (status)
            "",                                                   # 25 HR Status           (status)
            "Sudha G Rao",                                        # 26 Verified by
            fmt_date(claim.StatusDate),                           # 27 Verified on
            "",                                                   # 28 Hold Amount Finance  (finance/split)
            "",                                                   # 29 Hold Release Amount  (finance/split)
            "",                                                   # 30 Rejected Amount      (finance/split)
            "",                                                   # 31 Finance Remarks      (finance/split)
            "",                                                   # 32 Finance Status       (finance/split)
            "",                                                   # 33 Payable Amount       (finance/split)
            "",                                                   # 34 Paid                 (finance/split)
            "",                                                   # 35 Paid on              (finance/split)
            safe(profile, "bankname"),                            # 36 Bank Name
            safe(profile, "accountnumber"),                       # 37 Account Number
            safe(profile, "ifsccode"),                            # 38 IFSC Code
            safe(profile, "nameasperbank"),                       # 39 Beneficiary Name
            safe(claim, "NatureOfExpense"),                       # 40 Nature Of Expense
            safe(claim, "WorkingLocation"),                       # 41 Working Location
            safe(claim, "AccountingLocation"),                    # 42 Accounting Location
            "",                                                   # 43 Split No.
            "",                                                   # 44 Split Created On
        ]

    def apply_child_fields(values, child, claim):
        if child is None:
            return values
        values[4]  = safe(child, "ExpenseHead")                                    # 5  Item
        values[9]  = fmt_duration(getattr(child, "ReceiptDate", None),
                                  getattr(child, "ReceiptDate1", None))            # 10 Claim Period

        # 11 Claimed month: every month covered by the duration
        d1 = getattr(child, "ReceiptDate", None)
        d2 = getattr(child, "ReceiptDate1", None)
        if d1 or d2:
            values[10] = month_span_label(d1, d2)
        else:
            values[10] = month_label(claim.DateofCreation)
        return values

    def apply_status_fields(values, status):
        if status is None:
            return values
        values[13] = safe(status, "status")               # 14 Claim Status
        values[18] = safe(status, "holdamounthr", 0)      # 19 Hold Amount By HR
        values[19] = safe(status, "rejectamounthr", 0)    # 20 Rejected Amount HR
        values[20] = safe(status, "approvedamount", 0)    # 21 Approved Amount (dropped when writing)
        values[21] = safe(status, "advancededuct", 0)     # 22 Advance if any for deduction
        values[22] = safe(status, "approvedamount", 0)    # 23 Final Appr.Amt
        values[23] = safe(status, "accountscomments")     # 24 HR Remarks
        values[24] = safe(status, "accountstatus")        # 25 HR Status

        # Nature / Working / Accounting location are saved on ClaimStatus
        if safe(status, "NatureOfExpense"):
            values[IDX_NATURE] = status.NatureOfExpense
        if safe(status, "WorkingLocation"):
            values[IDX_WORKING] = status.WorkingLocation
        if safe(status, "AccountingLocation"):
            values[IDX_ACCOUNTING] = status.AccountingLocation
        return values

    def apply_finance_fields(values, status):
        """Parent-claim finance columns, always read from ClaimStatus (with or without splits)."""
        if status is None:
            return values
        values[27] = safe(status, "holdamountfin", 0)                                    # 28 Hold Amount Finance
        values[28] = safe(status, "releasehold", 0)                                      # 29 Hold Release Amount
        values[29] = safe(status, "rejectamountfin", safe(status, "rejectamounthr", 0))  # 30 Rejected Amount
        values[30] = safe(status, "financecomments")                                     # 31 Finance Remarks
        values[31] = safe(status, "financestatus")                                       # 32 Finance Status
        values[32] = safe(status, "payableamount", 0)                                    # 33 Payable Amount
        values[33] = safe(status, "paid", 0)                                             # 34 Paid
        values[34] = fmt_date(safe(status, "paidon", None))                              # 35 Paid on
        return values

    def apply_split_fields(values, split, split_no):
        """Finance columns + split columns read from one ClaimSplit row."""
        values[27] = safe(split, "holdamountfin", 0)        # 28 Hold Amount Finance
        values[28] = safe(split, "releasehold", 0)          # 29 Hold Release Amount
        values[29] = safe(split, "rejectamountfin", 0)      # 30 Rejected Amount
        values[30] = safe(split, "financecomments")         # 31 Finance Remarks
        values[31] = safe(split, "financestatus")           # 32 Finance Status
        values[32] = safe(split, "payableamount", 0)        # 33 Payable Amount
        values[33] = safe(split, "paid", 0)                 # 34 Paid
        values[34] = fmt_date(safe(split, "paidon", None))  # 35 Paid on

        # Split-level locations override the claim/status-level ones
        if safe(split, "NatureOfExpense"):
            values[IDX_NATURE] = split.NatureOfExpense
        if safe(split, "WorkingLocation"):
            values[IDX_WORKING] = split.WorkingLocation
        if safe(split, "AccountingLocation"):
            values[IDX_ACCOUNTING] = split.AccountingLocation

        values[IDX_SPLIT_NO]      = split_no                                  # 43 Split No.
        values[IDX_SPLIT_CREATED] = fmt_date(safe(split, "created_on", None)) # 44 Split Created On
        return values

    def merge_identical_runs(ws, row_start, row_end, col_idx):
        if row_end <= row_start:
            return
        run_start = row_start
        run_value = ws.cell(row=row_start, column=col_idx).value

        for r in range(row_start + 1, row_end + 2):
            current = ws.cell(row=r, column=col_idx).value if r <= row_end else object()
            if current == run_value:
                continue
            if (r - 1) > run_start and run_value not in (None, ""):
                try:
                    ws.merge_cells(
                        start_row=run_start, start_column=col_idx,
                        end_row=r - 1,       end_column=col_idx,
                    )
                except Exception:
                    logger.exception(
                        "download_excel_latesthr: merge failed col=%s rows=%s..%s",
                        col_idx, run_start, r - 1,
                    )
            run_start = r
            run_value = current if r <= row_end else None

    # ---- DT No lookup: match full name to User.first_name, return User.last_name ----
    dt_cache = {}

    def lookup_dt_no(name):
        name = " ".join(str(name or "").split())   # trim + collapse extra spaces
        if not name:
            return ""
        if name in dt_cache:
            return dt_cache[name]

        result = (
            User.objects
            .filter(first_name__iexact=name)
            .values_list("last_name", flat=True)
            .first()
        ) or ""

        dt_cache[name] = result
        return result

    row = 2
    sl_no = 1
    try:
        for claim in claims:
            user = getattr(claim, "user", None)
            profile = getattr(user, "userprofileb", None) if user else None

            # Sort in Python so the prefetched data is used (no extra query per claim)
            children = sorted(claim.child_models.all(), key=lambda c: c.pk)
            statuses = sorted(claim.claimstatus_set.all(), key=lambda s: s.pk)
            splits   = splits_by_claim.get(claim.pk, [])     # ClaimSplit rows for THIS claim

            # The claim's current status = its LATEST ClaimStatus row (highest pk).
            # This is the same row the queryset filter checked.
            first_status = statuses[-1] if statuses else None

            # ---- Current Reviewer: ClaimStatus.approvedby, else Manager ----
            reviewer_name = ""
            if first_status and first_status.approvedby:
                reviewer_name = str(first_status.approvedby).strip()

            manager_name = str(claim.Manager or "").strip()

            # DT No = User.last_name where User.first_name matches the name
            reviewer_dt = lookup_dt_no(reviewer_name) or lookup_dt_no(manager_name)

            # Total Claim Amount = TotalClaimAmount stored on the FIRST child row
            # (same value the table shows via child_models.first)
            first_child = children[0] if children else None
            total_claim_amount = getattr(first_child, "TotalClaimAmount", 0) or 0

            parent_row = parent_values(
                claim, user, profile, sl_no, total_claim_amount,
                reviewer_name, reviewer_dt,
            )

            block_rows = []

            # --- 1) Item rows: one per child (the parent claim rows) ---
            # The first item row carries the parent's finance columns, always read
            # from ClaimStatus, whether or not the claim has splits. It goes on the
            # first item row only, so it is not double counted across items.
            for i, child in enumerate(children):
                vals = list(parent_row)
                vals = apply_child_fields(vals, child, claim)
                vals = apply_status_fields(vals, first_status)
                if i == 0:
                    vals = apply_finance_fields(vals, first_status)
                block_rows.append(vals)

            # A claim with splits but no child rows still needs its parent row
            if splits and not children:
                vals = list(parent_row)
                vals = apply_status_fields(vals, first_status)
                vals = apply_finance_fields(vals, first_status)
                block_rows.append(vals)

            # --- 2) Split rows: one per ClaimSplit of this claim (ordered by id) ---
            # Finance columns, locations and split columns come only from ClaimSplit.
            for n, split in enumerate(splits, start=1):
                vals = list(parent_row)                      # same details as the parent claim
                vals = apply_status_fields(vals, first_status)
                vals = apply_split_fields(vals, split, n)    # overrides only the split fields
                vals[2] = f"{claim.ClaimNumber}_{n}"         # 3  Claim No. -> e.g. CLM1001_1, CLM1001_2
                block_rows.append(vals)

            # --- Fallback if the claim has no child rows and no splits ---
            if not block_rows:
                vals = list(parent_row)
                vals = apply_status_fields(vals, first_status)
                vals = apply_finance_fields(vals, first_status)
                block_rows.append(vals)

            start_row = row
            for values in block_rows:
                values = values[:DROP_IDX] + values[DROP_IDX + 1:]   # drop Approved Amount
                for col_idx, val in enumerate(values, start=1):
                    ws.cell(row=row, column=col_idx).value = val
                row += 1
            end_row = row - 1

            if end_row > start_row:
                for col_idx in sorted(MERGE_COLS):
                    merge_identical_runs(ws, start_row, end_row, col_idx)

            sl_no += 1

    except Exception:
        logger.exception("download_excel_latesthr: failed while writing rows")
        return HttpResponse("Could not write the claim report. Check server logs.", status=500)

    for column_cells in ws.columns:
        length = max(len(str(cell.value or "")) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = min(length + 3, 60)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Claims_Report.xlsx"'
    wb.save(response)

    return response


from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import VendorParentModel, VendorDetailModel


from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import VendorParentModel, VendorDetailModel


from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import VendorParentModel, VendorDetailModel


from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import VendorParentModel, VendorDetailModel


def download_vendor_excel_latest(request):
    if request.method != "POST":
        return HttpResponse("Invalid request method")

    # Filters from form
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")
    project_name = request.POST.get("project_name")
    vendor_name = request.POST.get("vendor_name")

    queryset = VendorParentModel.objects.all()

    if start_date:
        queryset = queryset.filter(DateofCreation__gte=start_date)

    if end_date:
        queryset = queryset.filter(DateofCreation__lte=end_date)

    if project_name:
        queryset = queryset.filter(ProjectName=project_name)

    if vendor_name:
        queryset = queryset.filter(VendorName=vendor_name)

    wb = Workbook()
    ws = wb.active
    ws.title = "Vendor Claims"

    headers = [
        "Claim Number",
        "Raised By",
        "Vendor Name",
        "Project Name",
        "Service Month",
        "Date of Invoice",
        "Basic Value",
        "GST Rate",
        "GST Value",
        "Invoice Value",
        "TDS Rate",
        "TDS Value",
        "GST on Hold",
        "Advance Paid",
        "Amount On Hold",
        "Net Payable",
        "Approved By",
        "Bank Name",
        "Account Number",
        "IFSC Code",
        "Beneficiary Name",
        "PAN",
        "GST Number",
        "Mail ID",
        "Contact Number",
        "MSME Certificate",
        "Lower Tax Deduction Certificate"
    ]

    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    row_num = 2

    for claim in queryset:
        vendor = VendorDetailModel.objects.filter(
            VendorName=claim.VendorName
        ).first()

        # ---------------- Calculations ----------------
        try:
            basic_value = float(claim.TotalClaimAmount or 0)
        except:
            basic_value = 0.0

        try:
            gst_rate = float(claim.GST or 0)
        except:
            gst_rate = 0.0

        tds_rate = 0.0  # Update if TDS field exists

        try:
            advance_paid = float(claim.AdvanceAmount or 0)
        except:
            advance_paid = 0.0

        gst_on_hold = 0.0
        amount_on_hold = 0.0

        gst_value = round((basic_value * gst_rate) / 100, 2)
        invoice_value = round(basic_value + gst_value, 2)
        tds_value = round((basic_value * tds_rate) / 100, 2)

        net_payable = round(
            invoice_value
            - tds_value
            - gst_on_hold
            - advance_paid
            - amount_on_hold,
            2
        )

        # ---------------- Service Month ----------------
        service_month = ""
        if claim.FromDate:
            service_month = claim.FromDate.strftime("%B")

        # ---------------- MSME ----------------
        msme = "No"
        if vendor and vendor.MSMECopy:
            if "default.pdf" not in str(vendor.MSMECopy):
                msme = "Yes"

        # ---------------- Write Excel ----------------
        ws.cell(row=row_num, column=1, value=claim.VendorClaimNumber or "")
        ws.cell(row=row_num, column=2, value=claim.RaisedBy or "")
        ws.cell(row=row_num, column=3, value=claim.VendorName or "")
        ws.cell(row=row_num, column=4, value=claim.ProjectName or "")
        ws.cell(row=row_num, column=5, value=service_month)
        ws.cell(
            row=row_num,
            column=6,
            value=claim.InvoiceDate.strftime("%d-%m-%Y") if claim.InvoiceDate else ""
        )

        ws.cell(row=row_num, column=7, value=basic_value)
        ws.cell(row=row_num, column=8, value=gst_rate)
        ws.cell(row=row_num, column=9, value=gst_value)
        ws.cell(row=row_num, column=10, value=invoice_value)
        ws.cell(row=row_num, column=11, value=tds_rate)
        ws.cell(row=row_num, column=12, value=tds_value)
        ws.cell(row=row_num, column=13, value=gst_on_hold)
        ws.cell(row=row_num, column=14, value=advance_paid)
        ws.cell(row=row_num, column=15, value=amount_on_hold)
        ws.cell(row=row_num, column=16, value=net_payable)
        ws.cell(row=row_num, column=17, value="Prabhakara G V Reddy")
        ws.cell(row=row_num, column=18, value=vendor.BankName if vendor else "")
        ws.cell(row=row_num, column=19, value=vendor.AccountNumber if vendor else "")
        ws.cell(row=row_num, column=20, value=vendor.IFSCCode if vendor else "")
        ws.cell(row=row_num, column=21, value=claim.VendorName or "")
        ws.cell(row=row_num, column=22, value=vendor.PanNumber if vendor else "")
        ws.cell(row=row_num, column=23, value=vendor.VendorGST if vendor else "")
        ws.cell(row=row_num, column=24, value=vendor.VendorEmail if vendor else "")
        ws.cell(row=row_num, column=25, value=vendor.MobileNumber if vendor else "")
        ws.cell(row=row_num, column=26, value=msme)
        ws.cell(row=row_num, column=27, value="")

        row_num += 1

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="vendor_claims.xlsx"'

    wb.save(response)
    return response



def view_child_history(request):
    user = request.user
    parentclaimdata = ParentModel.objects.filter(user=user).order_by('-ClaimNumber')

    data = {
        'user': user,
        'parentclaimdata': parentclaimdata,        
    }

    return render(request, 'history.html', data)


import os
import zipfile
from django.http import HttpResponse
from django.core.files.storage import default_storage

def download_claim_files(request, ClaimNumber):
    # Get the claim data (adjust this based on your model structure)
    parentclaimdata = ParentModel.objects.get(ClaimNumber=ClaimNumber)
    childclaimdata  = ChildModel.objects.filter(parent=parentclaimdata)

    # Create a zip file
    zip_file_path = os.path.join(default_storage.location, f"{ClaimNumber}_files.zip")
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        for child_claim in childclaimdata:
            if child_claim.BillAttachment:
                file_path = default_storage.path(child_claim.BillAttachment.name)
                zip_file.write(file_path, os.path.basename(file_path))

    # Prepare the response
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Claimnumber{ClaimNumber}_files.zip"'

    # Write the zip file to the response
    with open(zip_file_path, 'rb') as zip_file:
        response.write(zip_file.read())

    # Delete the temporary zip file
    os.remove(zip_file_path)

    return response

from django.views.decorators.http import require_GET
@login_required  # plus the same role check your report view uses
@require_GET
def user_suggestions(request):
    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    users = (
        User.objects
        .filter(parentmodel__isnull=False)  # only users who have claims
        .filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
        .distinct()
        .order_by('first_name')[:10]
    )

    return JsonResponse({
        'results': [
            {'id': u.id, 'name': u.first_name or u.username, 'dt': u.last_name}
            for u in users
        ]
    })

import os
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO

import pandas as pd
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import FileResponse, HttpResponse
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_POST


def get_filtered_claims(data):
    """Filters shared by the report, Excel and vouchers. Returns a plain ParentModel queryset."""
    year = data.get('year')
    month = data.get('month')
    start = data.get('startdate')
    end = data.get('enddate')
    project = data.get('project_name')
    username = (data.get('username') or '').strip()

    qs = ParentModel.objects.all()

    if start or end:
        # StatusDate is a DateTimeField, so compare on the date part
        if start:
            qs = qs.filter(StatusDate__date__gte=start)
        if end:
            qs = qs.filter(StatusDate__date__lte=end)
    else:
        if year:
            qs = qs.filter(StatusDate__year=year)
        if month:
            qs = qs.filter(StatusDate__month=month)

    if project:
        qs = qs.filter(Project=project)

    user_id = (data.get('user_id') or '').strip()
    user_name = (data.get('user_name') or '').strip()

    if user_id.isdigit():
        qs = qs.filter(user_id=user_id)                      # picked from suggestions
    elif user_name:
        qs = qs.filter(user__first_name__icontains=user_name)

    return qs


# @login_required + whatever role check your report view uses
@require_POST
def generate_excel(request):
    claims = (
        get_filtered_claims(request.POST)
        .select_related('user')
        .prefetch_related('claimstatus_set')
        .annotate(total_claim=Sum('child_models__ClaimAmount'))
        .order_by('-StatusDate', 'ClaimNumber')
    )

    rows = []
    total_claim = 0
    total_approved = 0

    for claim in claims:
        statuses = list(claim.claimstatus_set.all())
        status = statuses[0] if statuses else None

        claim_amount = float(claim.total_claim or 0)
        approved_amount = float(status.approvedamount or 0) if status else 0

        account_status = (
            status.accountstatus
            if status and status.accountstatus in ('Approved', 'Rejected')
            else 'Pending'
        )
        payment = 'PaymentDone' if status and status.financestatus == 'PaymentDone' else 'Pending'

        total_claim += claim_amount
        total_approved += approved_amount

        rows.append({
            'ClaimNumber': claim.ClaimNumber,
            'DateofApproval': claim.StatusDate.strftime('%d-%m-%Y') if claim.StatusDate else '',
            'AssociateName': claim.user.first_name if claim.user else '',
            'DTNumber': claim.user.last_name if claim.user else '',
            'Department': claim.Department,
            'Manager': claim.Manager,
            'Project': claim.Project,
            'Subproject': claim.Subproject,
            'ExpenseDetails': claim.ExpenseDetails,
            'TotalClaimAmount': claim_amount,
            'ApprovedAmount': approved_amount,
            'AccountStatus': account_status,
            'Payment': payment,
        })

    if not rows:
        return HttpResponse('No claims found for the selected filters.', status=404)

    rows.append({
        'ClaimNumber': 'Total',
        'TotalClaimAmount': round(total_claim, 2),
        'ApprovedAmount': round(total_approved, 2),
    })

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name='Claims')

    project = get_valid_filename(request.POST.get('project_name') or 'all_projects')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'selected_claims_{project}_{timestamp}.xlsx'

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# @login_required + whatever role check your report view uses
@require_POST
def download_vouchers(request):
    claims = get_filtered_claims(request.POST)

    # One query for all attachments instead of one query per claim
    children = (
        ChildModel.objects
        .filter(parent__in=claims)
        .exclude(BillAttachment='')
        .select_related('parent__user')
    )

    # Spooled to disk, so a big zip doesn't sit in memory
    tmp = tempfile.TemporaryFile()
    files_added = 0
    used_names = set()

    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
        for child in children:
            if not child.BillAttachment:
                continue

            try:
                file_path = default_storage.path(child.BillAttachment.name)
            except NotImplementedError:
                # Storage isn't local disk (e.g. S3), see note below
                continue

            if not os.path.exists(file_path):
                continue

            parent = child.parent
            arcname = os.path.join(
                parent.user.username,
                str(parent.ClaimNumber),
                os.path.basename(file_path),
            )

            # Avoid two attachments with the same name overwriting each other on extract
            if arcname in used_names:
                base, ext = os.path.splitext(arcname)
                arcname = f'{base}_{child.pk}{ext}'
            used_names.add(arcname)

            zf.write(file_path, arcname)  # streams from disk, no file.read() into memory
            files_added += 1

    if files_added == 0:
        tmp.close()
        return HttpResponse('No voucher attachments found for the selected filters.', status=404)

    tmp.seek(0)
    return FileResponse(
        tmp,
        as_attachment=True,
        filename='Vouchers.zip',
        content_type='application/zip',
    )
from django.http import HttpResponse, StreamingHttpResponse

import logging
import os
import tempfile
import zipfile
import re

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponse

NO_COMPRESS_EXT = {".jpg", ".jpeg", ".png", ".pdf", ".zip", ".gif", ".webp"}


def _safe(name, default="Unknown"):
    """Make a string safe to use as a folder/file name inside the ZIP."""
    name = re.sub(r'[\\/:*?"<>|]+', "_", str(name or "")).strip()
    return name or default


def _valid_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@login_required
def download_vouchers_latest(request):
    g = request.GET

    year         = (g.get("year") or "").strip()
    month        = (g.get("month") or "").strip()
    startdate    = (g.get("startdate") or "").strip()
    enddate      = (g.get("enddate") or "").strip()
    project      = (g.get("project_name") or "").strip()
    user_id      = (g.get("user_id") or "").strip()
    user_name    = (g.get("user_name") or "").strip()

    # ---- Validate inputs -------------------------------------------------
    if year and not year.isdigit():
        return HttpResponse("Invalid year.", status=400)
    if month and not (month.isdigit() and 1 <= int(month) <= 12):
        return HttpResponse("Invalid month.", status=400)

    start_d = end_d = None
    if startdate:
        start_d = _valid_date(startdate)
        if not start_d:
            return HttpResponse("Invalid start date.", status=400)
    if enddate:
        end_d = _valid_date(enddate)
        if not end_d:
            return HttpResponse("Invalid end date.", status=400)

    # ---- Build filters (only the ones that have a value) -----------------
    filters = {"claimstatus_set__accountstatus": "Approved"}

    # Same date field the table shows in the "ApprDt." column.
    # Change to StatusDate if that is what your list view filters on.
    date_field = "StatusDateAccounts"

    if year:
        filters[f"{date_field}__year"] = int(year)
    if month:
        filters[f"{date_field}__month"] = int(month)
    if start_d:
        filters[f"{date_field}__date__gte"] = start_d
    if end_d:
        filters[f"{date_field}__date__lte"] = end_d
    if project:
        filters["Project"] = project

    # Name: exact user id wins; otherwise fall back to first name
    # (the "UserName" column shows user.first_name)
    if user_id.isdigit():
        filters["user_id"] = int(user_id)
    elif user_name:
        filters["user__first_name__iexact"] = user_name

    # ---- Query: only claims + only children that have an attachment ------
    children_qs = (
        ChildModel.objects
        .exclude(BillAttachment="")
        .exclude(BillAttachment__isnull=True)
        .only("id", "BillAttachment", "parent_id")   # adjust FK name if different
    )

    claims = (
        ParentModel.objects
        .filter(**filters)
        .distinct()
        .select_related("user")
        .only("id", "ClaimNumber", "user__username")
        .prefetch_related(Prefetch("child_models", queryset=children_qs))
    )

    # ---- Build ZIP on disk (flat memory usage) ---------------------------
    tmp = tempfile.TemporaryFile()
    files_added = 0
    first_username = None

    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for claim in claims.iterator(chunk_size=200):
            username = claim.user.username if claim.user else "UnknownUser"
            first_username = first_username or username

            for child in claim.child_models.all():
                att = child.BillAttachment
                if not att:
                    continue

                base = os.path.basename(att.name)
                ext = os.path.splitext(base)[1].lower()
                arcname = "/".join([
                    _safe(username, "UnknownUser"),
                    _safe(claim.ClaimNumber, "NoClaimNo"),
                    f"{child.pk}_{_safe(base, 'file')}",
                ])
                ctype = zipfile.ZIP_STORED if ext in NO_COMPRESS_EXT else zipfile.ZIP_DEFLATED

                try:
                    try:
                        path = default_storage.path(att.name)      # local disk
                        if not os.path.exists(path):
                            logger.warning("Missing file: %s", att.name)
                            continue
                        zf.write(path, arcname, compress_type=ctype)
                    except NotImplementedError:                     # S3 / remote
                        with att.open("rb") as f:
                            zf.writestr(arcname, f.read(), compress_type=ctype)
                    files_added += 1
                except Exception:
                    logger.exception("Failed to add %s", att.name)

    if files_added == 0:
        tmp.close()
        return HttpResponse("No vouchers found for the selected filters.", status=404)

    tmp.seek(0)

    # ZIP name reflects the filters
    parts = ["Vouchers"]
    if user_id.isdigit() or user_name:
        parts.append(_safe(first_username or user_name))
    if year:
        parts.append(year + (f"-{int(month):02d}" if month else ""))
    if start_d or end_d:
        parts.append(f"{start_d or 'start'}_to_{end_d or 'end'}")
    if project:
        parts.append(_safe(project))
    zip_name = "_".join(parts)[:120] + ".zip"

    return FileResponse(
        tmp,
        as_attachment=True,
        filename=zip_name,
        content_type="application/zip",
    )



from django.db.models import Count, F

def duplicates(request):

    simplified_query = ChildModel.objects.values('ReceiptNumber', 'ClaimAmount', 'parent__ClaimNumber', 'parent__user__first_name').order_by("-ReceiptNumber")


    # Grouped claims list to store filtered results
    grouped_claims = []

    # Dictionary to store counts of items for filtering
    item_counts = {}

    # Count occurrences of each item
    for item in simplified_query:
        key = (item['ReceiptNumber'], item['ClaimAmount'], item['parent__ClaimNumber'], item['parent__user__first_name'])
   
        if key in item_counts:
            item_counts[key] += 1
        else:
            item_counts[key] = 1

    # Filter to keep only those groups with more than one record (indicating duplicates)
    for key, count in item_counts.items():
        receipt_number, claim_amount, parent_claim_number, username = key
       

   
        duplicate_count = simplified_query.filter(
            ReceiptNumber=receipt_number,
            ClaimAmount=claim_amount,
            parent__user__first_name=username
        ).count()
 
        if duplicate_count > 1:
            grouped_claims.append({
                'ReceiptNumber': receipt_number,
                'ClaimAmount': claim_amount,
                'parent__ClaimNumber': parent_claim_number,
                'parent__user__first_name': username
            })

  
    grouped_claims = sorted(grouped_claims, key=lambda x: x['ClaimAmount'])

    data = {
   
        'grouped_claims': grouped_claims,
    }

    return render(request, "duplicates.html", data)

def vendor(request):     
    return render(request,'base2.html') 


from django.shortcuts import render
from datetime import datetime, timedelta
import json

def vendorclaims(request):
    user = request.user
    first_name = user.first_name
    last_name = user.last_name

    # Define the date range
    today = datetime.today()
    min_date = today - timedelta(days=30)  # 30 days ago
    max_date = today + timedelta(days=30)  # 30 days from now

    # Format dates as strings in YYYY-MM-DD format
    min_date_str = min_date.strftime('%Y-%m-%d')
    max_date_str = max_date.strftime('%Y-%m-%d')
    
    # Get the user's group
    user_group = user.groups.first()  # Assuming the user is in a group

   
    vendors = VendorDetailModel.objects.all()  # Fallback if no group found

    claims = VendorParentModel.objects.all()

    claims_data = [
        {
            'vendorName': claim.VendorName,
            'fromDate': claim.FromDate.strftime('%Y-%m-%d'),
            'toDate': claim.ToDate.strftime('%Y-%m-%d')
        }
        for claim in claims
    ]

    return render(request, 'vendorclaims.html', {
        'first_name': first_name,
        'last_name': last_name,
        'projects': Project.objects.all(),  # Assuming you still need this
        'subprojects' : Subproject.objects.all(),
        'vendors': vendors,
        'claims_data': json.dumps(claims_data),  # Pass serialized claims data
        'minDate': min_date_str,
        'maxDate': max_date_str,
    })



from django.db.models import Max
from django.contrib import messages
from django.shortcuts import render, redirect

def vendorrecord(request):
    if request.user.first_name not in ['Prabhakara Reddy G V']:
        VendorId = None  
        group_to_vendor_id = {
            'GPM': 'VNGPM_',
            'GPO': 'VNGPO_',
            'HR': 'VNH_',
            'Admin': 'VNA_',
            'Finance': 'VNF_',
            'IT': 'VNI_'
        }

        for group_name, vendor_prefix in group_to_vendor_id.items():
            if request.user.groups.filter(name=group_name).exists():     
                
                # Check if there are any existing vendors with this prefix
                if VendorDetailModel.objects.filter(VendorId__startswith=vendor_prefix).count() == 0:
                    VendorId = f'{vendor_prefix}1001'
                else:
                    # Get the current maximum VendorId for this group
                    max_claim = VendorDetailModel.objects.filter(VendorId__startswith=vendor_prefix).aggregate(max_claim=Max('VendorId'))
                    max_claim_value = max_claim['max_claim']

                    if max_claim_value:
                        try:
                            numeric_part = int(max_claim_value.split('_')[1])
                            VendorId = f'{vendor_prefix}{numeric_part + 1}'
                        except (IndexError, ValueError):
                            VendorId = f'{vendor_prefix}1001'  # Default to 1001 if there's an error
                break  # Exit the loop after finding the group
            
        if request.method == "POST":
            user_groups = request.user.groups.values_list('name', flat=True)

            # Check if the user belongs to any groups
            if user_groups:
                if user_groups[0] == 'Manager':
                    if request.user.first_name == 'Sanjay MS':
                        EnteredBy = 'GPO'
                    else:
                        EnteredBy = 'GPM'
                elif user_groups[0] == 'Manager':
                    EnteredBy = 'GPM'
                elif user_groups[0] == 'Accounts':
                    EnteredBy = 'HR'
                else:
                    EnteredBy = user_groups[0]  # Get the first group name       
    
            VendorName = request.POST.get('VendorName')
            VendorEmail = request.POST.get('VendorEmail')
            VendorGST = request.POST.get('VendorGST')
            BankName = request.POST.get('BankName')
            AccountNumber = request.POST.get('AccountNumber')
            IFSCCode = request.POST.get('IFSCCode')
            PlotNumber = request.POST.get('PlotNumber')
            StreetName = request.POST.get('StreetName')
            Locality = request.POST.get('Locality')
            City = request.POST.get('City')
            Pincode = request.POST.get('Pincode')
            PanNumber = request.POST.get('PanNumber')
            State = request.POST.get('State')
            MobileNumber = request.POST.get('MobileNumber')
            GSTCopy = request.FILES.get('GSTCopy')  
            MSMECopy = request.FILES.get('MSMECopy') 
            CancelledCheque = request.FILES.get('CancelledCheque') 
            PANCopy = request.FILES.get('PANCopy') 
            EmailCopy = request.FILES.get('EmailCopy') 
            ContractCopy = request.FILES.get('ContractCopy')
            
            if not VendorName or not VendorEmail:
                messages.error(request, "Both VendorName and VendorEmail are required.")
                return render(request, 'vendordetails.html')
            
            # Check if the vendor already exists
            if VendorDetailModel.objects.filter(VendorName=VendorName, VendorEmail=VendorEmail).exists():
                messages.error(request, "A Vendor with this name and Email already exists.")
                return render(request, 'vendordetails.html')

            # Create VendorDetailModel instance
            emp = VendorDetailModel(
                EnteredBy=EnteredBy,
                VendorName=VendorName,
                VendorId=VendorId,
                VendorEmail=VendorEmail,
                VendorGST=VendorGST,
                BankName=BankName,
                AccountNumber=AccountNumber,
                IFSCCode=IFSCCode,
                PlotNumber=PlotNumber,
                StreetName=StreetName,
                Locality=Locality,
                City=City,
                Pincode=Pincode,
                PanNumber=PanNumber,
                State=State,
                MobileNumber=MobileNumber,
                GSTCopy=GSTCopy,
                CancelledCheque=CancelledCheque,
                MSMECopy=MSMECopy,
                EmailCopy=EmailCopy,
                PANCopy=PANCopy,
                ContractCopy=ContractCopy
            )
            emp.save()       

            return redirect('vendorrecord')  

        group_names = ['Finance', 'Accounts', 'HR', 'Admin', 'IT', 'GPM', 'GPO']  # Add all relevant groups here
        
        for group_name in group_names:
            if request.user.groups.filter(name=group_name).exists():
                user_group = group_name
                break  # Exit loop after finding the first matching group


        vendorrecord = VendorDetailModel.objects.all()
         

        # if user_group:
            # Filter records based on the user's group
        # vendorrecord = VendorDetailModel.objects.filter(
        #     EnteredBy=user_group
        # ).order_by('VendorId')
        # else:
        #     # If the user is not in any specified group, return an empty queryset or handle as needed
        #     vendorrecord = VendorDetailModel.objects.none()  # No records
        data = {
            'data': vendorrecord,     
        }     

        return render(request, "vendordetails.html", data)
    else:
        return render(request, "unauthorized.html")

       


def vendorforfinance(request,VendorName):

    vendor_detail = get_object_or_404(VendorDetailModel, VendorName=VendorName)
    print(vendor_detail)
 

    data = {
        'data': vendor_detail,     
    } 

    print(data)

    return render(request, "vendorforfinance.html", data)



from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Max
from .models import VendorParentModel  # Adjust the import based on your project structure

def savevendorrecord(request):
    if VendorParentModel.objects.count() == 0:
        VendorClaimNumber = 'V100'
    else:
        max_claim = VendorParentModel.objects.aggregate(max_claim=Max('VendorClaimNumber'))
        max_claim_value = max_claim['max_claim']
        if max_claim_value:        
            numeric_part = int(max_claim_value[1:])  # Skip the 'V' prefix
            VendorClaimNumber = f'V{numeric_part + 1}'

    DateofCreation = timezone.now().date()  # Use timezone-aware datetime
    RaisedBy = request.user.first_name
    DTNumber = request.user.last_name

    if request.method == "POST": 
        user_groups = request.user.groups.values_list('name', flat=True)
       
        if user_groups:
            if user_groups[0] == 'Manager':
                if request.user.first_name == 'Sanjay MS':
                    EnteredBy = 'GPO'
                else:
                    EnteredBy = 'GPM'
            elif user_groups[0] == 'Manager':
                EnteredBy = 'GPM'
            elif user_groups[0] == 'Accounts':
                EnteredBy = 'HR'
            else:
                EnteredBy = user_groups[0]  # Get the first group name      
      
        project_id = request.POST.get('Project')  # Project ID from the form
        subproject_title = request.POST.get('Subproject')  # Subproject Title from the form

        # Retrieve the Subproject based on the provided title and project ID
        subproject = Subproject.objects.filter(subproject_title=subproject_title)
        proj = Project.objects.get(id=project_id)
            
        VendorName = request.POST.get('VendorSelection')
        VendorExpenseDetail = request.POST.get('VendorExpenseDetail')
        TotalClaimAmount = request.POST.get('TotalClaimAmount')
        InvoiceNumber = request.POST.get('InvoiceNumber')
        InvoiceDate = request.POST.get('InvoiceDate')
        FromDate = request.POST.get('FromDate')     
        ToDate = request.POST.get('ToDate')  
        Description = request.POST.get('Description') 
        InvoiceAttachment = request.FILES.get('InvoiceAttachment')   
        EmailAttachment = request.FILES.get('EmailAttachment')   
        Quantity = request.POST.get('Quantity')
        Unit = request.POST.get('Unit')
        Amount = request.POST.get('Amount')
        Field = request.POST.get('Field')
        Approval = request.POST.get('Approval')
        WorkOrder = request.POST.get('WorkOrder')
        PurchaseOrder = request.POST.get('PurchaseOrder') 
        Currency = request.POST.get('Currency')
        Rate = request.POST.get('Rate')
        GST = request.POST.get('GSTPercentage')      
        Remark = request.POST.get('Remarks')         
        AddApprovedBy = request.POST.get('AddApprovedBy')
        AddAttachment = request.FILES.get('AddAttachment')
        AddField = request.POST.get('AddField')
        AdvanceApprovedBy = request.POST.get('AdvanceApprovedBy')
        AdvanceAmount = request.POST.get('AdvanceAmount')
        AdvanceAttachment = request.FILES.get('AdvanceAttachment')
        ToBeDeducted = request.POST.get('ToBeDeducted') 

        if AdvanceAmount == '':
            AdvanceAmount = 0.0
        if Amount == '':
            Amount = 0.0
         

        # Save the file and create the VendorChildModel instance
        if InvoiceAttachment:
            file_name = default_storage.save(InvoiceAttachment.name, InvoiceAttachment)
        else:
            file_name = None  

        if EmailAttachment:
            file_name2 = default_storage.save(EmailAttachment.name, EmailAttachment)
        else:
            file_name2 = None

        if AddAttachment:
            file_nameadd = default_storage.save(AddAttachment.name, AddAttachment)
        else:
            file_nameadd = None

        if AdvanceAttachment:
            file_nameadv = default_storage.save(AdvanceAttachment.name, AdvanceAttachment)
        else:
            file_nameadv = None

        # Convert date strings to date objects
        FromDate = datetime.strptime(FromDate, '%Y-%m-%d').date() if FromDate else timezone.now().date()
        ToDate = datetime.strptime(ToDate, '%Y-%m-%d').date() if ToDate else timezone.now().date()
        InvoiceDate = datetime.strptime(InvoiceDate, '%Y-%m-%d').date() if InvoiceDate else timezone.now().date()     

        vn1 = VendorParentModel(
            RaisedBy=RaisedBy,
            EnteredBy=EnteredBy,
            DTNumber=DTNumber,
            VendorClaimNumber=VendorClaimNumber,
            VendorExpenseDetail=VendorExpenseDetail,
            DateofCreation=DateofCreation,            
            ProjectName=proj,
            Subproject=subproject_title,
            VendorName=VendorName,
            TotalClaimAmount=TotalClaimAmount,
            InvoiceNumber=InvoiceNumber,
            Description=Description,
            InvoiceDate=InvoiceDate,
            FromDate=FromDate,
            ToDate=ToDate,
            Quantity=Quantity,
            Unit=Unit,
            Rate=Rate,
            AdditionalAmount=Amount,
            AdditionalField=Field,
            Approval=Approval,
            WorkOrder=WorkOrder,
            PurchaseOrder=PurchaseOrder,
            Currency=Currency,
            GST=GST,        
            Remarks=Remark,
            ToBeDeducted=ToBeDeducted,
            InvoiceAttachment=file_name,
            EmailAttachment=file_name2,
            AddApprovedBy=AddApprovedBy,
            AddField=AddField,
            AdvanceApprovedBy=AdvanceApprovedBy,
            AdvanceAmount=AdvanceAmount,
            AddAttachment=file_nameadd,
            AdvanceAttachment=file_nameadv
        )
        vn1.save()
        to_email= ['prabhakara@deducetech.com']    

        email_thread = threading.Thread(target=sendvendormailtoprabhu, 
                                        args=(to_email, VendorClaimNumber, RaisedBy))
        email_thread.start()

    return redirect('entereddatavendor')


@login_required
def entereddatavendor(request):
    user = request.user
    last_name = user.last_name
    first_name = user.first_name
    email = user.email

    # Filter vendor parent claim data raised by the current user
    vendorparentclaimdata = VendorParentModel.objects.filter(RaisedBy=first_name).order_by('-VendorClaimNumber')

    # Process each vendor record to add related status and project title
    for vendor in vendorparentclaimdata:
        # Retrieve the latest status
        vendor.status = vendor.vendorclaimstatus_set.order_by('-id').first()
        
      

    # Prepare the context for the template
    data = {
        'user': user,
        'vendorparentclaimdata': vendorparentclaimdata,
        'last_name': last_name,
        'email': email,
        'first_name': first_name,
    }

    # Render the template with the data
    return render(request, "dataenteredvendor.html", data)



@login_required
def overviewreport(request):

    user = request.user
    last_name = user.last_name
    first_name = user.first_name
    email = user.email
    parentclaimdata = VendorParentModel.objects.filter(RaisedBy=request.user.first_name) 
 
    projects = Project.objects.all()
    vendors = VendorDetailModel.objects.all() 
 
    data = {
        'user': user,    
        'parentclaimdata': parentclaimdata,
        'last_name':last_name,
        'email':email,
        'first_name':first_name, 
        'projects':projects,
        'vendors':vendors,               
    }
    return render(request, "overviewreport.html", data)

def showvendorclaim(request, VendorClaimNumber):
    user = request.user
    first_name = user.first_name
    last_name = user.last_name
    parentclaimdata = get_object_or_404(VendorParentModel, VendorClaimNumber=VendorClaimNumber)     
    is_rejected = parentclaimdata.vendorclaimstatus_set.filter(status='Rejected').exists()  
    comments = parentclaimdata.vendorclaimstatus_set.values_list('comments', flat=True).first()    
    vendors = VendorDetailModel.objects.all() 
    selected_vendor = parentclaimdata.VendorName
    projects = Project.objects.all()
    subprojects = Subproject.objects.all()
    selected_project_id = parentclaimdata.ProjectName  # Assuming this holds the project_id   
    selected_subproject_id = parentclaimdata.Subproject  # Assuming this holds the subproject_id
    claims = VendorParentModel.objects.all() 
    claims_data = [
        {
            'vendorName': claim.VendorName,
            'fromDate': claim.FromDate.strftime('%Y-%m-%d'),
            'toDate': claim.ToDate.strftime('%Y-%m-%d')
        }
        for claim in claims
    ] 
    data = {
        'user': user,
        'VendorClaimNumber': VendorClaimNumber,       
        'parentclaimdata': parentclaimdata,        
        'is_rejected': is_rejected,             
        'projects':projects,
        'subprojects':subprojects,
        'vendors':vendors,     
        'comments': comments,
        'first_name':first_name,
        'last_name':last_name,
        'selected_project':selected_project_id,
        'selectedsubproject':selected_subproject_id,
        'selected_vendor':selected_vendor,
        'claims_data': json.dumps(claims_data),
    }    
    return render(request, "savedformvendor.html", data)


def showvendordetails(request, VendorId):
    # Filter the vendor details based on VendorId
    data = VendorDetailModel.objects.filter(VendorId=VendorId)

  
    vendor_details = data.first()  # Get the first matching object
  
    context = {
            'vendor': vendor_details  # Pass the vendor object to the context
        }   

    return render(request, "savedformregistered.html", context)


def updatevendordetail(request, VendorId):
    claim = get_object_or_404(VendorDetailModel, VendorId=VendorId)
    
    if request.method == "POST":    
        user_groups = request.user.groups.values_list('name', flat=True)
    
        if user_groups:
            if user_groups[0] == 'Manager':
                if request.user.first_name == 'Sanjay MS':
                    EnteredBy = 'GPO'
                else:
                    EnteredBy = 'GPM'
            elif user_groups[0] == 'Manager':
                EnteredBy = 'GPM'
            elif user_groups[0] == 'Accounts':
                EnteredBy = 'HR'
            else:
                EnteredBy = user_groups[0]  # Get the first group name 

        VendorName = request.POST.get('VendorName')
        VendorEmail = request.POST.get('VendorEmail')
        VendorGST = request.POST.get('VendorGST')
        BankName = request.POST.get('BankName')
        AccountNumber = request.POST.get('AccountNumber')
        IFSCCode = request.POST.get('IFSCCode')
        PlotNumber = request.POST.get('PlotNumber')
        StreetName = request.POST.get('StreetName')
        Locality = request.POST.get('Locality')
        City = request.POST.get('City')
        Pincode = request.POST.get('Pincode')
        PanNumber = request.POST.get('PanNumber')
        State = request.POST.get('State')
        MobileNumber = request.POST.get('MobileNumber')
        Duration = request.POST.get('Duration')
        GSTCopy = request.FILES.get('GSTCopyNew')  
        MSMECopy = request.FILES.get('MSMECopyNew') 
        CancelledCheque = request.FILES.get('CancelledChequeNew') 
        PANCopy = request.FILES.get('PANCopyNew') 
        EmailCopy = request.FILES.get('EmailCopyNew') 
        ContractCopy = request.FILES.get('ContractCopyNew')       
          


        if GSTCopy:
            file_name = default_storage.save(GSTCopy.name, GSTCopy)
        else:
            file_name = claim.GSTCopy 

        if MSMECopy:
            file_name2 = default_storage.save(MSMECopy.name, MSMECopy)
        else:
            file_name2 = claim.MSMECopy 

        if CancelledCheque:
            file_nameadd = default_storage.save(CancelledCheque.name, CancelledCheque)
        else:
            file_nameadd = claim.CancelledCheque 

        if PANCopy:
            file_nameadv = default_storage.save(PANCopy.name, PANCopy)
        else:
            file_nameadv = claim.PANCopy  

        if EmailCopy:
            file_nameade = default_storage.save(EmailCopy.name, EmailCopy)
        else:       
            file_nameade = claim.EmailCopy  

        if ContractCopy:
            file_nameadc = default_storage.save(ContractCopy.name, ContractCopy)
        else:       
            file_nameadc = claim.ContractCopy       



        claim.EnteredBy = EnteredBy 
        claim.VendorName = VendorName 
        claim.EnteredBy = EnteredBy
        claim.VendorEmail = VendorEmail
        claim.VendorGST = VendorGST
        claim.BankName = BankName 
        claim.AccountNumber = AccountNumber
        claim.IFSCCode = IFSCCode
        claim.PlotNumber = PlotNumber
        claim.StreetName = StreetName
        claim.Locality = Locality
        claim.City = City
        claim.Pincode = Pincode
        claim.PanNumber = PanNumber
        claim.State = State
        claim.MobileNumber = MobileNumber 
        claim.Duration = Duration           
        claim.GSTCopy =  file_name           
        claim.MSMECopy = file_name2
        claim.CancelledCheque = file_nameadd
        claim.PANCopy = file_nameadv
        claim.EmailCopy = file_nameade
        claim.ContractCopy = file_nameadc      
        claim.save()             

    return redirect('vendorrecord')




def updaterecordvendor(request, VendorClaimNumber):
        claim = get_object_or_404(VendorParentModel, VendorClaimNumber=VendorClaimNumber)
    
        if request.method == "POST":
            # DateofCreation = datetime.strptime(request.POST.get('DateofCreation'), '%B %d, %Y').date()
            month_mapping = {
                            'Jan.': 'January',
                            'Feb.': 'February',
                            'Mar.': 'March',
                            'Apr.': 'April',
                            'May.': 'May',
                            'Jun.': 'June',
                            'Jul.': 'July',
                            'Aug.': 'August',
                            'Sep.': 'September',
                            'Oct.': 'October',
                            'Nov.': 'November',
                            'Dec.': 'December',
                        }

            raw_date = request.POST.get('DateofCreation') 
            for abbreviated, full in month_mapping.items():
                raw_date = raw_date.replace(abbreviated, full)     


            DateofCreation = datetime.now().date()

            project = request.POST.get('Project')
            subproject = request.POST.get('Subproject')
            VendorName = request.POST.get('VendorSelection')
            VendorExpenseDetail = request.POST.get('VendorExpenseDetail')
            TotalClaimAmount = request.POST.get('TotalClaimAmount')
            InvoiceNumber = request.POST.get('InvoiceNumber')
            InvoiceDate = request.POST.get('InvoiceDate')
            InvoiceAttachment = request.FILES.get('delete') 
            Description = request.POST.get('Description')  
            WorkOrder = request.POST.get('WorkOrder')
            PurchaseOrder = request.POST.get('PurchaseOrder') 
            EmailAttachment = request.FILES.get('EmailAttachmentNew') 
            FromDate = request.POST.get('FromDate')     
            ToDate = request.POST.get('ToDate')            
            Quantity = request.POST.get('Quantity')
            Unit = request.POST.get('Unit')
            Amount = request.POST.get('Amount')
            Field = request.POST.get('Field')         
            Currency = request.POST.get('Currency')
            Rate = request.POST.get('Rate')
            GST = request.POST.get('GSTPercentage')      
            Remark = request.POST.get('Remarks')        
            AddAttachment = request.FILES.get('AddAttachmentNew')
            AddField = request.POST.get('AddField') 
            AdvanceAmount = request.POST.get('AdvanceAmount')
            AdvanceAttachment = request.FILES.get('AdvanceAttachmentNew')
            ToBeDeducted = request.POST.get('ToBeDeducted')             


            if InvoiceAttachment:
                file_name = default_storage.save(InvoiceAttachment.name, InvoiceAttachment)
            else:
                file_name = claim.InvoiceAttachment 

            if EmailAttachment:
                file_name2 = default_storage.save(EmailAttachment.name, EmailAttachment)
            else:
                file_name2 = claim.EmailAttachment 

            if AddAttachment:
                file_nameadd = default_storage.save(AddAttachment.name, AddAttachment)
            else:
                file_nameadd = claim.AddAttachment 

            if AdvanceAttachment:
                file_nameadv = default_storage.save(AdvanceAttachment.name, AdvanceAttachment)
            else:
                file_nameadv = claim.AdvanceAttachment 

            if InvoiceDate:
                InvoiceDate = datetime.strptime(InvoiceDate, '%Y-%m-%d').date()
      

            claim.DateofCreation = DateofCreation   
            claim.ProjectName = project            
            claim.Subproject = subproject
            claim.VendorName = VendorName 
            claim.VendorExpenseDetail = VendorExpenseDetail 
            claim.Description = Description            
            claim.TotalClaimAmount = TotalClaimAmount
            claim.InvoiceNumber =  InvoiceNumber
            claim.InvoiceAttachment =  file_name             
            claim.InvoiceDate = InvoiceDate
            claim.EmailAttachment = file_name2
            claim.AddAttachment = file_nameadd
            claim.AdvanceAttachment = file_nameadv
            claim.FromDate = FromDate 
            claim.ToDate = ToDate    
            claim.Quantity = Quantity 
            claim.Unit = Unit 
            claim.AddField = AddField 
            claim.AdvanceAmount = AdvanceAmount 
            claim.AdditionalAmount = Amount 
            if WorkOrder:
                claim.WorkOrder = WorkOrder 
            else:
                claim.WorkOrder = None
            if PurchaseOrder:
                claim.PurchaseOrder = PurchaseOrder 
            else:
                claim.PurchaseOrder = None
            claim.Currency = Currency      
            claim.AdditionalField = Field
            claim.Rate = Rate 
            claim.GST = GST 
            claim.Remarks = Remark   
            claim.ToBeDeducted = ToBeDeducted   
            claim.save()             

            if FromDate:
                FromDate = datetime.strptime(FromDate, '%Y-%m-%d').date()
                FromDate = timezone.make_aware(datetime.combine(FromDate, datetime.min.time()))
            else:
                FromDate = timezone.now()

            if ToDate:
                ToDate = datetime.strptime(ToDate, '%Y-%m-%d').date()
                ToDate = timezone.make_aware(datetime.combine(ToDate, datetime.min.time()))
            else:
                ToDate = timezone.now()

               
            claim_status, created = VendorClaimStatus.objects.get_or_create(claim=claim)
            claim_status.status = "ReSubmitted" 
            claim_status.financestatus = "Pending"  

            claim_status.save()
            return redirect('entereddatavendor')


        context = {
            'ClaimNumber': VendorClaimNumber,     
            'Remarks': Remark,
        }
        
        messages.success(request, "Claim submitted successfully!")
        return render(request, "dataenteredvendor.html", context)
 


def financeviewvendor(request):
    vendorparentclaimdata = VendorParentModel.objects.filter(vendorclaimstatus_set__status='Approved').order_by('-VendorClaimNumber')
    all_groups = Group.objects.all()
    selected_group = request.GET.get('group')
    if selected_group == 'HR':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'GPM':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'GPO':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'Admin':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'IT':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'Finance':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    for vendor in vendorparentclaimdata:
        vendor.status = vendor.vendorclaimstatus_set.order_by('-id').first() 
    data = {        
        'vendorparentclaimdata': vendorparentclaimdata, 
        'all_groups':all_groups        
    }
    return render(request, "financeviewvendor.html", data)


def managerviewvendor(request):
    vendorparentclaimdata = VendorParentModel.objects.filter(
    Q(vendorclaimstatus_set__financestatus='Rejected') | Q(vendorclaimstatus_set__status=None)  | Q(vendorclaimstatus_set__status='ReSubmitted') ).order_by('-VendorClaimNumber')


    all_groups = Group.objects.all()
    selected_group = request.GET.get('group')
    if selected_group == 'HR':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'GPM':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'GPO':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'Admin':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'IT':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    elif selected_group == 'Finance':
        vendorparentclaimdata = vendorparentclaimdata.filter(EnteredBy=selected_group)
    for vendor in vendorparentclaimdata:
        vendor.status = vendor.vendorclaimstatus_set.order_by('-id').first() 

    
    data = {        
        'vendorparentclaimdata': vendorparentclaimdata, 
        'all_groups':all_groups,
             
    }
    return render(request, "managerviewvendor.html", data)


def replace_vendorbill_attachment(request, VendorClaimNumber):
    parentclaimdata = get_object_or_404(VendorParentModel, VendorClaimNumber=VendorClaimNumber)
    VendorClaimNumber = request.GET.get('VendorClaimNumber')

    if request.method == 'POST' and 'new_InvoiceAttachment' in request.FILES:
        # Delete the existing attachment
        if parentclaimdata.InvoiceAttachment:
            default_storage.delete(parentclaimdata.InvoiceAttachment.name)
            parentclaimdata.InvoiceAttachment.delete()

        # Save the new attachment
        new_bill_attachment =  request.FILES.get('new_InvoiceAttachment')
        parentclaimdata.InvoiceAttachment = new_bill_attachment
        parentclaimdata.save()

        return redirect('showvendorclaim', VendorClaimNumber=parentclaimdata.VendorClaimNumber)

    return render(request, 'replace_vendorbill_attachment.html', {'parentclaimdata': parentclaimdata})

def delete_vendorchild_form(request, child_claim_id):
    child_claim = get_object_or_404(VendorParentModel, id=child_claim_id)
    try:
       
        VendorParentModel.objects.filter(id=child_claim_id).delete()

        
        return redirect('showvendorclaim', ClaimNumber=child_claim.parent.VendorClaimNumber)
    except Exception as e:
        # Return an error response
        return JsonResponse({'error': f'Error: {e}'}, status=500)
    


def sendvendormailtotl(to_email, claim_number,status,comments,RaisedBy):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=claim_number)
    subject = f'Vendor Claim {status} - Claim Number: {claim_number}'     

    message = render_to_string('vendoremailtotl.html', {'claim': claim,'claim_number':claim_number,'RaisedBy':RaisedBy,'comments':comments,'status':status})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass 



def sendvendormailtoprabhu(to_email, claim_number,RaisedBy):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=claim_number)
    subject = f'Vendor Claim Number: {claim_number} Submitted By: {RaisedBy}'    

    message = render_to_string('vendoremailprabhu.html', {'claim': claim,'claim_number':claim_number,'RaisedBy':RaisedBy})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass 

def sendvendorrejectedmailtoprabhu(to_email, claim_number,financestatus,financecomments):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=claim_number)
    subject = f'Vendor Claim {financestatus} - Claim Number: {claim_number}'     

    message = render_to_string('vendorrejectedemailprabhu.html', {'claim': claim,'financestatus':financestatus,'claim_number':claim_number,'financecomments':financecomments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass

def sendvendormailtofinance(to_email, claim_number, status, comments):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=claim_number)
    subject = f'Vendor Claim {status} - Claim Number: {claim_number}'    

    message = render_to_string('vendoremailtofinance.html', {'claim': claim,'status':status,'claim_number':claim_number,'comments':comments})
    plain_message = strip_tags(message)
    from_email = 'expense@deducetech.in'

    if to_email:
        send_mail(subject, plain_message, from_email, to_email, html_message=message)
    else:     
        pass 

def managerreviewvendor(request, VendorClaimNumber):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=VendorClaimNumber)
    parentclaimdata = get_object_or_404(VendorParentModel, VendorClaimNumber=VendorClaimNumber)
    is_approved = parentclaimdata.vendorclaimstatus_set.filter(status='Approved') \
    .exclude(financestatus='Rejected').exists()
    user_email = User.objects.filter(first_name=claim.RaisedBy).values_list('email', flat=True).first()

    financecomments = claim.vendorclaimstatus_set.values_list('financecomments', flat=True).first()


    vendor_name = claim.VendorName
    vendor_detail = get_object_or_404(VendorDetailModel, VendorName=vendor_name)
    quantity = float(claim.Quantity) 
    rate = float(claim.Rate)         
    BasicAmount = quantity * rate 
    GST = claim.GST /100
    GSTAmount =  (BasicAmount * GST) 
    if request.method == 'POST':   
        comments = request.POST.get('comments')
        status = request.POST.get('status')      

        # Update or create ClaimStatus
        claim_status, created = VendorClaimStatus.objects.get_or_create(claim=claim)
        claim_status.status = status
        claim_status.comments = comments
    
        claim_status.save()

        # Update the claim's StatusDateAccounts
        claim.StatusDate = timezone.now().date()
        claim.save()  
       

        if status == 'Rejected':
            to_email=user_email
            email_thread = threading.Thread(target=sendvendormailtotl, 
                                        args=(to_email, VendorClaimNumber, status, comments,parentclaimdata.RaisedBy))
            email_thread.start()

        else:
            to_email = ['mahabaleshwar@deducetech.com'] 
            email_thread = threading.Thread(target=sendvendormailtofinance, 
                                            args=(to_email, VendorClaimNumber, status, comments))
            email_thread.start()       

        return redirect('managerviewvendor')
    
    context = {
        'claim': claim,
        'is_approved':is_approved,
        'parentclaimdata': parentclaimdata,
        'vendor_detail': vendor_detail,
        'BasicAmount':BasicAmount,
        'GSTAmount':GSTAmount,
        'financecommentsvendor':financecomments 

    }
    return render(request, "managerreviewvendor.html", context)
    

def financereviewvendor(request, VendorClaimNumber):
    claim = get_object_or_404(VendorParentModel, VendorClaimNumber=VendorClaimNumber)
    parentclaimdata = get_object_or_404(VendorParentModel, VendorClaimNumber=VendorClaimNumber)   
    is_approved = parentclaimdata.vendorclaimstatus_set.filter(financestatus='Approved').exists()  
    vendor_name = claim.VendorName
    vendor_detail = get_object_or_404(VendorDetailModel, VendorName=vendor_name)
    quantity = float(claim.Quantity) 
    rate = float(claim.Rate)         
    BasicAmount = quantity * rate 
    GST = claim.GST /100
    GSTAmount =  (BasicAmount * GST)
    if request.method == 'POST':   
        financecomments = request.POST.get('financecomments')
        financestatus = request.POST.get('financestatus')   
        # Update or create ClaimStatus
        claim_status, created = VendorClaimStatus.objects.get_or_create(claim=claim)
        claim_status.financestatus = financestatus
        claim_status.financecomments = financecomments    
        claim_status.save()

        # Update the claim's StatusDateAccounts
        claim.StatusDateAccounts = timezone.now().date()
        claim.save() 

        to_email = ['prabhakara@deducetech.com']  

        if financestatus == 'Rejected':
            email_thread = threading.Thread(target=sendvendorrejectedmailtoprabhu, 
                                        args=(to_email, VendorClaimNumber, financestatus, financecomments))
            email_thread.start()            

        return redirect('financeviewvendor')
    
    context = {
        'claim': claim,
        'parentclaimdata': parentclaimdata,           
        'is_approved':is_approved,
        'vendor_detail': vendor_detail,
        'BasicAmount':BasicAmount,
        'GSTAmount':GSTAmount    

    }

    return render(request, "financereviewvendor.html", context)



from openpyxl import Workbook

def safe_float(value):
    try:
        return float(value) if value not in [None, ''] else 0.0
    except ValueError:
        return 0.0

def downloadoverviewreport(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        claims = data.get('claims', [])

        # Create a new workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Claims Data"

        # Header Row
        headers = [
            "ClaimNumber", "RaisedBy", "VendorName", "ProjectName",
            "DateofInvoice", "InvoicePeriod", "InvoiceAmount", "GST",
            "Tax", "TotalAmount"
        ]
        ws.append(headers)

        totalInvoiceAmount = 0
        totalTax = 0
        totalAmount = 0

        # Data Rows
        for claim in claims:
            row = [
                claim.get("ClaimNumber"),
                claim.get("RaisedBy"),
                claim.get("VendorName"),
                claim.get("ProjectName"),
                claim.get("DateofInvoice"),
                claim.get("InvoicePeriod"),
                safe_float(claim.get("InvoiceAmount")),
                safe_float(claim.get("GST")),
                safe_float(claim.get("Tax")),
                safe_float(claim.get("TotalAmount"))
            ]
            ws.append(row)

            # Accumulate totals
            totalInvoiceAmount += safe_float(claim.get("InvoiceAmount"))
            totalTax += safe_float(claim.get("Tax"))
            totalAmount += safe_float(claim.get("TotalAmount"))

        # Only one Totals Row
        ws.append([
            "Total:",
            "",
            "",
            "",
            "",
            "",
            totalInvoiceAmount,
            "",
            totalTax,
            totalAmount
        ])

        # Save workbook to an in-memory file-like object
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Create an HTTP response with the in-memory file
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="VendorExpense.xlsx"'
        return response
    
def downloadporeport(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        claims = data.get('claims', [])

        # Create a new workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Claims Data"

        # Header Row
        headers = [
            "PONumber", "POReference", "VendorName", "PODate",
            "ApprovalFrom", "RequestedBy"
          
        ]
        ws.append(headers)

    
        for claim in claims:
            row = [
                claim.get("PONumber"),
                claim.get("POReference"),
                claim.get("VendorName"),
                claim.get("PODate"),
                claim.get("ApprovalFrom"),
                claim.get("RequestedBy"),
        
            ]
            ws.append(row)

  

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Create an HTTP response with the in-memory file
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="VendorExpense.xlsx"'
        return response


@login_required
def approvedclaimsvendor(request): 
    approvedclaims = VendorParentModel.objects.filter(vendorclaimstatus_set__financestatus='Approved').order_by('-VendorClaimNumber') 
    data = {
        'approvedclaims': approvedclaims,
     
    }
    return render(request, "approvedclaimsvendor.html", data)


@login_required
def approvedclaimsbymanagervendor(request): 
    approvedclaims = VendorParentModel.objects.filter(vendorclaimstatus_set__status='Approved').order_by('-VendorClaimNumber') 
    data = {
        'approvedclaims': approvedclaims,     
    }
    return render(request, "approvedclaimsbymanagervendor.html", data)



@login_required
def poform(request): 
    vendors = VendorDetailModel.objects.all() 
      
    data = {
        "vendors": vendors
    }
    return render(request,"poform.html",data)

import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import VendorDetailModel  # Adjust the import based on your app structure

from django.http import JsonResponse

def calculate_gst(amount, gst_percentage):
    try:
        # Convert inputs to float
        amount = float(amount)
        gst_percentage = float(gst_percentage)

        # Calculate GST
        gst_amount = (amount * gst_percentage) / 100
        return round(gst_amount, 2)  # Return the GST amount rounded to 2 decimal places
    except (ValueError, TypeError):
        return 0.0  # Return 0.0 if there's an error in conversion


from datetime import datetime
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import PODetailModel, POChildModel

@login_required
def save_po_record(request):
    if request.method == 'POST':
        # Capture main purchase order data
        vendor_name = request.POST.get('VendorSelection')  # Assuming this is the vendor name selected
        po_date = request.POST.get('PODate')
        PONumber = request.POST.get('PONumber')
        po_reference = request.POST.get('POReference')
        vendor_reference = request.POST.get('VendorReference')
        Terms = request.POST.get('terms')
        approval_from = request.POST.get('ApprovalFrom')
        ship_to = request.POST.get('ShipTo')
        po_email_copy = request.FILES.get('POEmailCopy')  # File upload
        requested_by = request.user  # Get the logged-in user

        # Generate unique PO number
        current_month = datetime.now().month
        if current_month >= 4:  # From April to December
            financial_year = f"{datetime.now().year}-{datetime.now().year + 1}"
        else:  # From January to March
            financial_year = f"{datetime.now().year - 1}-{datetime.now().year}"

        # Location-based PO code (example: "BNG" for Bangalore, "GGN" for Gurgaon)  

        if PONumber == "Bangalore":
            location_code = "BNG"
        elif PONumber == "Salem":
            location_code = "SLM"
        elif PONumber == "Karimnagar":
            location_code = "KMN"
        else:
            location_code = "GGN"

     
        # Retrieve the last PO for the location and financial year
        last_po = PODetailModel.objects.filter(
            PONumber__contains=f"{financial_year}-{location_code}"  # Combine location and financial year
        ).order_by('-id').first()


        # Default starting sequence number
        if last_po:
            # Extract the PONumber and split it to get the sequence number part (last part)
            last_po_number = last_po.PONumber
            sequence_number_str = last_po_number.split('-')[-1]  # Extract the sequence number part
            last_sequence = int(sequence_number_str)  # Convert it to integer
            sequence_number = last_sequence + 1  # Increment the sequence number
        else:
            # If no previous PO exists, start the sequence at 1 for the new financial year
            sequence_number = 1

        # Generate the new PO number with the incremented sequence number
        po_number_generated = f"PO-{financial_year}-{location_code}-{str(sequence_number).zfill(3)}"

        # Create the Purchase Order instance
        purchase_order = PODetailModel(
            VendorName=vendor_name,
            PODate=po_date,
            POReference=po_reference,
            Terms=Terms,
            VendorReference=vendor_reference,
            PONumber=po_number_generated,  # Use the generated PO number
            ApprovalFrom=approval_from,
            ShipTo=ship_to,
            POEmailCopy=po_email_copy,
            RequestedBy=requested_by
        )
        purchase_order.save()

        # Loop through the product fields
        product_count = 0
        while True:
            product_count += 1
            description = request.POST.get(f'Description{product_count}')
            if not description:  # Break if no more products
                break
            hsn_code = request.POST.get(f'HSNCode{product_count}')
            quantity = request.POST.get(f'Quantity{product_count}')
            unit = request.POST.get(f'Unit{product_count}')
            rate = request.POST.get(f'Rate{product_count}')
            gst_percentage = request.POST.get(f'GSTPercentage{product_count}')
            amount = request.POST.get(f'Amount{product_count}')
            total_amount = request.POST.get(f'TotalAmount{product_count}')  # Calculate or retrieve this
            gst_amount = (float(amount) * float(gst_percentage) / 100) if amount and gst_percentage else 0

            # Create and save each Product instance
            product = POChildModel(
                parent_po=purchase_order,
                Description=description,
                HSNCode=hsn_code,
                Quantity=quantity,
                Unit=unit,
                Rate=rate,
                GSTPercentage=gst_percentage,
                Amount=amount,
                TotalAmount=total_amount,
                GSTAmount=gst_amount
            )
            product.save()

        # Redirect to a view page or return a success message
        return redirect('view_po_record', po_id=purchase_order.id)  # Redirect to view page with PO ID

    return render(request, 'popdf.html')  # Render form page if not POST


def view_po_record(request, po_id):
    # Fetch the purchase order and related products
    purchase_order = PODetailModel.objects.get(id=po_id)
    products = POChildModel.objects.filter(parent_po=purchase_order)

    # Assuming `TotalAmount` is a field in POChildModel that holds the total amount for each product
    total_amount = sum(float(product.TotalAmount) for product in products)

    # Convert total_amount to an integer or round it as necessary
    total_amount_int = round(total_amount)

    context = {
        'purchase_order': purchase_order,
        'products': products,
        'total_amount_words': convert_to_words(total_amount_int)  # Convert total amount to words
    }

    return render(request, 'view_po_record.html', context)



def convert_to_words(num):
    num = int(num)  # <-- critical: strip any float/decimal (e.g. 271400.00 -> 271400)

    if num == 0:
        return "Zero"

    units = [
        '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
        'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
        'Seventeen', 'Eighteen', 'Nineteen'
    ]

    tens = [
        '', '', 'Twenty', 'Thirty', 'Forty', 'Fifty',
        'Sixty', 'Seventy', 'Eighty', 'Ninety'
    ]

    def two_digit_word(n):
        if n < 20:
            return units[n]
        return tens[n // 10] + (' ' + units[n % 10] if n % 10 != 0 else '')

    def three_digit_word(n):
        if n < 100:
            return two_digit_word(n)
        return (
            units[n // 100] + ' Hundred' +
            (' ' + two_digit_word(n % 100) if n % 100 != 0 else '')
        )

    result = []

    crore = num // 10000000
    if crore > 0:
        result.append(two_digit_word(crore) + ' Crore')
        num %= 10000000

    lakh = num // 100000
    if lakh > 0:
        result.append(two_digit_word(lakh) + ' Lakh')
        num %= 100000

    thousand = num // 1000
    if thousand > 0:
        result.append(two_digit_word(thousand) + ' Thousand')
        num %= 1000

    if num > 0:
        result.append(three_digit_word(num))

    return ' '.join(result).strip()




from decimal import Decimal, ROUND_HALF_UP

@login_required
def update_po_record(request, po_id):
    # Fetch the purchase order using get_object_or_404 for better error handling
    purchase_order = get_object_or_404(PODetailModel, id=po_id)

    if request.method == 'POST':
        # Update main purchase order fields
        purchase_order.VendorName = request.POST.get('VendorName')
        purchase_order.POReference = request.POST.get('POReference')
        purchase_order.Terms = request.POST.get('terms')        
        purchase_order.VendorReference = request.POST.get('VendorReference')
        purchase_order.PODate = request.POST.get('PODate') 
        purchase_order.ApprovalFrom = request.POST.get('ApprovalFrom')
        purchase_order.ShipTo = request.POST.get('ShipTo')

        # Handle file upload if present
        if request.FILES.get('POEmailCopy'):
            purchase_order.POEmailCopy = request.FILES.get('POEmailCopy')

        purchase_order.save()

        # Clear existing child records
        POChildModel.objects.filter(parent_po=purchase_order).delete()

        # Initialize totals
        total_amount_sum = 0  # Total of amounts excluding GST
        total_amount_total = 0  # Total of amounts including GST
        total_gst_sum = 0

        vendor_name = purchase_order.VendorName  # Get the vendor name from the purchase order
        vendor = VendorDetailModel.objects.filter(VendorName=vendor_name).first()

        address_mapping = {
            "Bangalore": "Bellissimo Ventures Private Limited (Deduce Technologies®), Brigade Software Park (BSP), 6th Floor, 27th Cross Road, BSK II Stage, Banashankari, Bengaluru, Karnataka 560070, GST Number: 29AAHCB5498H1Z4, PAN: AAHCB5498H",
            "Gurugram": "Bellissimo Ventures Private Limited (Deduce Technologies®), D-1103, The Light House, Town Square, Sector- 82, Vatika India Next, Gurugram, Haryana- 122004, GST Number: 06AAHCB5498H1ZC",
            "Srinagar": "Bellissimo Ventures Private Limited (Deduce Technologies®), Town Square, Gogji Bagh, 2nd Floor, Srinagar, Kashmir – 190008",
            "Salem": "Bellissimo Ventures Private Limited (Deduce Technologies®), ELCO-SEZ IT Park ,P424+76G Dalmiya colony, Jagir Ammapalayam, Vellakalpatti, Salem, Tamil Nadu 636012, GST Number: 33AAHCB5498H1ZF, PAN: AAHCB5498H",
            "Karimnagar":"Bellissimo Ventures Private Limited (Deduce Technologies®), 4th Floor, IT Tower, Street Road, Sircilla Bypass Road, Karimnagar , Telangana - 505001, GST Number : 36AAHCB5498H1Z9"
        }

        # Get the address based on ShipTo
        ShipTo = address_mapping.get(purchase_order.ShipTo, "Default Address")

        # Process products from the form
        product_count = 0
        while True:
            product_count += 1
            product_id = request.POST.get(f'product_id{product_count}')
            description = request.POST.get(f'Description{product_count}')

            if not description:  # Stop if no description is provided
                break
            
            # Get the form data for the product, making sure to round to two decimals where needed
            quantity = Decimal(request.POST.get(f'Quantity{product_count}', 0)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            rate = Decimal(request.POST.get(f'Rate{product_count}', 0)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            gst_percentage = Decimal(request.POST.get(f'GSTPercentage{product_count}', 0)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            amount = Decimal(request.POST.get(f'Amount{product_count}', 0)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            
            # Create a new product
            product = POChildModel(
                parent_po=purchase_order,
                Description=description,
                HSNCode=request.POST.get(f'HSNCode{product_count}'),
                Quantity=quantity,
                Unit=request.POST.get(f'Unit{product_count}'),
                Rate=rate,
                GSTPercentage=gst_percentage,
                Amount=amount,
            )

            gst_amount = amount * (gst_percentage / 100)
            total_amount = amount + gst_amount

            # Ensure that totals are rounded to 2 decimal places
            total_amount = total_amount.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            gst_amount = gst_amount.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            
            product.TotalAmount = total_amount  # Assuming you have a field for TotalAmount
            product.GSTAmount = gst_amount  # Assuming you have a field for GSTAmount
            
            # Save the new product
            product.save()

            # Update totals
            total_amount_sum += amount
            total_amount_total += total_amount
            total_gst_sum += gst_amount

        # Prepare the context data to pass to the template
        context = {
            'POReference': purchase_order.POReference,
            'PONumber': purchase_order.PONumber,
            'ShipTo': ShipTo,
            'Terms': purchase_order.Terms,
            'VendorReference': purchase_order.VendorReference,
            'PODate': purchase_order.PODate,
            'ApprovalFrom': purchase_order.ApprovalFrom,
            'emailCopyPath': purchase_order.POEmailCopy.url if purchase_order.POEmailCopy else '',
            'TotalAmountWords': convert_to_words(int(total_amount_sum)),  # Sum of amounts in words
            'totalAmountSum': total_amount_sum.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),  # Total amount (excluding GST)
            'totalAmountTotal': total_amount_total.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
            'total_gst_sum': total_gst_sum.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),  
    
            'totalAmountTotalWords': convert_to_words(round(total_amount_total)).title(),  # Convert to proper case

            'childForms': POChildModel.objects.filter(parent_po=purchase_order),  # Get updated child forms
            'vendor': vendor,
        }

        return render(request, 'popdf.html', context)  # Render template with the updated details

    # If not a POST request, render the form with existing data
    return render(request, 'popdf.html', {
        'purchase_order': purchase_order,
        'products': POChildModel.objects.filter(parent_po=purchase_order),
    })



def get_vendor_details(request, VendorName):
    vendor = VendorDetailModel.objects.get(VendorName=VendorName)
    data = {
        'VendorEmail': vendor.VendorEmail,
        'VendorGST': vendor.VendorGST,
        'BankName': vendor.BankName,
        'AccountNumber': vendor.AccountNumber,
        'IFSCCode': vendor.IFSCCode,
        'PlotNumber': vendor.PlotNumber,
        'StreetName': vendor.StreetName,
        'Locality': vendor.Locality,
        'City': vendor.City,
        'Pincode': vendor.Pincode,
        'State': vendor.State,
        'MobileNumber': vendor.MobileNumber,
        'PanNumber': vendor.PanNumber,
    }
    return JsonResponse(data)
    


def poreport(request):
    user = request.user.first_name
    data = PODetailModel.objects.all()

    vendors = VendorDetailModel.objects.all()
    projects = Project.objects.all()

    context ={
        'data':data,
        'vendors':vendors,
        'projects':projects
    }
    return render(request,"poreport.html",context)

def showpos(request): 
    data = PODetailModel.objects.all()
    vendors = VendorDetailModel.objects.all()
    context ={
        'data':data,
        'vendors':vendors       
    }
    return render(request,"showpos.html",context)


from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, get_object_or_404
from .models import PODetailModel, POChildModel, VendorDetailModel
from decimal import Decimal

from decimal import Decimal, ROUND_HALF_UP

def poproducts(request, PONumber):
    # Fetch the parent PO (Purchase Order) details
    parentpodata = get_object_or_404(PODetailModel, PONumber=PONumber)

    # Fetch all child records (products or line items) for the given PO
    childpodata = POChildModel.objects.filter(parent_po=parentpodata)

    # Get vendor details based on the vendor name in the parent PO
    vendor_name = parentpodata.VendorName
    vendor = VendorDetailModel.objects.filter(VendorName=vendor_name).first()

    # Define the address mapping based on ShipTo
    address_mapping = {
        "Bangalore": "Bellissimo Ventures Private Limited (Deduce Technologies®), Brigade Software Park (BSP), 6th Floor, 27th Cross Road, BSK II Stage, Banashankari, Bengaluru, Karnataka 560070, GST Number: 29AAHCB5498H1Z4, PAN: AAHCB5498H",
        "Gurugram": "Bellissimo Ventures Private Limited (Deduce Technologies®), D-1103, The Light House, Town Square, Sector- 82, Vatika India Next, Gurugram, Haryana- 122004, GST Number: 06AAHCB5498H1ZC",
        "Srinagar": "Bellissimo Ventures Private Limited (Deduce Technologies®), Town Square, Gogji Bagh, 2nd Floor, Srinagar, Kashmir – 190008",
        "Salem": "Bellissimo Ventures Private Limited (Deduce Technologies®), ELCO-SEZ IT Park ,P424+76G Dalmiya colony, Jagir Ammapalayam, Vellakalpatti, Salem, Tamil Nadu 636012, GST Number: 33AAHCB5498H1ZF, PAN: AAHCB5498H",
        "Karimnagar":"Bellissimo Ventures Private Limited (Deduce Technologies®), 4th Floor, IT Tower, Street Road, Sircilla Bypass Road, Karimnagar , Telangana - 505001, GST Number : 36AAHCB5498H1Z9" 
    }
    # Get the ShipTo address from the mapping
    ShipTo = address_mapping.get(parentpodata.ShipTo, "Default Address")

    # Initialize cumulative totals
    total_amount_sum = Decimal('0')
    total_amount_total = Decimal('0')
    total_gst_sum = Decimal('0')

    # Process each product (child) and accumulate the totals
    for child in childpodata:
        # Convert the necessary fields to Decimal for calculation
        quantity = Decimal(child.Quantity)
        rate = Decimal(child.Rate)
        gst_percentage = Decimal(child.GSTPercentage)
        amount = Decimal(child.Amount)

        # Calculate the GST and total amounts for the current product
        gst_amount = amount * (gst_percentage / 100)
        total_amount = amount + gst_amount

     

    # Prepare context to pass to the template
    context = {
        'parentpodata': parentpodata,
        'childpodata': childpodata,  # All child records for the PO
        'ShipTo': ShipTo,
        'TotalAmountWords': parentpodata.totalAmountTotalWords,  # Sum of amounts in words
        'totalAmountSum': parentpodata.totalAmountSum,  # Total amount (excluding GST)
        'totalAmountTotal': parentpodata.totalAmountTotal,
        'total_gst_sum': parentpodata.total_gst_sum,
        'totalAmountTotalWords': parentpodata.totalAmountTotalWords,  # Convert total amount to words
        'vendor': vendor,  # Vendor details
    }

    # Render the template with the context
    return render(request, "poproducts.html", context)




from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import PODetailModel, POChildModel

from datetime import datetime

month_mapping = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}

def update_polast(request, PONumber):
    print(f"Received request for PO ID: {PONumber}")

    # Fetch the PO detail and child PO details
    po_detail = get_object_or_404(PODetailModel, PONumber=PONumber)
    po_children = POChildModel.objects.filter(parent_po=po_detail)

    if request.method == 'POST':     

        try:
            # Update the main PO fields with the new data (or keep old if not provided)
            po_detail.POReference = request.POST.get('POReference', po_detail.POReference)
            po_detail.VendorReference = request.POST.get('VendorReference', po_detail.VendorReference)
            po_detail.PODate = request.POST.get('PODate', po_detail.PODate)
            po_detail.Terms = request.POST.get('Terms', po_detail.Terms)
            po_detail.totalAmountSum = request.POST.get('totalAmountSum', po_detail.totalAmountSum)
            po_detail.total_gst_sum = request.POST.get('totalGSTValue', po_detail.total_gst_sum)
            po_detail.totalAmountTotal = request.POST.get('totalAmount', po_detail.totalAmountTotal)
            po_detail.totalAmountTotalWords = request.POST.get('totalValueWords', po_detail.totalAmountTotalWords)
        

            # If PODate is updated, convert it to a date format
            if po_detail.PODate:
                try:
                    po_date_str = po_detail.PODate.replace(',', '').strip()  # Remove commas and trailing spaces
                    if po_date_str:  # Ensure it's not an empty string
                        month_str = po_date_str.split()[0].strip('.')  # 'Oct.' -> 'Oct'
                        month_num = month_mapping.get(month_str, None)

                        if not month_num:
                            raise ValueError(f"Invalid month abbreviation: {month_str}")

                        # Reconstruct the date string in the format '%Y-%m-%d'
                        date_str = f"{po_date_str.split()[2]}-{month_num}-{po_date_str.split()[1]}"
                        po_detail.PODate = datetime.strptime(date_str, '%Y-%m-%d').date()

                except Exception as e:                
                    return redirect('update_polast', PONumber=PONumber)

            po_detail.save()

        except Exception as e:          
            return redirect('update_polast', PONumber=PONumber)

        # Update child PO records
        for child in po_children:
            try:
                description = request.POST.get(f'description_{child.id}', child.Description)
                if not description:
                    raise ValueError(f"Description for child PO {child.id} is required.")
                
                child.Description = description
                child.HSNCode = request.POST.get(f'hsn_code_{child.id}', child.HSNCode)
                child.Quantity = request.POST.get(f'quantity_{child.id}', child.Quantity)
                child.Rate = request.POST.get(f'unit_rate_{child.id}', child.Rate)
                child.Amount = request.POST.get(f'basic_value_{child.id}', child.Amount)
                child.GSTPercentage = request.POST.get(f'gst_rate_{child.id}', child.GSTPercentage)
                child.GSTAmount = request.POST.get(f'gst_amount_{child.id}', child.GSTAmount)
                child.TotalAmount = request.POST.get(f'total_amount_{child.id}', child.TotalAmount)

                child.save()
            except Exception as e:               
                return redirect('poproducts', PONumber=PONumber)

       
        return redirect('poproducts', PONumber=PONumber)

    # Render the form and pass current PO and child PO details to the template
    return render(request, "showpos.html", {'po_detail': po_detail, 'po_children': po_children})

def generatereportvendor(request):  
    parentclaimdata = VendorParentModel.objects.filter(vendorclaimstatus_set__status='Approved').order_by('VendorClaimNumber') 
    projects = Project.objects.all()
    vendors = VendorDetailModel.objects.all()   
    data = {
        'parentclaimdata': parentclaimdata, 
        'projects':projects,
        'vendors':vendors

    }
    return render(request, "generatereportvendor.html",data)



def downloadvouchersvendor(request):
    if request.method == 'POST':
        try:
            # Ensure request is JSON
            try:
                claims_data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return HttpResponse("Invalid JSON", status=400)

            claims = claims_data.get('claims', [])
            if not claims:
                return HttpResponse("No claims provided", status=400)

            # Prepare the ZIP file in memory
            zip_buffer = BytesIO()

            # Create a ZIP file in memory
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for claim in claims:
                    # Get VendorClaimNumber and RaisedBy from the data sent by the frontend
                    vendor_claim_number = claim.get('vendorClaimNumber')
                    raised_by = claim.get('raisedBy')

                    if vendor_claim_number:
                        # Query the database to get the VendorParentModel object for this VendorClaimNumber
                        try:
                            vendor_claim = VendorParentModel.objects.get(VendorClaimNumber=vendor_claim_number)
                        except VendorParentModel.DoesNotExist:
                            # Skip if no matching claim is found
                            continue

                        # Create a folder structure within the zip with format ClaimNumber-RaisedBy
                        folder_name = f"{vendor_claim_number}-{raised_by}"

                        # Collect the attachment files
                        attachments = [
                            vendor_claim.InvoiceAttachment,
                            vendor_claim.EmailAttachment,
                            vendor_claim.AddAttachment,
                            vendor_claim.AdvanceAttachment
                        ]

                        # Add attachments to the zip under the folder
                        for attachment in attachments:
                            if attachment and os.path.exists(attachment.path):  # Ensure file exists
                                file_name = os.path.basename(attachment.path)  # Get the file name
                                file_path_in_zip = os.path.join(folder_name, file_name)
                                zip_file.write(attachment.path, arcname=file_path_in_zip)  # Write file to zip

            # Finalize the ZIP file in memory
            zip_buffer.seek(0)

            # Serve the zip file as a response to be downloaded
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="Vouchers_{vendor_claim_number}.zip"'
            return response

        except Exception as e:
            # Provide detailed error message
            return HttpResponse(f"Error processing request: {str(e)}", status=500)

    return HttpResponse(status=400)  # Only allow POST method
     
     

    
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.storage import default_storage
from datetime import datetime
from io import BytesIO
from django.core.files.base import ContentFile

import os
from django.db import transaction

@login_required
def autouploadclaim(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        file_name = default_storage.save(excel_file.name, excel_file)
        file_path = default_storage.path(file_name)

        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active

        errors = []
        success_count = 0

        for row_no, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or not row[0]:          # skip empty rows
                continue
            try:
                with transaction.atomic():
                    last_name = str(row[0]).strip()
                    claim_number = row[1]
                    department = row[2]
                    manager = row[3]
                    project = row[4]
                    subproject = row[5]
                    expense_details = row[6]
                    receipt_number = row[7]
                    receipt_date = row[8]
                    claim_amount = row[9]
                    totalclaimamount = row[10]
                    remarks = row[11]
                    user_email = row[13] if len(row) > 13 else None

                    user = User.objects.get(last_name=last_name)
                    status_date = datetime.now().strftime('%Y-%m-%d')

                    parent_model = ParentModel.objects.filter(ClaimNumber=claim_number).first()
                    if parent_model:
                        parent_model.Manager = manager
                        parent_model.Department = department
                        parent_model.Project = project
                        parent_model.Subproject = subproject
                        parent_model.ExpenseDetails = expense_details
                        parent_model.DTNumber = last_name
                        parent_model.DeduceEmailAddress = user_email
                        parent_model.StatusDate = status_date
                        parent_model.excelfile = file_name      # <-- attach the excel
                        parent_model.save()
                    else:
                        parent_model = ParentModel.objects.create(
                            user=user,
                            Manager=manager,
                            ClaimNumber=claim_number,
                            Department=department,
                            Project=project,
                            Subproject=subproject,
                            ExpenseDetails=expense_details,
                            DTNumber=last_name,
                            DeduceEmailAddress=user_email,
                            StatusDate=status_date,
                            DateofCreation=status_date,         # add if required in your model
                            excelfile=file_name,                # <-- attach the excel
                        )

                    child_model = ChildModel.objects.filter(
                        ReceiptNumber=receipt_number, parent=parent_model
                    ).first()
                    if child_model:
                        child_model.ReceiptDate = receipt_date
                        child_model.ClaimAmount = claim_amount
                        child_model.TotalClaimAmount = totalclaimamount
                        child_model.Remarks = remarks
                        child_model.save()
                    else:
                        pdf_filename = f"{last_name}.pdf"
                        pdf_file = generate_pdf(last_name, totalclaimamount, pdf_filename)
                        billattachment = default_storage.save(pdf_filename, pdf_file)
                        ChildModel.objects.create(
                            user=user,
                            parent=parent_model,
                            ReceiptNumber=receipt_number,
                            ReceiptDate=receipt_date,
                            ClaimAmount=claim_amount,
                            TotalClaimAmount=totalclaimamount,
                            Remarks=remarks,
                            BillAttachment=billattachment,
                        )

                    if not ClaimStatus.objects.filter(claim=parent_model).exists():
                        ClaimStatus.objects.create(
                            claim=parent_model,
                            status='Approved',
                            accountstatus='',
                            financestatus='',
                            accountselect='',
                            managementselect='',
                            managementstatus='',
                            approvedby='Bharath S R',
                        )
                    success_count += 1

            except User.DoesNotExist:
                errors.append(f"Row {row_no}: user '{row[0]}' not found")
            except Exception as e:
                errors.append(f"Row {row_no}: {type(e).__name__} - {e}")

        msg = f"{success_count} row(s) processed."
        if errors:
            msg += " Errors: " + " | ".join(errors)
        return HttpResponse(msg, status=200 if success_count else 400)

    return render(request, 'autouploadclaim.html')


# Function to generate the PDF
def generate_pdf(last_name, totalclaimamount, pdf_filename):
    buffer = BytesIO()  # In-memory buffer to hold the PDF
    
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter  # Standard letter size (8.5 x 11 inches)
    
    c.setFont("Helvetica", 12)    
    # Add the content for the PDF
    c.drawString(100, height - 100, f"Walk & Verify Claim for {last_name}")
    c.drawString(100, height - 120, f"Total Claim Amount: Rs.{totalclaimamount}")
    
    c.showPage()
    c.save()    
    buffer.seek(0)    
    # Convert the buffer to a file-like object and save it
    pdf_file = ContentFile(buffer.read())
    buffer.close()
    
    return pdf_file


def get_subprojects(request):
    # Check if the request is an AJAX request using the X-Requested-With header
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "GET":
        project_id = request.GET.get('project_id')
        subprojects = []

        # Check if project_id is provided and valid
        if project_id:
            try:
                # Get the project by project_id
                project = Project.objects.get(id=project_id)  # Make sure we are using the 'id' field
                
                # Retrieve all subprojects related to the selected project
                subprojects = project.subprojects.all()  # Make sure subprojects are related

                # Prepare the data for JSON response
                subprojects_data = [
                    {'subproject_id': subproject.subproject_id, 'subproject_title': subproject.subproject_title}
                    for subproject in subprojects
                ]

                return JsonResponse({'subprojects': subprojects_data})

            except Project.DoesNotExist:

                return JsonResponse({'error': 'Project not found'}, status=404)

        return JsonResponse({'error': 'No project_id provided'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def fieldclaims(request):
    claims = ParentModel.objects.filter(Q(skipmanager='Anil Kumar') | Q(skipmanager='Bharath S R'))
    user_count_list=[]
    total_claim_amounts = []

    for claim in claims:     
        child_claim = ChildModel.objects.filter(parent=claim).first()
        total_claim_amount = child_claim.TotalClaimAmount if child_claim else 0
        total_claim_amounts.append((claim.ClaimNumber, total_claim_amount))

    user_count_list.append({'claims': claims, 'total_claim_amounts': total_claim_amounts})

    data = {
        'claims': claims,
        'total_claim_amounts': total_claim_amounts,     
    }

    return render(request, "fieldclaims.html", data)


import os
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.contrib import messages
from .models import ExcelFile


def upload_excel(request):
    if request.method == 'POST':
        file_date_str = request.POST.get('file_date')
        description   = request.POST.get('description', '')
        uploaded_file = request.FILES.get('file')

        # ---- VALIDATION ----
        if not uploaded_file or not file_date_str:
            messages.error(request, 'Please provide both a file and a date.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ['.xls', '.xlsx']:
            messages.error(request, 'Only .xls or .xlsx files are allowed.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        try:
            file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # ---- SAVE ----
        try:
            obj = ExcelFile.objects.create(
                file=uploaded_file,
                file_date=file_date,
                description=description,
            )
            print("SAVED id:", obj.id, "| path:", obj.file.path,
                  "| on_disk:", os.path.exists(obj.file.path))
            messages.success(request, f'Uploaded "{uploaded_file.name}" for {file_date}.')
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Save failed: {e}')

        # Redirect back to the page you came from (works for any page hosting the form)
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # GET → nothing to do
    return redirect(request.META.get('HTTP_REFERER', '/'))


def download_file(request, file_id):
    obj = get_object_or_404(ExcelFile, id=file_id)
    if not os.path.exists(obj.file.path):
        return HttpResponse('File not found on server.', status=404)
    return FileResponse(
        open(obj.file.path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(obj.file.path),
    )

from datetime import datetime
from django.http import JsonResponse
from django.urls import reverse
from .models import ExcelFile


def search_excel_by_date(request):
    date_str = (request.GET.get('date') or '').strip()
    if not date_str:
        return JsonResponse(
            {'success': False, 'message': 'Please provide a date.'},
            status=400,
        )

    try:
        target = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse(
            {'success': False, 'message': 'Invalid date format.'},
            status=400,
        )

    qs = ExcelFile.objects.filter(file_date=target).order_by('-uploaded_at')

    files = []
    for f in qs:
        files.append({
            'id':          f.id,
            'file_date':   f.file_date.strftime('%Y-%m-%d'),
            'file_name':   f.file.name.split('/')[-1],   # strip folder path
            'description': f.description or '',
            'uploaded_at': f.uploaded_at.strftime('%Y-%m-%d %H:%M'),
            'download_url': reverse('download_file', args=[f.id]),
        })

    return JsonResponse({'success': True, 'files': files})


import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import ClaimSplit, ClaimStatus  # adjust import path


VALID_FINANCE_STATUSES = ("Approved", "Hold", "Rejected")
MAX_AMOUNT = Decimal("99999999.99")
ZERO = Decimal("0.00")


# ---------------------------------------------------------------------------
# Parsing / validation helpers
# ---------------------------------------------------------------------------

def _is_blank(value):
    return value is None or str(value).strip() == ""


def _to_decimal(raw, label):
    """Convert raw input to a Decimal with 2 places. Raises ValueError."""
    try:
        value = Decimal(str(raw).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid amount for " + label + ".")
    if not value.is_finite() or value < 0 or value > MAX_AMOUNT:
        raise ValueError("Amount out of range for " + label + ".")
    return value


def _parse_amount(data, *keys, default=ZERO):
    """
    Try each key in order; the first non-blank one wins.
    Missing / blank -> `default` (pass default=None to detect "not sent").
    """
    for key in keys:
        raw = data.get(key)
        if not _is_blank(raw):
            return _to_decimal(raw, key.replace("_", " "))
    return default


def _parse_paid_date(data):
    """Accept 'paid_date' or 'paidon'. Returns a date or None."""
    raw = data.get("paid_date")
    if _is_blank(raw):
        raw = data.get("paidon")
    raw = str(raw or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValueError("Invalid paid date.")


def _clean_text(value, max_len):
    return str(value or "").strip()[:max_len]


def _parse_finance_row(data):
    """
    Validate the payload from the page.
    Raises ValueError with a user-facing message.
    Returns a dict keyed by model field names.
    """
    status = str(data.get("finance_status") or "").strip()
    if status not in VALID_FINANCE_STATUSES:
        raise ValueError("Choose Approved, Hold or Rejected.")

    remarks = str(data.get("finance_remarks") or "").strip()
    if len(remarks.split()) > 20:
        raise ValueError("Finance remarks can be at most 20 words.")

    return {
        "financestatus": status,
        "financecomments": remarks,
        "holdamountfin": _parse_amount(data, "hold_amount_fin", "holdamountfin"),
        "originalholdfin": _parse_amount(data, "original_hold_amount_fin", default=None),
        "releasehold": _parse_amount(data, "hold_release_amount"),
        # None means "page did not send it"; the rules function then falls back to HR's value.
        "rejectamountfin": _parse_amount(data, "rejected_amount", default=None),
        "payableamount": _parse_amount(data, "payable_amount"),
        "paid": _parse_amount(data, "paid_amount"),
        "paidon": _parse_paid_date(data),
        "NatureOfExpense": _clean_text(data.get("nature_of_expense"), 120),
        "AccountingLocation": _clean_text(data.get("accounting_location"), 120),
        "WorkingLocation": _clean_text(data.get("working_location"), 120),
    }


def _apply_business_rules(values, claim_status):
    """
    Server-side rules. Returns an error string, or None if everything is fine.

    - Hold release cannot exceed the HR hold amount (Approved / Hold).
    - Rejected status forces the hold release to 0.
    - RejectedAmt is the value typed on the page. Only when none was sent
      does it fall back to the HR rejected amount.
    """
    status = values["financestatus"]
    hr_hold = claim_status.holdamounthr or ZERO
    hr_rejected = claim_status.rejectamounthr or ZERO

    if values["rejectamountfin"] is None:
        values["rejectamountfin"] = Decimal(str(hr_rejected)).quantize(Decimal("0.01"))

    if status in ("Approved", "Hold"):
        if values["releasehold"] > hr_hold:
            return "Hold release cannot exceed HR hold amount (" + str(hr_hold) + ")."
    else:  # Rejected
        values["releasehold"] = ZERO

    return None


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

@login_required
@require_POST
def save_finance_claim(request, claim_number):
    try:
        data = json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON request."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"ok": False, "error": "Invalid request data."}, status=400)

    try:
        values = _parse_finance_row(data)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    with transaction.atomic():
        claim_status = (
            ClaimStatus.objects
            .select_for_update()
            .select_related("claim")
            .filter(claim__ClaimNumber=claim_number)
            .order_by("id")
            .first()
        )
        if claim_status is None:
            return JsonResponse(
                {"ok": False, "error": "Claim not found: " + str(claim_number)},
                status=404,
            )

        error = _apply_business_rules(values, claim_status)
        if error:
            return JsonResponse({"ok": False, "error": error}, status=400)

        claim_status.financestatus = values["financestatus"]
        claim_status.financecomments = values["financecomments"]
        claim_status.holdamountfin = values["holdamountfin"]
        claim_status.releasehold = values["releasehold"]
        claim_status.rejectamountfin = values["rejectamountfin"]
        claim_status.payableamount = values["payableamount"]
        claim_status.paid = values["paid"]
        claim_status.paidon = values["paidon"]
        claim_status.NatureOfExpense = values["NatureOfExpense"]
        claim_status.AccountingLocation = values["AccountingLocation"]
        claim_status.WorkingLocation = values["WorkingLocation"]

        # The template reads `originalholdfin`. Save it only if the model has that field.
        if values["originalholdfin"] is not None and hasattr(claim_status, "originalholdfin"):
            claim_status.originalholdfin = values["originalholdfin"]

        claim_status.save()

    return JsonResponse(
        {
            "ok": True,
            "message": "Finance claim saved successfully.",
            "claim_number": str(claim_number),
        },
        status=200,
    )
# ---------------------------------------------------------------------------
# Save / create a split row
# ---------------------------------------------------------------------------

# Fields every record of a claim (ParentModel, ClaimStatus, all splits) should share.
from datetime import date
from decimal import Decimal, InvalidOperation

CLASSIFICATION_FIELDS = ("NatureOfExpense", "AccountingLocation", "WorkingLocation")
FINANCE_STATUSES = ("Approved", "Hold", "Rejected")


def _split_decimal(raw, label):
    """Blank -> 0. Must be a valid, non-negative number."""
    if raw in (None, ""):
        return Decimal("0.00")
    try:
        val = Decimal(str(raw)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a valid number.")
    if val < 0:
        raise ValueError(f"{label} cannot be negative.")
    return val


@login_required
@require_POST
def save_finance_split(request, claim_number):
    """
    Create or update one ClaimSplit.
    - split_id given and belongs to this claim -> UPDATE it.
    - otherwise                                 -> CREATE a new split.
    Payable amount is saved exactly as sent by the front end.
    Total claim amount (ClaimSplit.TotalClaimAmount) is saved exactly as sent;
    a new split starts at 0.
    Returns split_id and the display name  <ClaimNumber>_<n>.
    """
    try:
        data = json.loads(request.body or "{}")
        if not isinstance(data, dict):
            return JsonResponse({"ok": False, "error": "Invalid request data."}, status=400)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON request."}, status=400)

    raw_split_id = data.get("split_id")
    try:
        split_id = int(raw_split_id) if raw_split_id not in (None, "", "None") else None
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Invalid split id."}, status=400)

    # ---- read and validate the payload ----
    status = str(data.get("finance_status") or "").strip()
    if status not in FINANCE_STATUSES:
        return JsonResponse({"ok": False, "error": "Choose a finance status."}, status=400)

    try:
        hold_fin = _split_decimal(data.get("hold_amount_fin"), "Hold amount")
        release  = _split_decimal(data.get("hold_release_amount"), "Hold release amount")
        rejected = _split_decimal(data.get("rejected_amount"), "Rejected amount")
        paid     = _split_decimal(data.get("paid_amount"), "Paid amount")

        # Payable: whatever the front end sends (None only if the key is missing/blank)
        payable_posted = data.get("payable_amount")
        payable_in = (
            _split_decimal(payable_posted, "Payable amount")
            if payable_posted not in (None, "") else None
        )

        # Total claim amount of this split (None only if the key is missing/blank)
        total_posted = data.get("total_claim_amount")
        total_claim = (
            _split_decimal(total_posted, "Total claim amount")
            if total_posted not in (None, "") else None
        )

        # Approved amount of this split (None only if the key is missing/blank)
        approved_posted = data.get("approved_amount")
        approved_in = (
            _split_decimal(approved_posted, "Approved amount")
            if approved_posted not in (None, "") else None
        )
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    paid_raw = str(data.get("paid_date") or data.get("paidon") or "").strip()
    paid_on = None
    if paid_raw:
        try:
            paid_on = date.fromisoformat(paid_raw[:10])
        except ValueError:
            return JsonResponse({"ok": False, "error": "Paid date is not valid."}, status=400)

    remarks = " ".join(str(data.get("finance_remarks") or "").split()[:20])

    values_class = {
        "NatureOfExpense": str(data.get("nature_of_expense") or "").strip(),
        "AccountingLocation": str(data.get("accounting_location") or "").strip(),
        "WorkingLocation": str(data.get("working_location") or "").strip()[:100],
    }

    with transaction.atomic():
        main = (
            ClaimStatus.objects
            .select_for_update()
            .filter(claim__ClaimNumber=claim_number)
            .order_by("id")
            .first()
        )
        if main is None:
            return JsonResponse({"ok": False, "error": "Claim not found."}, status=404)
        claim = main.claim

        hr_hold = main.holdamounthr or Decimal("0")

        if status in ("Hold", "Approved") and release > hr_hold:
            return JsonResponse(
                {"ok": False, "error": f"Hold release cannot exceed the HR hold amount ({hr_hold})."},
                status=400,
            )
        if status == "Rejected":
            release = Decimal("0.00")

        if split_id is not None:
            split = (
                ClaimSplit.objects
                .select_for_update()
                .filter(pk=split_id, claim=claim)
                .first()
            )
            if split is None:
                return JsonResponse(
                    {"ok": False, "error": "Split row not found for this claim."}, status=404
                )
            created = False
        else:
            split = ClaimSplit(claim=claim)
            created = True

        split.financestatus = status
        split.financecomments = remarks
        split.holdamountfin = hold_fin
        split.releasehold = release
        split.rejectamountfin = rejected
        split.paid = paid
        split.paidon = paid_on

        # Payable amount: save exactly what the front end sent.
        if payable_in is not None:
            split.payableamount = payable_in
        elif created:
            split.payableamount = Decimal("0.00")
        # else: key missing on an update -> keep the value already in the DB

        # Total claim amount: save exactly what the front end sent (0 for a new split).
        # Requires the field  TotalClaimAmount  on the ClaimSplit model.
        if total_claim is not None:
            split.TotalClaimAmount = total_claim
        elif created:
            split.TotalClaimAmount = Decimal("0.00")
        # else: key missing on an update -> keep the value already in the DB

        # Approved amount: save exactly what the front end sent (0 for a split row).
        # Requires the field  approvedamount  on the ClaimSplit model.
        if approved_in is not None:
            split.approvedamount = approved_in
        elif created:
            split.approvedamount = Decimal("0.00")
        # else: key missing on an update -> keep the value already in the DB

        for name, value in values_class.items():
            setattr(split, name, value)
        split.save()

        # Share NON-BLANK classification values with the claim, its status row
        # and the sibling splits (a blank split never wipes saved values).
        shared = {k: v for k, v in values_class.items() if v}
        if shared:
            for name, value in shared.items():
                setattr(claim, name, value)
                setattr(main, name, value)
            claim.save(update_fields=list(shared))
            main.save(update_fields=list(shared))
            ClaimSplit.objects.filter(claim=claim).exclude(pk=split.pk).update(**shared)

        # Display name: ClaimNumber_<position among this claim's splits>
        ids = list(ClaimSplit.objects.filter(claim=claim).order_by("id").values_list("id", flat=True))
        position = ids.index(split.pk) + 1

    return JsonResponse(
        {
            "ok": True,
            "message": "Split created." if created else "Split updated.",
            "claim_number": str(claim_number),
            "split_id": split.pk,
            "split_name": f"{claim_number}_{position}",
            "created": created,
            "payable_amount": str(split.payableamount),
            "total_claim_amount": str(getattr(split, "TotalClaimAmount", 0)),
            "approved_amount": str(getattr(split, "approvedamount", None) or 0),
        },
        status=200,
    )
# ---------------------------------------------------------------------------
# Delete a split row
# ---------------------------------------------------------------------------

@login_required
@require_POST
def delete_finance_split(request, split_id):
    with transaction.atomic():
        split = (
            ClaimSplit.objects
            .select_for_update()
            .filter(pk=split_id)
            .first()
        )
        if split is None:
            return JsonResponse({"ok": False, "error": "Split row not found."}, status=404)

        claim_number = split.claim.ClaimNumber
        split.delete()

    return JsonResponse(
        {
            "ok": True,
            "message": "Split row removed.",
            "claim_number": str(claim_number),
        },
        status=200,
    )


import io
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

BANK_HEADERS = ["DT Number", "Name as per Bank", "Bank Name", "Account Number", "IFSC Code"]
MAX_UPLOAD_MB = 5


def _cell_to_str(value):
    """Excel can return 123.0 for numeric cells, so turn those back into '123'."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


@login_required
def download_bank_template(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Bank Details"
    ws.append(BANK_HEADERS)
    ws.append(["DT1234", "John Doe", "State Bank of India", "123456789012", "SBIN0001234"])

    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col in ("A", "B", "C", "D", "E"):
        ws.column_dimensions[col].width = 24
    # Text format, so account numbers keep leading zeros
    for row in ws.iter_rows(min_row=2, max_row=1000):
        for cell in row:
            cell.number_format = "@"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="bank_details_template.xlsx"'
    return response


@login_required
def bulk_update_bank_details(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

    upload = request.FILES.get("file")
    if not upload:
        return JsonResponse({"status": "error", "message": "Please choose an Excel file."}, status=400)
    if not upload.name.lower().endswith(".xlsx"):
        return JsonResponse({"status": "error", "message": "Only .xlsx files are allowed."}, status=400)
    if upload.size > MAX_UPLOAD_MB * 1024 * 1024:
        return JsonResponse({"status": "error", "message": f"File too large (max {MAX_UPLOAD_MB} MB)."}, status=400)

    try:
        wb = load_workbook(upload, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)

        # Map headers (case/space-insensitive) so column order doesn't matter
        header = next(rows, None)
        if not header:
            return JsonResponse({"status": "error", "message": "The file is empty."}, status=400)
        header_map = {_cell_to_str(h).lower(): i for i, h in enumerate(header) if h is not None}
        missing = [h for h in BANK_HEADERS if h.lower() not in header_map]
        if missing:
            return JsonResponse(
                {"status": "error", "message": "Missing column(s): " + ", ".join(missing)},
                status=400,
            )

        def get(row, name):
            idx = header_map[name.lower()]
            return _cell_to_str(row[idx]) if idx < len(row) else ""

        # Duplicate DT numbers inside the file: the LAST row wins (replaces earlier ones)
        records = {}
        errors = []
        dup_in_file = 0
        for line_no, row in enumerate(rows, start=2):
            if not row or all(c is None or str(c).strip() == "" for c in row):
                continue
            dt = get(row, "DT Number")
            if not dt:
                errors.append(f"Row {line_no}: DT Number is empty.")
                continue
            if dt in records:
                dup_in_file += 1
            records[dt] = {
                "line": line_no,
                "nameasperbank": get(row, "Name as per Bank"),
                "bankname": get(row, "Bank Name"),
                "accountnumber": get(row, "Account Number"),
                "ifsccode": get(row, "IFSC Code").upper(),
            }

        created_count = updated_count = 0
        with transaction.atomic():
            for dt, rec in records.items():
                users = list(User.objects.filter(last_name=dt)[:2])
                if not users:
                    errors.append(f"Row {rec['line']}: DT number '{dt}' not found.")
                    continue
                if len(users) > 1:
                    errors.append(f"Row {rec['line']}: DT number '{dt}' matches multiple users.")
                    continue

                # Existing record is replaced, otherwise created
                _, created = UserProfileB.objects.update_or_create(
                    user=users[0],
                    defaults={
                        "dtnumber": dt,
                        "nameasperbank": rec["nameasperbank"],
                        "bankname": rec["bankname"],
                        "accountnumber": rec["accountnumber"],
                        "ifsccode": rec["ifsccode"],
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        return JsonResponse({
            "status": "success",
            "message": f"{created_count} created, {updated_count} replaced, "
                       f"{dup_in_file} duplicate row(s) in file merged, {len(errors)} skipped.",
            "errors": errors[:50],
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)