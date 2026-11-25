import hashlib
from functools import wraps

from django.http import JsonResponse
from django.utils import timezone

from .models import VendorAPIKey


def require_api_key(view_func):
    """
    Use this in place of @login_required on any endpoint an external
    vendor calls directly (server-to-server, no browser session/cookies
    involved). Vendor sends their key as either:

        Authorization: Api-Key <the-key>
    or
        X-API-Key: <the-key>

    On success, request.vendor_api_key is set to the matching
    VendorAPIKey row, so the view can log/attribute the call if needed.
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Api-Key '):
            raw_key = auth_header[len('Api-Key '):].strip()
        else:
            raw_key = request.headers.get('X-API-Key', '').strip()

        if not raw_key:
            return JsonResponse({'error': 'Missing API key'}, status=401)

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        try:
            api_key = VendorAPIKey.objects.get(key_hash=key_hash, is_active=True)
        except VendorAPIKey.DoesNotExist:
            return JsonResponse({'error': 'Invalid or inactive API key'}, status=401)

        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=['last_used_at'])

        request.vendor_api_key = api_key
        return view_func(request, *args, **kwargs)

    return wrapped