from datetime import datetime

from django.utils import timezone
from django.db.models import Q

from .models import ChatMessage, Profile, UserBlock


def unread_messages(request):
    """
    Inject unread message metadata for the current user.
    Uses the session-stored timestamp of the last time they opened the
    Messages page to decide if there is anything new.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    profile = Profile.objects.filter(user=user).first()

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

    if profile:
        group_ids = profile.community_groups.values_list("id", flat=True)
        group_rooms = [f"group-{gid}" for gid in group_ids]
        if group_rooms:
            room_filter = room_filter | Q(room__in=group_rooms)

    qs = ChatMessage.objects.filter(room_filter).exclude(sender=user)
    blocked_ids = set(
        UserBlock.objects.filter(Q(blocker=user) | Q(blocked=user)).values_list("blocked_id", flat=True)
    ) | set(
        UserBlock.objects.filter(Q(blocker=user) | Q(blocked=user)).values_list("blocker_id", flat=True)
    )
    if blocked_ids:
        qs = qs.exclude(sender_id__in=blocked_ids)
    if last_seen:
        qs = qs.filter(created_at__gt=last_seen)

    unread_count = qs.count()
    return {
        "has_unread_messages": unread_count > 0,
        "unread_message_count": unread_count,
    }
