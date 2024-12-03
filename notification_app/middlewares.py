
# from channels.middleware import BaseMiddleware
# from channels.db import database_sync_to_async

# from users.models import User
# from rest_framework.authtoken.models import Token
# from django.contrib.auth.models import AnonymousUser




# @database_sync_to_async
# def get_user(token):
#     try:
#         token = Token.objects.get(key=token)
#         user = token.user
#         print(f"User: {user.username}")
#         return user
#     except:
#         return AnonymousUser()




# class JwtAuthMiddleware(BaseMiddleware):
#     def __init__(self, inner):
#         self.inner = inner

#     async def __call__(self, scope, receive, send):
#         headers = dict(scope["headers"])
#         token_full = headers[b'authorization'].decode('utf-8')
#         token = token_full.split("Token ")[1]
#         user = await get_user(token)
#         scope['user'] = user

#         return await super().__call__(scope, receive, send)
       


from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

@database_sync_to_async
def get_user(token):
    try:
        token_obj = Token.objects.get(key=token)
        return token_obj.user
    except Token.DoesNotExist:

        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        initial_message = await receive()
        if initial_message.get("type") == "websocket.connect":
            try:
                
                token = scope['path'].split('notifications/')[1]
                user = await get_user(token)
                scope['user'] = user
            except Exception as e:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()


        return await super().__call__(scope, receive, send)
       