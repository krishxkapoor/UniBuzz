import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import DirectMessage, Group, GroupMessage
from students.models import StudentUser
from core.utils import contains_profanity_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We need to get the user from the session asynchronously
        self.role, self.user_id = await self.get_session_data()
        
        if not self.role or not self.user_id:
            await self.close()
            return

        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Sort IDs to create a unique room name for this 1-on-1 chat
        ids = sorted([int(self.user_id), int(self.other_user_id)])
        self.room_group_name = f'chat_{ids[0]}_{ids[1]}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Profanity check before saving
        if await contains_profanity_async(message):
            await self.send(text_data=json.dumps({
                'type': 'profanity_error',
                'message': 'Your message contains inappropriate language and cannot be sent.'
            }))
            return

        # Save to DB
        msg_obj = await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.user_id,
                'sender_role': self.role,
                'timestamp': msg_obj.timestamp.strftime('%b. %d, %Y, %I:%M %p').replace('AM', 'a.m.').replace('PM', 'p.m.')
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_role': event['sender_role'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, message):
        return DirectMessage.objects.create(
            sender_role=self.role,
            sender_id=self.user_id,
            receiver_role='student', # Only students can use this for now
            receiver_id=self.other_user_id,
            content=message
        )

    @database_sync_to_async
    def get_session_data(self):
        session = self.scope.get('session', {})
        role = session.get('role')
        user_id = session.get(f'{role}_id') if role else None
        return role, user_id

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.role, self.user_id = await self.get_session_data()
        
        if not self.role or not self.user_id:
            await self.close()
            return

        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'group_{self.group_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Profanity check before saving
        if await contains_profanity_async(message):
            await self.send(text_data=json.dumps({
                'type': 'profanity_error',
                'message': 'Your message contains inappropriate language and cannot be sent.'
            }))
            return

        msg_obj, sender_name = await self.save_group_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.user_id,
                'sender_name': sender_name,
                'timestamp': msg_obj.timestamp.strftime('%b. %d, %Y, %I:%M %p').replace('AM', 'a.m.').replace('PM', 'p.m.')
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_group_message(self, message):
        student = StudentUser.objects.get(id=self.user_id)
        group = Group.objects.get(id=self.group_id)
        msg = GroupMessage.objects.create(
            group=group,
            sender=student,
            content=message
        )
        return msg, student.name

    @database_sync_to_async
    def get_session_data(self):
        session = self.scope.get('session', {})
        role = session.get('role')
        user_id = session.get(f'{role}_id') if role else None
        return role, user_id
