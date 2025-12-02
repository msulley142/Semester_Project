# calibration_app/mood_utils.py
from django.utils import timezone
from .models import Mood


def create_mood_entry(
    account_user,
    mood_score=None,
    mood_type=None,
    note=None,
    related_goal=None,
    energy_level=None,
    sleep_hours=None,
    stress_level=None,
    social_interaction=None,
    timestamp=None,
):
    """
    Safely create a Mood entry if mood_score is provided.
    Assumes Mood has an 'account_user' FK like your other models.
    """
    if not mood_score:
        return

    try:
        mood_score = int(mood_score)
    except (TypeError, ValueError):
        return

    if timestamp is None:
        timestamp = timezone.now()

    data = {
        "user": account_user,   # if your Mood model uses 'user', change this key
        "mood_score": mood_score,
        "mood_type": mood_type or None,
        "note": note or None,
        "related_goal": related_goal,
    }

    if energy_level not in ("", None):
        try:
            data["energy_level"] = int(energy_level)
        except ValueError:
            pass

    if sleep_hours not in ("", None):
        try:
            data["sleep_hours"] = float(sleep_hours)
        except ValueError:
            pass

    if stress_level not in ("", None):
        try:
            data["stress_level"] = int(stress_level)
        except ValueError:
            pass

    if social_interaction not in ("", None):
        try:
            data["social_interaction"] = int(social_interaction)
        except ValueError:
            pass

    data["timestamp"] = timestamp

    Mood.objects.create(**data)
