

from functools import wraps
from django.http import JsonResponse

from organization.models import Organization

# def authenticate_access_key(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         access_key = request.headers.get('access_key')
#         access_id = request.headers.get('access_id') 

#         print(request.headers, access_id, access_key)
        
#         found = Organization.objects.filter(access_key=access_key, access_id=access_id, access_id__isnull=False, access_key__isnull=False).exists()

#         print(found)
#         if found:
#             return view_func(request, *args, **kwargs) 
        
#         return JsonResponse({"error": "Unauthorized access"}, status=403)

#     return _wrapped_view


def authenticate_access_key(request):
    access_key = request.headers.get('access_key')
    access_id = request.headers.get('access_id')  
    print(request.headers)   
    found = Organization.objects.filter(access_key=access_key, access_id=access_id, access_id__isnull=False, access_key__isnull=False).exists()
    if found:
        return True, ''
    return False, JsonResponse({"error": "Unauthorized access"}, status=403)
