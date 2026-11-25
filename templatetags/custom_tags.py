from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def is_manager(user):
    return user.groups.filter(name='Manager').exists()

@register.filter
def is_management(user):
    return user.groups.filter(name='Management').exists()

@register.filter
def is_Accounts(user):
    return user.groups.filter(name='Accounts').exists()

@register.filter
def is_Finance(user):
    return user.groups.filter(name='Finance').exists()

@register.filter
def is_Fieldteam(user):
    return user.groups.filter(name='Fieldteam').exists()

@register.filter
def is_VendorManager(user):
    return user.groups.filter(name='VendorManager').exists()

@register.filter
def is_HR(user):
    return user.groups.filter(name='HR').exists()

@register.filter
def is_IT(user):
    return user.groups.filter(name='IT').exists()

@register.filter
def is_Admin(user):
    return user.groups.filter(name='Admin').exists()

@register.filter
def is_GPM(user):
    return user.groups.filter(name='GPM').exists()

@register.filter
def is_GPO(user):
    return user.groups.filter(name='GPO').exists()

@register.filter
def is_Anil(user):
    return user.groups.filter(name='Anil').exists()

@register.filter
def is_Siddraju(user):
    return user.groups.filter(name='Siddraju').exists()


