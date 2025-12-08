from django.db.models import Count, Max, Sum, Q
from django.db.models.functions import TruncDate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView
from django.views import View
from django.contrib.auth.models import User

from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from .models import Skill,  Habit, Reward, Journal, Badge, User_Badge,Task, Profile, Goals

from django.contrib import messages


from django.utils.dateparse import parse_date
from calibration_app.progress_tracker import   goal_date_tracker
from calibration_app.analytics import tasks_summary, goals_summary, habits_skills_summary, streak_analytics, mood_analytics, mood_productivity_correlation, week_behavior_points, xp_activity_summary
from calibration_app.mood_tracker import create_mood_entry
from django.utils import timezone
import json
from datetime import timedelta




# Create your views here.





#----Signup View----#

class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        user = form.save()
        Profile.objects.get_or_create(user=user)
        login(self.request, user)
        messages.success(self.request, f"Hi, {user.username}! Please complete your profile before continuing.")
        return redirect(self.success_url)


#----Dashboard View----#

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #used to find to find the last two skills the user has recently worked on and to display on the dashboard.
        
        latest_skills_t = (Skill.objects.filter(account_user=self.request.user, journal__account_user=self.request.user).annotate(latest_entry=Max('journal__date')).exclude(latest_entry=None).order_by('-latest_entry')[:2]  ) #edted and corrected by chatgpt. 
        temp = []
        for skill in latest_skills_t:
            data = skill.skill_progress_data()
            skill.skill_progress_tracked = data["skill_progress_tracked"]
            skill.to_level_up = data["to_level_up"]
            skill.left_over = data["left_over"]
            temp.append(skill)

        context['latest_skills'] = temp
        
        # finds the lastest habits logged by the user.
        recent_habits_t = Habit.objects.filter(account_user=self.request.user).order_by('-created_at')[:2]
        temp2 = []
        for habit in recent_habits_t:
            data2 = goal_date_tracker(habit)
            habit.goal_duration = data2["goal_duration"]
            habit.days_since_start = data2["days_since_start"]
            habit.days_left = data2["days_left"]
            habit.goal_percentage = data2["goal_percentage"]
            habit.goal_complete = data2["goal_complete"]
            temp2.append(habit)


        #used to send to template for display on webpage. 
        context['recent_habits'] = temp2
        context['recent_badges'] = User_Badge.objects.filter(account_user=self.request.user).order_by('-awarded_at')[:3]
        context['current_task'] =  Task.objects.filter(account_user=self.request.user, status__in=['NOTSTARTED', 'INPROGRESS']).order_by('-date', '-id')[:5]
        context['current_goals'] = Goals.objects.filter(account_user=self.request.user, status__in=['not_started', 'in_progress']).order_by('due_date')[:5]
        xp_stats = xp_activity_summary(self.request.user)
        context["xp_today"] = xp_stats["xp_today"]
        context["xp_week"] = xp_stats["xp_week"]
        # streak banner (dashboard only, show once per day)
        try:
            stats = streak_analytics(self.request.user)
            streak = stats.get("login_streak", 0)
            today_key = timezone.localdate().isoformat()
            last_shown = self.request.session.get("streak_banner_date")
            if streak >= 3 and last_shown != today_key:
                messages.success(self.request, f"Streak: {streak} days. Keep it going!")
                self.request.session["streak_banner_date"] = today_key
        except Exception:
            pass

        # friends list for dashboard (buddies only)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        friends_qs = profile.buddies_list().select_related("user")
       
        now = timezone.now()
        friends_payload = []
        for buddy in friends_qs:
            last_login = buddy.user.last_login
            is_online = False
            if last_login:
                # simple heuristic: seen within last 10 minutes counts as online
                is_online = (now - last_login) <= timedelta(minutes=10)
            friends_payload.append({
                "id": buddy.user.id,
                "username": buddy.user.username,
                "is_online": is_online,
            })
        context["friends"] = friends_payload
        # Current groups for dashboard quick view
        groups_payload = []
        for g in profile.community_groups.all().order_by("name"):
            groups_payload.append({
                "id": g.id,
                "name": g.name,
                "category": g.category,
                "member_count": getattr(g, "member_count", g.members.count()),
            })
        context["my_groups"] = groups_payload

        # Calendar data: tasks (by date) and goals (due_date) 
        start = timezone.now().date() - timedelta(days=14)
        end = start + timedelta(days=28)

        events = {}

        task_days = (
            Task.objects.filter(account_user=self.request.user, date__date__range=(start, end))
            .annotate(day=TruncDate("date"))
            
        )
        for t in task_days:
            if t.day is None:
                continue
            str_day = t.day.isoformat()
            events.setdefault(str_day, {"tasks": 0, "goals": 0, "tasks_detail": [], "goals_detail": []})
            events[str_day]["tasks"] += 1


            events[str_day]["tasks_detail"].append({ "id": t.id, "title": t.title, "status": t.status })


        goal_days = (
            Goals.objects.filter(account_user=self.request.user, due_date__isnull=False, due_date__range=(start, end))
        )


        for g in goal_days:
            if g.due_date is None:
                continue

            str_day = g.due_date.isoformat()
            events.setdefault(str_day, {"tasks": 0, "goals": 0, "tasks_detail": [], "goals_detail": []})
            events[str_day]["goals"] += 1
            
            events[str_day]["goals_detail"].append({ "id": g.id, "title": g.title, "status": g.status })


        context["calendar_events_json"] = json.dumps(events)
        return context
    

#----Discipline Buidler View----#
class DisciplineBuilderView(LoginRequiredMixin, TemplateView):
     template_name = 'skillbuilder.html'
    
     def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        load_skill_t= Skill.objects.filter(account_user=self.request.user).order_by('-created_at', 'name')
        
        #cards_hidden = 4
        #context['cards_hidden'] = cards_hidden
        temp3 = []
        for skill in load_skill_t:
         data = skill.skill_progress_data()
         skill.skill_progress_tracked = data["skill_progress_tracked"]
         skill.to_level_up = data["to_level_up"]
         skill.left_over = data["left_over"]
         temp3.append(skill)

        context['load_skills'] = temp3


        load_habits_t = Habit.objects.filter(account_user=self.request.user).order_by('-created_at', 'name')
        temp4 = []
        for habit in load_habits_t:
            data2 = goal_date_tracker(habit)
            habit.goal_duration = data2["goal_duration"]
            habit.days_since_start = data2["days_since_start"]
            habit.days_left = data2["days_left"]
            habit.goal_percentage = data2["goal_percentage"]
            habit.goal_complete = data2["goal_complete"]
            temp4.append(habit)

        context['load_habits'] = temp4
        context['load_goals'] = Goals.objects.filter(account_user= self.request.user, status__in=['not_started', 'in_progress','completed','abandoned']).order_by('start_date')
        context['load_journals'] = Journal.objects.filter(account_user=self.request.user).order_by('date')
        context['load_tasks'] = Task.objects.filter(account_user=self.request.user).order_by('-date', '-id')
        return context
     #allows user to log skill and habit updates on thw webpage.
     #This function is mostly AI generated. The same method was use for the function below this one.
    
       
     #allows users to log tasks through the on the progress tracker/ discipline builder webpage.

    


class ProgressTrackerView(LoginRequiredMixin, TemplateView):
    template_name = 'progresstracker.html'

    def get_context_data(self, **kwargs):
      

        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ---- FILTER INPUTS ----
        q = (self.request.GET.get("q") or "").strip()
        task_status = self.request.GET.get("task_status") or ""
        goal_status = self.request.GET.get("goal_status") or ""
        date_from = parse_date(self.request.GET.get("date_from") or "")
        date_to = parse_date(self.request.GET.get("date_to") or "")
        task_sort = self.request.GET.get("task_sort") or "recent"
        goal_sort = self.request.GET.get("goal_sort") or "due"

        # ---- BASE QUERYSETS ----
        tasks_qs = Task.objects.filter(account_user=user)
        goals_qs = Goals.objects.filter(account_user=user)
        habits_qs = Habit.objects.filter(account_user=user)
        skills_qs = Skill.objects.filter(account_user=user)

        # ---- APPLY FILTERS ----
        if q:
            tasks_qs = tasks_qs.filter(title__icontains=q)
            goals_qs = goals_qs.filter(title__icontains=q)
        if task_status in {Task.NOTSTARTED, Task.INPROGRESS, Task.COMPLETED}:
            tasks_qs = tasks_qs.filter(status=task_status)
        if goal_status in {"not_started", "in_progress", "completed", "abandoned"}:
            goals_qs = goals_qs.filter(status=goal_status)
        if date_from:
            tasks_qs = tasks_qs.filter(date__date__gte=date_from)
            goals_qs = goals_qs.filter(due_date__isnull=False, due_date__gte=date_from)
        if date_to:
            tasks_qs = tasks_qs.filter(date__date__lte=date_to)
            goals_qs = goals_qs.filter(due_date__isnull=False, due_date__lte=date_to)

        # ---- SORTING ----
        task_sort_map = {
            "recent": ("-date", "-id"),
            "oldest": ("date", "id"),
            "points": ("-points", "-date"),
        }
        goal_sort_map = {
            "due": ("due_date", "id"),
            "priority": ("-priority", "due_date"),
            "recent": ("-start_date", "-id"),
        }
        tasks_qs = tasks_qs.order_by(*task_sort_map.get(task_sort, ("-date", "-id")))
        goals_qs = goals_qs.order_by(*goal_sort_map.get(goal_sort, ("due_date", "id")))



        task_stats = tasks_summary(user)
        goal_stats = goals_summary(user)
        hs_stats = habits_skills_summary(user)

        # Merge into one dict for the template: {{ stats.* }}
        context["stats"] = {
            **task_stats,
            **goal_stats,
            **hs_stats,
        }

        context["filters"] = {
            "q": q,
            "task_status": task_status,
            "goal_status": goal_status,
            "date_from": date_from.isoformat() if date_from else "",
            "date_to": date_to.isoformat() if date_to else "",
            "task_sort": task_sort,
            "goal_sort": goal_sort,
        }

   
        streak = streak_analytics(user)
        mood_info = mood_analytics(user)
        mood_corr = mood_productivity_correlation(user)

        context["analytics"] = {
            **streak,
            **mood_info,
            **mood_corr,
        }

           
        context["behavior_points"] = week_behavior_points(user)

       
        context["recent_tasks"] = tasks_qs[:12]
        context["goals"] = goals_qs[:12]

     
        today = timezone.now().date()
        processed_habits = []
        for habit in habits_qs:
            data2 = goal_date_tracker(habit)
            habit.goal_duration = data2["goal_duration"]
            habit.days_since_start = data2["days_since_start"]
            habit.days_left = data2["days_left"]
            habit.goal_percentage = data2["goal_percentage"]
            # you can reuse goal_complete if needed later
            # habit.goal_complete = data2["goal_complete"]
            processed_habits.append(habit)

        context["habits"] = processed_habits[:6]

      
        processed_skills = []
        for skill in skills_qs:
            data = skill.skill_progress_data()
            skill.skill_progress_tracked = data["skill_progress_tracked"]
            skill.to_level_up = data["to_level_up"]
            skill.left_over = data["left_over"]
            processed_skills.append(skill)

        context["skills"] = processed_skills[:6]

        # === Activity heatmap data (tasks + goals over recent weeks) ===
        start = timezone.now().date() - timedelta(days=27)
        end = timezone.now().date()
        events = {}

        task_days = (
            Task.objects.filter(account_user=user, date__date__range=(start, end))
            .annotate(day=TruncDate("date"))
        )
        for t in task_days:
            if t.day is None:
                continue
            day_key = t.day.isoformat()
            events.setdefault(day_key, {"tasks": 0, "goals": 0})
            events[day_key]["tasks"] += 1

        goal_days = Goals.objects.filter(account_user=user, due_date__isnull=False, due_date__range=(start, end))
        for g in goal_days:
            if g.due_date is None:
                continue
            day_key = g.due_date.isoformat()
            events.setdefault(day_key, {"tasks": 0, "goals": 0})
            events[day_key]["goals"] += 1

        context["calendar_events_json"] = json.dumps(events)

        return context









class RewardsTrackerView(LoginRequiredMixin, TemplateView):
    template_name = "rewards.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ---- LEADERBOARD ----
        profile, _ = Profile.objects.get_or_create(user=user)
        buddies = profile.buddies_list()
        players = [profile] + list(buddies)

        my_streak = streak_analytics(user)

        leaderboard = []
        for p in players:
            u = p.user
            streak_info = my_streak if u == user else streak_analytics(u)
            completed_tasks = Task.objects.filter(account_user=u, status=Task.COMPLETED)
            skills_qs = Skill.objects.filter(account_user=u)

            task_points = completed_tasks.aggregate(total=Sum("points"))["total"] or 0
            skill_xp = skills_qs.aggregate(total=Sum("xp"))["total"] or 0
            total_xp = task_points + skill_xp

            badge_count = User_Badge.objects.filter(account_user=u).count()

            leaderboard.append({
                "profile": p,
                "user": u,
                # extra fields used in template:
                "username": u.username,
                "initials": (u.username or "")[:2].upper(),
                "xp": total_xp,
                "total_xp": total_xp,
                "task_points": task_points,
                "skill_xp": skill_xp,
                "badges": badge_count,
                "badge_count": badge_count,
                "streak": streak_info["login_streak"],
                "is_self": (u == user),
                "is_me": (u == user),  # keep both so template is flexible
            })

        # sort by xp and assign rank
        leaderboard.sort(key=lambda row: row["xp"], reverse=True)
        for i, entry in enumerate(leaderboard, start=1):
            entry["rank"] = i
        context["leaderboard"] = leaderboard

        # ---- BADGES ----
        all_badges = list(Badge.objects.all().order_by("title"))
        unlocked_relations = list(
            User_Badge.objects.filter(account_user=user)
            .select_related("badge")
            .order_by("-awarded_at")
        )
        unlocked_ids = {ub.badge_id for ub in unlocked_relations}
        locked_badges = [b for b in all_badges if b.id not in unlocked_ids]

        context["unlocked_badges"] = unlocked_relations
        context["locked_badges"] = locked_badges

        # IMPORTANT: these names must match the template
        context["unlocked_badges_count"] = len(unlocked_relations)
        context["locked_badges_count"] = len(locked_badges)

        # ---- HERO METRICS ----
        me = next((row for row in leaderboard if row["is_self"]), None)
        context["total_xp"] = me["xp"] if me else 0
        token_total = Reward.objects.filter(account_user=user).aggregate(
            total=Sum("tokens")
        )["total"] or 0
        context["token_balance"] = token_total
        context["current_streak"] = my_streak["login_streak"]
        context["longest_streak"] = my_streak["longest_streak"]

        # ---- USER-CREATED REWARDS ----
        context["rewards"] = Reward.objects.filter(account_user=user)

        return context




  