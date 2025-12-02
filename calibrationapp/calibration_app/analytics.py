# core/analytics.py
from datetime import timedelta
from itertools import chain

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Mood, Journal, Task, Goals, Habit, Skill


# ---------- BASIC HELPERS ---------- #

def get_daily_mood(user, days_back=None):
    """
    Average mood per day for this user.
    Optionally limit to last N days.
    Returns: [{day, avg_mood, entries}, ...]
    """
    qs = Mood.objects.filter(user=user)

    if days_back is not None:
        start_date = timezone.now().date() - timedelta(days=days_back)
        qs = qs.filter(timestamp__date__gte=start_date)

    return list(
        qs.annotate(day=TruncDate("timestamp"))
          .values("day")
          .annotate(
              avg_mood=Avg("mood_score"),
              entries=Count("id"),
          )
          .order_by("day")
    )


def tasks_summary(user):
    qs = Task.objects.filter(account_user=user)

    total = qs.count()
    completed = qs.filter(status=Task.COMPLETED).count()
    in_progress = qs.filter(status=Task.INPROGRESS).count()
    not_started = qs.filter(status=Task.NOTSTARTED).count()

    completion_rate = int(round((completed / total) * 100)) if total > 0 else 0

    return {
        "tasks_total": total,
        "tasks_completed": completed,
        "tasks_in_progress": in_progress,
        "tasks_not_started": not_started,
        "tasks_completion_rate": completion_rate,
    }


def goals_summary(user):
    qs = Goals.objects.filter(account_user=user)

    total = qs.count()
    completed = qs.filter(status="completed").count()
    active = qs.filter(status__in=["in_progress", "not_started"]).count()

    completion_rate = int(round((completed / total) * 100)) if total > 0 else 0

    return {
        "goals_total": total,
        "goals_completed": completed,
        "goals_active": active,
        "goals_completion_rate": completion_rate,
    }


def habits_skills_summary(user):
    habits_count = Habit.objects.filter(account_user=user).count()
    skills_count = Skill.objects.filter(account_user=user).count()

    return {
        "habits_count": habits_count,
        "skills_count": skills_count,
    }


# ---------- LOGIN / ACTIVITY STREAKS ---------- #

def _activity_dates(user):
    """
    Set of dates where the user had any activity:
    - mood entry
    - task
    - journal
    """
    mood_days = (
        Mood.objects.filter(user=user)
        .annotate(day=TruncDate("timestamp"))
        .values_list("day", flat=True)
    )
    task_days = (
        Task.objects.filter(account_user=user)
        .annotate(day=TruncDate("date"))
        .values_list("day", flat=True)
    )
    journal_days = (
        Journal.objects.filter(account_user=user)
        .annotate(day=TruncDate("date"))
        .values_list("day", flat=True)
    )

    return set(chain(mood_days, task_days, journal_days))


def _current_streak(activity_dates):
    """
    Current streak in days, counting backwards from today,
    as long as each previous day has activity.
    """
    if not activity_dates:
        return 0

    today = timezone.now().date()
    streak = 0
    cursor = today

    while cursor in activity_dates:
        streak += 1
        cursor = cursor - timedelta(days=1)

    return streak


def _longest_streak(activity_dates):
    if not activity_dates:
        return 0

    dates_sorted = sorted(activity_dates)
    longest = 1
    current = 1

    for i in range(1, len(dates_sorted)):
        if (dates_sorted[i] - dates_sorted[i - 1]) == timedelta(days=1):
            current += 1
        else:
            longest = max(longest, current)
            current = 1

    return max(longest, current)


def streak_analytics(user):
    activity_dates = _activity_dates(user)

    login_streak = _current_streak(activity_dates)
    longest_streak = _longest_streak(activity_dates)

    # Consistency over the last 14 days
    lookback_days = 14
    today = timezone.now().date()
    window_start = today - timedelta(days=lookback_days - 1)
    days_in_window = [
        window_start + timedelta(days=i) for i in range(lookback_days)
    ]
    active_days = sum(1 for d in days_in_window if d in activity_dates)
    consistency_score = int(round((active_days / lookback_days) * 100)) if lookback_days > 0 else 0

    if consistency_score >= 80:
        consistency_text = "You’re very consistent. Keep it going."
    elif consistency_score >= 50:
        consistency_text = "You’re doing okay. A few more check-ins would help."
    elif consistency_score > 0:
        consistency_text = "You’ve started – try logging a bit more regularly."
    else:
        consistency_text = "No recent activity logged yet."

    return {
        "login_streak": login_streak,
        "longest_streak": longest_streak,
        "consistency_score": consistency_score,
        "consistency_text": consistency_text,
    }


# ---------- MOOD ANALYTICS ---------- #

def mood_analytics(user):
    # last 14 days mood
    recent_mood = get_daily_mood(user, days_back=14)
    if not recent_mood:
        return {
            "avg_mood": None,
            "mood_trend_text": None,
        }

    avg_mood = sum(row["avg_mood"] for row in recent_mood) / len(recent_mood)

    # trend: compare last 3 days vs previous 3 days
    last3 = recent_mood[-3:]
    prev3 = recent_mood[-6:-3]

    def _avg(lst):
        return sum(x["avg_mood"] for x in lst) / len(lst) if lst else None

    last3_avg = _avg(last3)
    prev3_avg = _avg(prev3)

    mood_trend_text = None
    if last3_avg is not None and prev3_avg is not None:
        diff = last3_avg - prev3_avg
        if diff > 0.4:
            mood_trend_text = "Your mood has been trending up recently."
        elif diff < -0.4:
            mood_trend_text = "Your mood has dipped compared to last week."
        else:
            mood_trend_text = "Your mood has been relatively stable."

    return {
        "avg_mood": round(avg_mood, 2),
        "mood_trend_text": mood_trend_text,
    }


# ---------- TASKS VS MOOD (CORRELATION) ---------- #

def tasks_completed_vs_mood(user, days_back=30):
    """
    Per-day tasks completed and mood.
    Returns [{day, tasks_done, avg_mood}, ...]
    """
    # daily mood
    daily_mood = get_daily_mood(user, days_back=days_back)
    mood_by_day = {row["day"]: row["avg_mood"] for row in daily_mood}

    # limit tasks by date too
    start_date = timezone.now().date() - timedelta(days=days_back)
    completed = (
        Task.objects
        .filter(account_user=user, status=Task.COMPLETED, date__date__gte=start_date)
        .annotate(day=TruncDate("date"))
        .values("day")
        .annotate(tasks_done=Count("id"))
        .order_by("day")
    )

    data = []
    for row in completed:
        day = row["day"]
        data.append({
            "day": day,
            "tasks_done": row["tasks_done"],
            "avg_mood": mood_by_day.get(day),
        })
    return data


def _pearson_corr(xs, ys):
    n = len(xs)
    if n < 2:
        return None

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5

    if den_x == 0 or den_y == 0:
        return None

    return num / (den_x * den_y)


def mood_productivity_correlation(user):
    daily = tasks_completed_vs_mood(user, days_back=30)
    pairs = [(row["tasks_done"], row["avg_mood"]) for row in daily if row["avg_mood"] is not None]

    if len(pairs) < 3:
        return {
            "mood_productivity_correlation": None,
            "mood_correlation_text": "Not enough data yet to find a pattern.",
        }

    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]

    r = _pearson_corr(xs, ys)
    if r is None:
        text = "No clear relationship yet."
    else:
        if r > 0.5:
            text = "On days you complete more tasks, your mood tends to be higher."
        elif r > 0.2:
            text = "More tasks completed is slightly associated with better mood."
        elif r < -0.5:
            text = "Completing more tasks seems linked to lower mood. Watch your load."
        elif r < -0.2:
            text = "There might be a small negative link between workload and mood."
        else:
            text = "Your mood and task completion don’t show a strong pattern yet."

    return {
        "mood_productivity_correlation": round(r, 2) if r is not None else None,
        "mood_correlation_text": text,
    }


# ---------- WEEK AT A GLANCE (behavior_points) ---------- #

def week_behavior_points(user):
    """
    Build 7 entries for your chart:
    each: { label: 'Mon', score: 0–100, mood: 1–10 or None }
    """
    today = timezone.now().date()
    start = today - timedelta(days=6)

    # mood per day in last 7 days
    last7_mood = get_daily_mood(user, days_back=7)
    mood_by_day = {row["day"]: row["avg_mood"] for row in last7_mood}

    # tasks per day in last 7 days
    tasks = (
        Task.objects
        .filter(account_user=user, date__date__gte=start)
        .annotate(day=TruncDate("date"))
        .values("day")
        .annotate(tasks_done=Count("id"))
    )
    tasks_by_day = {row["day"]: row["tasks_done"] for row in tasks}

    # get max tasks to scale scores
    max_tasks = max(tasks_by_day.values()) if tasks_by_day else 0
    max_tasks = max(max_tasks, 1)  # avoid 0

    points = []
    for i in range(7):
        day = start + timedelta(days=i)
        label = day.strftime("%a")  # Mon, Tue, ...

        tasks_done = tasks_by_day.get(day, 0)
        mood = mood_by_day.get(day)

        # tasks normalized 0–100
        task_score = (tasks_done / max_tasks) * 100 if max_tasks > 0 else 0
        # mood normalized assuming 1–10
        if mood is not None:
            mood_score = ((mood - 1) / 9) * 100  # 1–10 → 0–100
        else:
            mood_score = 0

        # Blend: 60% tasks, 40% mood
        score = int(round(task_score * 0.6 + mood_score * 0.4))

        points.append({
            "label": label,
            "score": score,
            "mood": round(mood, 1) if mood is not None else None,
        })

    return points
