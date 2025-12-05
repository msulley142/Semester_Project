from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from .models import ChatMessage


def unread_messages(request):
    """
    Inject unread message metadata for the current user.
    Uses the session-stored timestamp of the last time they opened the
    Messages page to decide if there is anything new.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    # Parse the last time the user visited the messages page
    last_seen_raw = request.session.get("messages_last_seen_at")
    last_seen = None
    if last_seen_raw:
        try:
            last_seen = datetime.fromisoformat(last_seen_raw)
            if timezone.is_naive(last_seen):
                last_seen = timezone.make_aware(last_seen, timezone.get_current_timezone())
        except (TypeError, ValueError):
            last_seen = None

    # User is part of any room that starts/ends with their id, e.g. dm-2-5
    room_filter = (
        Q(room__startswith=f"dm-{user.id}-")
        | Q(room__endswith=f"-{user.id}")
        | Q(room__contains=f"-{user.id}-")
    )

    qs = ChatMessage.objects.filter(room_filter).exclude(sender=user)
    if last_seen:
        qs = qs.filter(created_at__gt=last_seen)

    unread_count = qs.count()
    return {
        "has_unread_messages": unread_count > 0,
        "unread_message_count": unread_count,
    }
