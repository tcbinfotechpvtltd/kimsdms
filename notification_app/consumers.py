# from channels.consumer import SyncConsumer, AsyncConsumer
from channels.generic.websocket import AsyncConsumer, AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


class NotificationsConsumer(AsyncWebsocketConsumer):


    async def connect(self):
        path = self.scope['path']
        token = path.split('notifications/')[1]
        user = await self.get_user(token)
        if user.is_authenticated:
            await self.accept()
            await self.add_channel_name(user, self.channel_name)
            await self.send(text_data="Test message")
        else:
            await self.close()


    async def receive(self, event):
        pass

    # async def chat_message(self, event):
    #     await self.send(text_data=event['text'])

    async def chat_message(self, event):
        print("Sending message:", event['text'])
        await self.send(text_data=event['text'])


    async def disconnect(self, close_code):
        user = self.scope['user']
        await self.remove_channel_name(user)
        print(f"{user} disconnected.")

    
    @database_sync_to_async
    def add_channel_name(self, user, channel_name):
        user.channel_name = channel_name
        user.is_online = True
        user.save()
        return user
    
    @database_sync_to_async
    def remove_channel_name(self, user):
        user.channel_name = None
        user.is_online = False
        user.save()
        return user
    

    @database_sync_to_async
    def get_user(self, token):
        try:
            token_obj = Token.objects.get(key=token)
            return token_obj.user
        except Token.DoesNotExist:
            return AnonymousUser()
        

