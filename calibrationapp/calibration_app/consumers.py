# calibration_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db import models
import re

from .models import ChatMessage, CommunityGroup, UserBlock
from .utils import sanitize_text

#The following code is heavily edited by ChatGPT.
# ChatConsumer handles WebSocket connections for chat functionality.


User = get_user_model()

# room name patterns for direct messages and group chats
DM_ROOM_PATTERN = re.compile(r"^dm-(\d+)-(\d+)$")
GROUP_ROOM_PATTERN = re.compile(r"^group-(\d+)$")
#message length limit
MAX_MESSAGE_LENGTH = 2000

# Chat consumer for handling WebSocket connections
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
        
        # Authorization check
        room = self.room_name or ""
        dm_match = DM_ROOM_PATTERN.match(room)
        group_match = GROUP_ROOM_PATTERN.match(room)

        if dm_match:
            uid_a, uid_b = dm_match.groups()
            if str(user.id) not in {uid_a, uid_b}:
                await self.close(code=4403)
                return
            other_id = int(uid_b) if str(user.id) == uid_a else int(uid_a)
            if await self.is_blocked(user.id, other_id):
                await self.close(code=4403)
                return
        elif group_match:
            group_id = int(group_match.group(1))
            is_member = await self.is_group_member(group_id, user.id)
            if not is_member:
                await self.close(code=4403)
                return
        else:
            await self.close(code=4400)
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

    @database_sync_to_async
    def is_blocked(self, user_id: int, other_id: int) -> bool:
        return UserBlock.objects.filter(
            models.Q(blocker_id=user_id, blocked_id=other_id)
            | models.Q(blocker_id=other_id, blocked_id=user_id)
        ).exists()

    @database_sync_to_async
    def is_group_member(self, group_id: int, user_id: int) -> bool:
        return CommunityGroup.objects.filter(
            pk=group_id,
            members__user_id=user_id,
        ).exists()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return

        message = (data.get("message") or "").strip()
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH]
        message = sanitize_text(message)
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
