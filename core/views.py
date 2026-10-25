from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    connection.ensure_connection()
    return JsonResponse({"status": "ok", "database": connection.vendor})
