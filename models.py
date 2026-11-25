from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


from django.db import models
from django.contrib.auth.models import User


class UserProfileB(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    nameasperbank = models.TextField(blank=True)
    dtnumber = models.TextField(blank=True)
    accountnumber = models.TextField(blank=True)
    bankname = models.TextField(blank=True)
    ifsccode = models.TextField(blank=True)   

    def __str__(self):
        return self.user.username



class ParentModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manager_of',null=True)
    skipmanager = models.TextField(blank=True, null=True)
    ClaimNumber = models.IntegerField()
    DateofCreation = models.DateField(auto_now_add=True)
    DateofSubmission = models.DateField(auto_now=True)
    DeduceEmailAddress = models.EmailField(max_length=30, null=True)
    DTNumber = models.TextField()
    Department = models.CharField(max_length=120)
    Manager = models.CharField(max_length=120)
    Project = models.CharField(max_length=120,null=True)
    Subproject = models.CharField(max_length=120,null=True)
    ExpenseDetails = models.CharField(max_length=120)
    StatusDate = models.DateTimeField(null=True, blank=True)
    StatusDateAccounts = models.DateTimeField(null=True, blank=True)    
    NatureOfExpense = models.TextField(null=True)
    AccountingLocation = models.TextField(null=True)
    WorkingLocation = models.TextField(null=True)
    excelfile = models.FileField(upload_to='media/', max_length=254,default='default.xlsx')

class ChildModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None)
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE, related_name='child_models',null=True)
    ReceiptNumber = models.CharField(max_length=100)
    ReceiptDate = models.DateField()
    ReceiptDate1 = models.DateField(null=True)
    BillAttachment = models.FileField(upload_to='media/', max_length=254,default='default.pdf')
    ExpenseHead = models.CharField(max_length=120)
    ClaimAmount = models.PositiveIntegerField()
    TotalClaimAmount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    Remarks = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)


class ClaimStatus(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    claim = models.ForeignKey(ParentModel, on_delete=models.CASCADE,related_name='claimstatus_set',null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    tlstatus = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    comments = models.TextField(blank=True, null=True)
    commentskip = models.TextField(blank=True, null=True)
    accountscomments = models.TextField(blank=True, null=True)
    accountstatus = models.CharField(max_length=20)
    financestatus = models.CharField(max_length=20,default='')
    accountselect = models.CharField(max_length=20,default='')
    managementselect = models.CharField(max_length=20,default='')
    managementstatus = models.CharField(max_length=20,default='')
    managementcomments = models.TextField(blank=True, null=True)
    financecomments = models.TextField(blank=True, null=True)
    approvedamount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    advancededuct = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    holdamounthr = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    holdamountfin = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    rejectamounthr = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    rejectamountfin = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    payableamount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    releasehold = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    rejecthold = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    finalpayableamount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    paidon = models.DateField(null=True, blank=True)
    paid = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    approvedby = models.TextField(blank=True, null=True)
    approvedbyskip = models.TextField(blank=True, null=True)  
    NatureOfExpense = models.TextField(null=True)
    AccountingLocation = models.TextField(null=True)  
    WorkingLocation = models.TextField(null=True) 
    

class ClaimSplit(models.Model):
    claim = models.ForeignKey(ParentModel, on_delete=models.CASCADE, related_name='splits')
    financestatus = models.CharField(max_length=20)
    holdamountfin = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    financecomments = models.TextField(blank=True, null=True)
    releasehold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rejectamountfin = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payableamount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paidon = models.DateField(null=True, blank=True)    # or paidon, see below
    created_on = models.DateField(auto_now_add=True, null=True)       # optional: the date the split was created
    NatureOfExpense = models.TextField(null=True)
    AccountingLocation = models.TextField(null=True)
    WorkingLocation = models.TextField(null=True)
    last_updated = models.DateTimeField(auto_now=True)
    TotalClaimAmount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approvedamount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']
    


class VendorParentModel(models.Model):
    VendorClaimNumber = models.CharField(max_length=120,null=True)
    DateofCreation = models.DateField(auto_now_add=True,null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    EnteredBy = models.CharField(max_length=120, null=True)
    RaisedBy = models.CharField(max_length=120)
    DTNumber = models.TextField(null=True)
    ProjectName = models.CharField(max_length=120)
    Subproject = models.CharField(max_length=120,null=True)
    VendorName = models.CharField(max_length=120)
    VendorExpenseDetail = models.TextField(null=True)
    Description = models.TextField(null=True)
    TotalClaimAmount = models.CharField(max_length=120)
    StatusDate = models.DateTimeField(null=True, blank=True)
    StatusDateAccounts = models.DateTimeField(null=True, blank=True)
    InvoiceNumber = models.CharField(null=True,max_length=500)
    InvoiceDate = models.DateField(null=True)
    FromDate = models.DateField(null=True)
    ToDate = models.DateField(null=True)
    Approval = models.CharField(max_length=120,null=True)
    WorkOrder = models.CharField(max_length=120,null=True)
    PurchaseOrder = models.CharField(max_length=120,null=True)
    InvoiceAttachment = models.FileField(upload_to='media2/', max_length=254,default='default.pdf') 
    EmailAttachment = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')   
    ClaimAmount = models.FloatField(null=True)
    AdditionalAmount = models.FloatField(null=True)
    AdditionalField = models.CharField(max_length=120,null=True)
    Quantity = models.CharField(max_length=120,null=True)
    Unit = models.CharField(max_length=120,null=True)
    Currency = models.CharField(max_length=120,null=True)    
    Rate = models.FloatField(null=True)
    GST = models.FloatField(null=True)   
    Remarks = models.TextField(null=True)
    AddApprovedBy = models.CharField(max_length=120,null=True)  
    AddAttachment = models.FileField(upload_to='media2/', max_length=254,default='default.pdf') 
    AddField = models.TextField(null=True)
    AdvanceApprovedBy = models.CharField(max_length=120,null=True) 
    AdvanceAmount = models.FloatField(null=True)
    AdvanceAttachment = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')
    ToBeDeducted = models.CharField(max_length=120,null=True) 


class VendorClaimStatus(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    claim = models.ForeignKey(VendorParentModel, on_delete=models.CASCADE,related_name='vendorclaimstatus_set',null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    comments = models.TextField(blank=True, null=True)
    financecomments = models.TextField(blank=True, null=True)
    financestatus = models.CharField(max_length=20)
    paymentstatus = models.CharField(max_length=20,default='')
    accountselect = models.CharField(max_length=20,default='')
    managementselect = models.CharField(max_length=20,default='')
    managementstatus = models.CharField(max_length=20,default='')
    managementcomments = models.TextField(blank=True, null=True)
    paymentcomments = models.TextField(blank=True, null=True)
    approvedamount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    approvedby = models.TextField(blank=True, null=True)
   


    def __str__(self):
        return f"{self.claim.VendorClaimNumber} - {self.status}"


class VendorDetailModel(models.Model):
    EnteredBy = models.CharField(max_length=120,null=True)
    Duration = models.CharField(max_length=120,null=True,default='1')
    VendorName = models.TextField(blank=True, null=True)
    VendorId = models.CharField(max_length=120,null=True)
    VendorEmail = models.EmailField()
    VendorGST = models.CharField(max_length=120)
    BankName = models.TextField(blank=True, null=True)
    AccountNumber = models.CharField(max_length=120)
    IFSCCode = models.CharField(max_length=120)
    PlotNumber = models.TextField(blank=True, null=True)
    StreetName = models.TextField(blank=True, null=True)
    Locality = models.TextField(blank=True, null=True)
    City = models.CharField(max_length=120)
    Pincode = models.CharField(max_length=120)
    State = models.CharField(max_length=120)
    MobileNumber = models.CharField(max_length=120,null=True)
    PanNumber = models.CharField(max_length=120,null=True)
    GSTCopy = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')
    MSMECopy = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')
    CancelledCheque = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')
    PANCopy = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')
    EmailCopy = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')
    ContractCopy = models.FileField(upload_to='media2/', max_length=254,default='default.pdf')

class PODetailModel(models.Model):
    VendorName = models.CharField(max_length=120)
    PODate = models.DateField(null=True)
    POReference = models.CharField(max_length=120, null=True)
    VendorReference = models.CharField(max_length=120, null=True)
    Terms = models.TextField(default=None)
    PONumber = models.CharField(max_length=120, null=True)
    ApprovalFrom = models.CharField(max_length=120, null=True)
    ShipTo = models.CharField(max_length=120, null=True)
    POEmailCopy = models.FileField(upload_to='media2/', max_length=254, default='default.pdf')
    RequestedBy = models.ForeignKey(User, on_delete=models.CASCADE,null=True)  # Assuming you want to link to the user
    totalAmountSum = models.CharField(max_length=500, null=True) 
    total_gst_sum = models.CharField(max_length=500, null=True)
    totalAmountTotal = models.CharField(max_length=500, null=True)
    totalAmountTotalWords = models.CharField(max_length=500, null=True)

class POChildModel(models.Model):
    parent_po = models.ForeignKey(PODetailModel, on_delete=models.CASCADE, related_name='children', null=True)
    Description = models.TextField()
    HSNCode = models.CharField(max_length=120)
    Quantity = models.CharField(max_length=120)
    Unit = models.CharField(max_length=120, null=True)
    Rate = models.CharField(max_length=120, null=True)
    GSTPercentage = models.CharField(max_length=120, null=True)
    Amount = models.CharField(max_length=120, null=True)
    TotalAmount = models.CharField(max_length=120, null=True)
    GSTAmount = models.CharField(max_length=120)

class Project(models.Model):
    project_id = models.CharField(max_length=100, unique=True)
    project_title = models.CharField(max_length=200)
    project_description = models.TextField()

    def __str__(self):
        return self.project_title

class Subproject(models.Model):
    subproject_title = models.CharField(max_length=200)
    subproject_id = models.CharField(max_length=100)
    
    # ForeignKey to establish the link between subproject and project
    project = models.ForeignKey(Project, related_name='subprojects', on_delete=models.CASCADE,default=None)

    def __str__(self):
        return self.subproject_title
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    manager = models.ForeignKey(User, related_name='managed_users', null=True, blank=True, on_delete=models.SET_NULL)



import secrets
import hashlib

from django.db import models


class VendorAPIKey(models.Model):
    """
    One row per external vendor/integration. The raw key is only ever
    shown once at creation time — only its SHA-256 hash is stored, so
    a database leak alone can't be used to authenticate as the vendor.
    """
    name = models.CharField(
        max_length=100,
        help_text='e.g. "Acme Vendor - Production" or "Acme Vendor - Sandbox"'
    )
    key_hash = models.CharField(max_length=64, unique=True)
    prefix = models.CharField(
        max_length=8,
        help_text='First 8 chars of the raw key, shown in admin for identification only'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Vendor API Key"

    def __str__(self):
        status = "active" if self.is_active else "REVOKED"
        return f"{self.name} ({self.prefix}..., {status})"

    @staticmethod
    def generate_key():
        """Returns (raw_key, key_hash). raw_key is shown to the caller
        exactly once and never stored — only key_hash is persisted."""
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, key_hash
    
class ExcelFile(models.Model):
    file = models.FileField(upload_to='excels/%Y/%m/')
    file_date = models.DateField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.file_date} - {self.file.name}"
    

     
        
        


