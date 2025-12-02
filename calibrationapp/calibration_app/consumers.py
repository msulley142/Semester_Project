# calibration_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room_name is taken from the URL: /ws/chat/<room_name>/
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.group_name = f"chat_{self.room_name}"

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    @database_sync_to_async
    def save_message(self, room: str, sender: User, body: str):
        return ChatMessage.objects.create(
            room=room,
            sender=sender,
            body=body,
        )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return

        message = (data.get("message") or "").strip()
        if not message:
            return

        user = self.scope["user"]
        username = user.username if user.is_authenticated else "Anonymous"

        # Save to DB
        await self.save_message(self.room_name, user, message)

        # Broadcast to everyone in this room
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": message,
                "user": username,
            },
        )

    async def chat_message(self, event):
        # This is called for group messages
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "user": event["user"],
                }
            )
        )
