from django.contrib import admin
from .models import ParentModel, ChildModel,ClaimStatus,UserProfile,VendorDetailModel,VendorParentModel,VendorClaimStatus,Project,PODetailModel,POChildModel,Subproject
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django import forms


class ChildModelInline(admin.StackedInline):
    model = ChildModel
    extra = 1

@admin.register(ParentModel)
class ParentModelAdmin(admin.ModelAdmin):
    inlines = [ChildModelInline]
    list_display = ['user','ClaimNumber', 'DateofCreation', 'DeduceEmailAddress', 'DTNumber', 'Department', 'Manager', 'ExpenseDetails','StatusDate','StatusDateAccounts']

    def manager_email(self, obj):
        return obj.manager.email

@admin.register(ChildModel)
class ChildModelAdmin(admin.ModelAdmin):
    list_display = ['ReceiptNumber', 'ReceiptDate','BillAttachment','ExpenseHead', 'ClaimAmount','TotalClaimAmount', 'Remarks','created_at']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request  # Pass the request object to the form
        return form

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)

@admin.register(ClaimStatus)
class ClaimStatusAdmin(admin.ModelAdmin):
    
    list_display = ['status','comments','accountscomments','accountstatus','financestatus','accountselect','managementselect','managementstatus','managementcomments','financecomments','approvedby','approvedamount']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = ['user', 'manager']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = ['project_id','project_title']

@admin.register(Subproject)
class SubprojectAdmin(admin.ModelAdmin):

    list_display = ['subproject_id','subproject_title']


@admin.register(VendorDetailModel)
class VendorDetailModelAdmin(admin.ModelAdmin):

    list_display = ['VendorName','VendorEmail', 'VendorGST', 'BankName', 'AccountNumber', 'IFSCCode', 'MobileNumber']


@admin.register(VendorParentModel)
class VendorParentModelAdmin(admin.ModelAdmin):
    list_display = ['user','DateofCreation','VendorClaimNumber','RaisedBy', 'ProjectName', 'VendorName', 'TotalClaimAmount','InvoiceNumber', 'FromDate', 'ToDate', 'InvoiceAttachment', 'ClaimAmount', 'Remarks']

@admin.register(VendorClaimStatus)
class VendorClaimStatusAdmin(admin.ModelAdmin):

    list_display = ['status','financestatus', 'financecomments'] 

@admin.register(PODetailModel)
class PODetailModelAdmin(admin.ModelAdmin):

    list_display = ['VendorName','RequestedBy']

@admin.register(POChildModel)
class POChildModelAdmin(admin.ModelAdmin):

    list_display = ['parent_po','Description']

class CustomGroupForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Users', False),
        required=False
    )

    class Meta:
        model = Group
        fields = ('name', 'users')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save(self, commit=True):
        group = super().save(commit)
        if commit:
            group.user_set.set(self.cleaned_data['users'])
        return group


class CustomGroupAdmin(GroupAdmin):
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and request.user.groups.filter(name='Manager').exists():
            fields += ('users',)
        return fields

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)   



