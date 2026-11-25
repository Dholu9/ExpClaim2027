from django.urls import path
from django.contrib import admin
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [  
    path('',views.index,name="index"),
    path('reset_password/',auth_views.PasswordResetView.as_view(template_name="reset_password.html"),name="reset_password"),
    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(template_name="reset_password_sent.html"),name="password_reset_done"),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="reset.html"),name="password_reset_confirm"),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name="reset_password_complete.html"),name="password_reset_complete"),
    path('logout/',views.logout_user,name="logout"), 
    path('upload_users/',views.upload_users,name="upload_users"),  
    path('change_last_name/',views.change_last_name,name="change_last_name"),   
    path('newclaim/',views.newclaim,name="newclaim"),
    path('addclaim/',views.addclaim,name="addclaim"),
    path('saverecord/',views.saverecord,name="saverecord"),
    path('entereddata/', views.entereddata, name='entereddata'),
    path('replace_bill_attachment/<int:child_claim_id>/', views.replace_bill_attachment, name='replace_bill_attachment'),
    path('delete_child_form/<int:child_claim_id>/', views.delete_child_form, name='delete_child_form'),    
    path('teams/',views.teams,name="teams"),
    path('associate/',views.associate,name="associate"),
    path('demo/', views.demo, name='demo'),
    path('democustom/', views.democustom, name='democustom'),
    path('selected_claims_view/', views.selected_claims_view, name='selected_claims_view'),    
    path('managementview/', views.managementview, name='managementview'),
    path('managementreview/<int:ClaimNumber>/',views.managementreview,name="managementreview"),
    path('approvedclaims/',views.approvedclaims,name="approvedclaims"), 
    path('approvedclaimsaccounts/',views.approvedclaimsaccounts,name="approvedclaimsaccounts"), 
    path('approvedclaimsmanager/',views.approvedclaimsmanager,name="approvedclaimsmanager"),         
    path('demo2/<int:ClaimNumber>/',views.demo2,name="demo2"),
    path('entereddata2/<int:ClaimNumber>/',views.entereddata2,name="entereddata2"),
    path('entereddatacustom/<int:ClaimNumber>/',views.entereddatacustom,name="entereddatacustom"),
    path('entereddata3/<int:ClaimNumber>/',views.entereddata3,name="entereddata3"),
    path('entereddata4/<int:ClaimNumber>/',views.entereddata4,name="entereddata4"),
    path('showclaim/<int:ClaimNumber>/', views.showclaim, name='showclaim'),  
    path('review_claim/<int:ClaimNumber>/',views.review_claim,name="review_claim"),
    path('accountsview/',views.accountsview,name="accountsview"),

    path('accountsviewrejected/',views.accountsviewrejected,name="accountsviewrejected"),



    path('financeview/',views.financeview,name="financeview"),
    path('accountsreview/<int:ClaimNumber>/',views.accountsreview,name="accountsreview"),
    path('send_approval_rejection_email/<int:claimNumber>/<str:status>/',views.send_approval_rejection_email,name="send_approval_rejection_email"),
    path('send_mail_mahima/<int:claimNumber>/<str:status>/',views.send_mail_mahima,name="send_mail_mahima"),    
    path('sendmailpayment/<int:claimNumber>/<str:status>/<str:paymentcomments>/',views.sendmailpayment,name="sendmailpayment"),    
    path('sendmailuser/<int:claimNumber>/<str:status>/',views.sendmailuser,name="sendmailuser"),
    path('sendmailmanagement/<int:claimNumber>/<str:status>/<str:managementcomments>/',views.sendmailmanagement,name="sendmailmanagement"), 
    path('sendmailvendormanager/<int:claimNumber>/<str:financestatus>/<str:financecomments>/',views.sendmailvendormanager,name="sendmailvendormanager"),
    path('sendmailvendorfinance/<int:claimNumber>/',views.sendmailvendorfinance,name="sendmailvendorfinance"),                   
    path('updaterecord/<int:ClaimNumber>/',views.updaterecord, name='updaterecord'),
    path('paymentreview/<int:ClaimNumber>/',views.paymentreview,name="paymentreview"),
    path('download_claim_files/<int:ClaimNumber>/',views.download_claim_files,name="download_claim_files"),
    path('generatereport/',views.generatereport,name="generatereport"),
    path('generatereportoptimized/',views.generatereportoptimized,name="generatereportoptimized"),
    path('generatereportfinaceview/',views.generatereportfinaceview,name="generatereportfinaceview"),
    path('download_bank_template/', views.download_bank_template, name='download_bank_template'),
    path('bulk_update_bank_details/', views.bulk_update_bank_details, name='bulk_update_bank_details'),
    path('update_expense_head/<int:ClaimNumber>/', views.update_expense_head, name='update_expense_head'),
    path('update_expense_details/', views.update_expense_details, name='update_expense_details'),

    

    
    path('generatereportfinance/',views.generatereportfinance,name="generatereportfinance"),     
    path('generatereportvendor/',views.generatereportvendor,name="generatereportvendor"),
    path('generate_pdf/',views.generate_pdf,name="generate_pdf"),
    path('generate_excel/',views.generate_excel,name="generate_excel"),
    path('download_vouchers/',views.download_vouchers,name="download_vouchers"),
    path('downloadvouchersvendor/',views.downloadvouchersvendor,name="downloadvouchersvendor"),
    path('download_excel_latest/',views.download_excel_latest,name="download_excel_latest"),
    path('download_excel_latesthr/',views.download_excel_latesthr,name="download_excel_latesthr"),
    path('download_vouchers_latest/',views.download_vouchers_latest,name="download_vouchers_latest"),
    path('download_vendor_excel_latest/',views.download_vendor_excel_latest,name="download_vendor_excel_latest"),
    path(
        "update-bank-details/",
        views.update_bank_details,
        name="update_bank_details"
    ),
    path('create-claim-parent/', views.create_claim_parent, name='create_claim_parent'),
    path('add-claim-receipt/', views.add_claim_receipt, name='add_claim_receipt'),
    path('financeview_api/', views.financeview_api, name='financeview_api'),
    path('user-suggestions/', views.user_suggestions, name='user_suggestions'),
    path('upload_excel/', views.upload_excel, name='upload_excel'),

    path('search-excel-by-date/', views.search_excel_by_date, name='search_excel_by_date'),
    path('download/<int:file_id>/', views.download_file, name='download_file'),
    path('save_finance_claim/<int:claim_number>/', views.save_finance_claim, name='save_finance_claim'),
    path('save_finance_split/<int:claim_number>/', views.save_finance_split, name='save_finance_split'),
    path('delete_finance_split/<int:split_id>/', views.delete_finance_split, name='delete_finance_split'),   

            
    path('claims/',views.claims,name="claims"),
    path('view_child_history/',views.view_child_history,name="view_child_history"),
    path('duplicates/',views.duplicates,name="duplicates"),
    path('vendor/',views.vendor,name="vendor"),
    path('vendorclaims/',views.vendorclaims,name="vendorclaims"),  
    path('vendorrecord/',views.vendorrecord,name="vendorrecord"),
    path('downloadoverviewreport/',views.downloadoverviewreport,name="downloadoverviewreport"),    
    path('updaterecordvendor/<str:VendorClaimNumber>/',views.updaterecordvendor, name='updaterecordvendor'),
    path('financeviewvendor/',views.financeviewvendor,name="financeviewvendor"),
    path('managerviewvendor/',views.managerviewvendor,name="managerviewvendor"),    
    path('financereviewvendor/<str:VendorClaimNumber>/',views.financereviewvendor,name="financereviewvendor"),
    path('managerreviewvendor/<str:VendorClaimNumber>/',views.managerreviewvendor,name="managerreviewvendor"), 
    path('showvendorclaim/<str:VendorClaimNumber>/', views.showvendorclaim, name='showvendorclaim'),

    path('showvendordetails/<str:VendorId>/', views.showvendordetails, name='showvendordetails'),  
    path('approvedclaimsvendor/',views.approvedclaimsvendor,name="approvedclaimsvendor"),          
    path('replace_vendorbill_attachment/<str:VendorClaimNumber>/', views.replace_vendorbill_attachment, name='replace_vendorbill_attachment'), 
    path('entereddatavendor/', views.entereddatavendor, name='entereddatavendor'), 
    path('overviewreport/', views.overviewreport, name='overviewreport'), 
    path('savevendorrecord/',views.savevendorrecord,name="savevendorrecord"),

    path('poreport/',views.poreport,name="poreport"),
    path('downloadporeport/',views.downloadporeport,name="downloadporeport"),
 
    path('vendorforfinance/<str:VendorName>/', views.vendorforfinance, name='vendorforfinance'), 
    path('poform/',views.poform,name="poform"),  
 
    path('get_vendor_details/<str:VendorName>/', views.get_vendor_details, name='get_vendor_details'), 
    path('updatevendordetail/<str:VendorId>/',views.updatevendordetail, name='updatevendordetail'), 
    path('view_po_record/<int:po_id>/',views.view_po_record,name="view_po_record"),
    path('update_po_record/<int:po_id>/',views.update_po_record,name="update_po_record"),
    path('save_po_record/',views.save_po_record,name="save_po_record"),  
    path('poproducts/<str:PONumber>/',views.poproducts,name="poproducts"),
    path('update_polast/<str:PONumber>/',views.update_polast,name="update_polast"),
    path('showpos/',views.showpos,name="showpos"),
    path('autouploadclaim/',views.autouploadclaim,name="autouploadclaim"),
    path('get-subprojects/', views.get_subprojects, name='get_subprojects'),
    path('approvedclaimsbymanagervendor/', views.approvedclaimsbymanagervendor, name='approvedclaimsbymanagervendor'),
    path('rejectedclaimsmanager/', views.rejectedclaimsmanager, name='rejectedclaimsmanager'),
    path('fieldclaims/', views.fieldclaims, name='fieldclaims'),

    

    
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

