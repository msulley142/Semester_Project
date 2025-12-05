# calibration_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
import re

from .models import ChatMessage

User = get_user_model()

ROOM_PATTERN = re.compile(r"^dm-(\d+)-(\d+)$")
MAX_MESSAGE_LENGTH = 2000


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room_name is taken from the URL: /ws/chat/<room_name>/
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.group_name = f"chat_{self.room_name}"

        # Require login
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        # Validate room pattern and ensure current user is part of the room
        match = ROOM_PATTERN.match(self.room_name or "")
        if not match:
            await self.close(code=4400)
            return
        uid_a, uid_b = match.groups()
        if str(user.id) not in {uid_a, uid_b}:
            await self.close(code=4403)
            return

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
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH]
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
