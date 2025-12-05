from django.db.models import Count, Max, Sum, Q
from django.db.models.functions import TruncDate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.views import View
from django.contrib.auth.models import User

from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from .models import Skill,  Habit, Reward, Journal, Badge, User_Badge,Task, Profile, Goals, Mood, Topics, Post, Forum, BuddyRequest, Friendship, ChatMessage, ForumVote
from .forms import SkillForm, HabitForm, JournalForm, RewardForm, TaskForm, ProfileForm, UserForm, GoalForm, MoodForm, TopicsForm, PostForm, ForumForm, BuddyRequestForm, BuddyRespondForm
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import make_aware
from datetime import datetime
from calibration_app.progress_tracker import task_completion_badge, award_badge, journal_entry_create,  streak_notify, abst_badge, goal_date_tracker, goal_award_updater
from calibration_app.analytics import tasks_summary, goals_summary, habits_skills_summary, streak_analytics, mood_analytics, mood_productivity_correlation, week_behavior_points, xp_activity_summary
from calibration_app.mood_tracker import create_mood_entry
from django.utils import timezone
import json
from datetime import timedelta




# Create your views here.
#----Landing View---#



class LoginView(FormView):
    template_name = 'auth/login.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        # Update streak/badges on each successful login
        try:
            streak_notify(user)
        except Exception:
            # don't block login on streak side-effects
            pass
        return super().form_valid(form)


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

        #context['recent_journal'] = Journal.objects.filter(account_user=self.request.user).order_by('-date', 'id')[:5]

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
                "username": buddy.user.username,
                "is_online": is_online,
            })
        context["friends"] = friends_payload

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
     def post_to_journal(self, request):
         
         entry_type = request.POST.get("entry_type")
         skill_user = request.POST.get("skill") or None
         habit_user = request.POST.get("habit") or None
         trigger = request.POST.get("trigger") or None
         note = request.POST.get("note") or None
         date_added = request.POST.get("date")
          
        #  default_date = None 
        #  if date_added:
        #      try:
        #          date_added = make_aware(datetime.fromisoformat(date_added))
        #      except Exception:
        #           default_date = None

         user_entry = Journal(account_user=request.user, entry_type=entry_type, trigger=trigger, note=note)
         
         #needed because I haven't seperated the skill and habit feilds for user input yet.  
         if skill_user:
             try: user_entry.skill = Skill.objects.get(id=skill_user, account_user=request.user)
             except Skill.DoesNotExist: pass
         if habit_user:
             try: user_entry.habit = Habit.objects.get(id=habit_user, account_user=request.user)
             except Habit.DoesNotExist: pass

         if skill_user and habit_user:
             messages.error(request, "Only one option is allowed.")
             return redirect('disciplinebuilder')

         user_entry.save()
         messages.success(request, "Journal entry saved")
         journal_entry_create(user_entry)

        
         return redirect('disciplinebuilder')

       
     #allows users to log tasks through the on the progress tracker/ discipline builder webpage.

     def post_to_task(self, request):
         
         title = request.POST.get("title")
         points = request.POST.get("points") or None
         user_skill = request.POST.get("skill") or None
         habit_user1 = request.POST.get('habit') or None
         status = request.POST.get("status") or None
         description = request.POST.get("description") or None
         date_user = request.POST.get("date")

         default_date1 = None 
         if date_user:
             try:
                 date_user = make_aware(datetime.fromisoformat(date_user))
             except Exception:
                  default_date1 = None

         user_task = Task(account_user=request.user, title=title, points=points, status=status, description=description)
         
         if user_skill:
             try: user_task.skill = Skill.objects.get(id=user_skill, account_user=request.user)
             except Skill.DoesNotExist: pass
         if habit_user1:
             try: user_task.habit = Habit.objects.get(id=habit_user1, account_user=request.user)
             except Habit.DoesNotExist: pass

         if user_skill and habit_user1:
             messages.error(request, "Only one option is allowed.")
             return redirect('disciplinebuilder')

         user_task.save()
         messages.success(request, "Task entry saved")
         return redirect('disciplinebuilder')
                                                  
         
     


class ProgressTrackerView(LoginRequiredMixin, TemplateView):
    template_name = 'progresstracker.html'

    def get_context_data(self, **kwargs):
        from django.utils import timezone  # if not already imported at top
        from django.utils.dateparse import parse_date

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

        # =========================
        # 1) TOP STATS (cards row)
        # =========================
        # you already imported these at the top:
        # from calibration_app.analytics import (
        #   tasks_summary, goals_summary, habits_skills_summary,
        #   streak_analytics, mood_analytics,
        #   mood_productivity_correlation, week_behavior_points
        # )

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

        # ======================================
        # 2) BEHAVIOR & MOOD SNAPSHOT (analytics)
        # ======================================
        streak = streak_analytics(user)
        mood_info = mood_analytics(user)
        mood_corr = mood_productivity_correlation(user)

        context["analytics"] = {
            **streak,
            **mood_info,
            **mood_corr,
        }

        # =================================
        # 3) WEEK AT A GLANCE (bar chart)
        # =================================
        context["behavior_points"] = week_behavior_points(user)

        # ==================================
        # 4) RECENT TASKS / GOALS (right now)
        # ==================================
        context["recent_tasks"] = tasks_qs[:12]
        context["goals"] = goals_qs[:12]

        # ==================================
        # 5) HABITS (with goal % + days left)
        # ==================================
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

        # ===========================
        # 6) SKILLS (XP + progress %)
        # ===========================
        processed_skills = []
        for skill in skills_qs:
            data = skill.skill_progress_data()
            skill.skill_progress_tracked = data["skill_progress_tracked"]
            skill.to_level_up = data["to_level_up"]
            skill.left_over = data["left_over"]
            processed_skills.append(skill)

        context["skills"] = processed_skills[:6]

        return context









class RewardsTrackerView(LoginRequiredMixin, TemplateView):
    template_name = "rewards.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
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
        ctx["leaderboard"] = leaderboard

        # ---- BADGES ----
        all_badges = list(Badge.objects.all().order_by("title"))
        unlocked_relations = list(
            User_Badge.objects.filter(account_user=user)
            .select_related("badge")
            .order_by("-awarded_at")
        )
        unlocked_ids = {ub.badge_id for ub in unlocked_relations}
        locked_badges = [b for b in all_badges if b.id not in unlocked_ids]

        ctx["unlocked_badges"] = unlocked_relations
        ctx["locked_badges"] = locked_badges

        # IMPORTANT: these names must match the template
        ctx["unlocked_badges_count"] = len(unlocked_relations)
        ctx["locked_badges_count"] = len(locked_badges)

        # ---- HERO METRICS ----
        me = next((row for row in leaderboard if row["is_self"]), None)
        ctx["total_xp"] = me["xp"] if me else 0

        token_total = Reward.objects.filter(account_user=user).aggregate(
            total=Sum("tokens")
        )["total"] or 0
        ctx["token_balance"] = token_total

        ctx["current_streak"] = my_streak["login_streak"]
        ctx["longest_streak"] = my_streak["longest_streak"]

        # ---- USER-CREATED REWARDS ----
        ctx["rewards"] = Reward.objects.filter(account_user=user)

        return ctx




    
class CommunityView(LoginRequiredMixin, TemplateView):
    template_name = 'community.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)

        selected_topic = self.request.GET.get("topic")

        context["topics"] = Topics.objects.all().order_by("name")
        threads = (
            Forum.objects.select_related("topic", "author")
            .annotate(
                comment_count=Count("post"),
                up_count=Count("votes", filter=Q(votes__value=ForumVote.UP)),
                down_count=Count("votes", filter=Q(votes__value=ForumVote.DOWN)),
            )
            .order_by("-created_at")
        )
        if selected_topic:
            threads = threads.filter(topic_id=selected_topic)

        context["selected_topic"] = selected_topic
        context["threads"] = threads[:50]
        context["buddies"] = profile.buddies_list()
        context["incoming"] = BuddyRequest.objects.filter(receiver=profile, status=BuddyRequest.PENDING)
        context["outgoing"] = BuddyRequest.objects.filter(sender=profile, status=BuddyRequest.PENDING)
        context["buddy_form"] = BuddyRequestForm()
        context["respond_form"] = BuddyRespondForm()
        context["user_votes"] = dict(
            ForumVote.objects.filter(user=self.request.user).values_list("forum_id", "value")
        )

        return context 

    def post(self, request, *args, **kwargs):
        topic_id = request.POST.get("topic")
        topic_name = (request.POST.get("topic_name") or "").strip()
        title = (request.POST.get("title") or "").strip()
        body = (request.POST.get("body") or "").strip()

        if not topic_id and not topic_name:
            messages.error(request, "Pick an existing topic or create a new one.")
            return redirect("community")

        topic = None
        if topic_id:
            topic = Topics.objects.filter(id=topic_id).first()
            if not topic:
                messages.error(request, "Topic not found.")
                return redirect("community")
        elif topic_name:
            topic, _ = Topics.objects.get_or_create(name=topic_name)

        if not title or not body:
            messages.error(request, "Title and body are required to post.")
            return redirect("community")

        Forum.objects.create(
            topic=topic,
            author=request.user,
            title=title,
            body=body,
        )

        messages.success(request, "Your discussion has been posted.")
        return redirect("community")


def forum_vote(request, pk):
    if not request.user.is_authenticated:
        return redirect("login")
    forum = get_object_or_404(Forum, pk=pk)
    value = request.POST.get("vote")
    if value == "up":
        vote_val = ForumVote.UP
    elif value == "down":
        vote_val = ForumVote.DOWN
    else:
        messages.error(request, "Invalid vote.")
        return redirect(request.META.get("HTTP_REFERER", "community"))

    existing, created = ForumVote.objects.get_or_create(forum=forum, user=request.user, defaults={"value": vote_val})
    if not created:
        if existing.value == vote_val:
            existing.delete()
        else:
            existing.value = vote_val
            existing.save(update_fields=["value"])

    up_count = ForumVote.objects.filter(forum=forum, value=ForumVote.UP).count()
    down_count = ForumVote.objects.filter(forum=forum, value=ForumVote.DOWN).count()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "up": up_count, "down": down_count})

    return redirect(request.META.get("HTTP_REFERER", "community"))





class CoachingView(LoginRequiredMixin, TemplateView):
    template_name = 'coaching.html'


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'userprofile.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)

        tasks_qs = Task.objects.filter(account_user=user)
        skills_qs = Skill.objects.filter(account_user=user)
        habits_qs = Habit.objects.filter(account_user=user)

        task_points = tasks_qs.filter(status=Task.COMPLETED).aggregate(total=Sum("points"))["total"] or 0
        skill_xp = skills_qs.aggregate(total=Sum("xp"))["total"] or 0
        total_xp = task_points + skill_xp

        streak_info = streak_analytics(user)

        skills_data = []
        for skill in skills_qs.order_by('-created_at')[:5]:
            data = skill.skill_progress_data()
            skills_data.append({
                "name": skill.name,
                "level": skill.level,
                "progress": data["skill_progress_tracked"],
            })

        habits_data = []
        for habit in habits_qs.order_by('-created_at')[:5]:
            gd = goal_date_tracker(habit)
            habits_data.append({
                "name": habit.name,
                "progress": gd["goal_percentage"],
            })

        badges = User_Badge.objects.filter(account_user=user).select_related("badge").order_by('-awarded_at')[:6]
        friends = profile.buddies_list().select_related("user")
        token_balance = Reward.objects.filter(account_user=user).aggregate(total=Sum("tokens"))["total"] or 0

        latest_journal = Journal.objects.filter(account_user=user).order_by('-date').first()
        mood_recent = Mood.objects.filter(user=user).order_by('-timestamp')[:5]

        activity = []
        for task in tasks_qs.filter(status=Task.COMPLETED).order_by('-date')[:3]:
            activity.append({
                "title": f"Completed {task.title}",
                "meta": task.date.strftime("%b %d, %Y"),
            })
        for j in Journal.objects.filter(account_user=user).order_by('-date')[:2]:
            activity.append({
                "title": f"Journal entry: {j.entry_type.title()}",
                "meta": j.date.strftime("%b %d, %Y"),
            })
        for b in badges[:2]:
            activity.append({
                "title": f"Badge unlocked: {b.badge.title}",
                "meta": b.awarded_at.strftime("%b %d, %Y"),
            })

        ctx.update({
            "profile": profile,
            "skills_data": skills_data,
            "habits_data": habits_data,
            "badges": badges,
            "friends": friends,
            "token_balance": token_balance,
            "total_xp": total_xp,
            "login_streak": streak_info.get("login_streak", 0),
            "skills_count": skills_qs.count(),
            "latest_journal": latest_journal,
            "mood_recent": mood_recent,
            "recent_activity": activity,
            "incoming": BuddyRequest.objects.filter(receiver=profile, status=BuddyRequest.PENDING),
            "outgoing": BuddyRequest.objects.filter(sender=profile, status=BuddyRequest.PENDING),
            "buddy_form": BuddyRequestForm(),
            "respond_form": BuddyRespondForm(),
        })
        return ctx


class VisitorProfileView(LoginRequiredMixin, TemplateView):
    template_name = "visitorprofile.html"

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        from calibration_app.progress_tracker import goal_date_tracker
        from calibration_app.analytics import streak_analytics
        ctx = super().get_context_data(**kwargs)
        target_user = get_object_or_404(User, pk=kwargs.get("user_id"))
        profile, _ = Profile.objects.get_or_create(user=target_user)

        skills_qs = Skill.objects.filter(account_user=target_user)
        habits_qs = Habit.objects.filter(account_user=target_user)
        goals_qs = Goals.objects.filter(account_user=target_user)
        badges = User_Badge.objects.filter(account_user=target_user).select_related("badge").order_by("-awarded_at")[:6]
        friends = profile.buddies_list().select_related("user")

        skills_data = []
        for skill in skills_qs.order_by("-created_at")[:5]:
            data = skill.skill_progress_data()
            skills_data.append({
                "name": skill.name,
                "level": skill.level,
                "progress": data["skill_progress_tracked"],
            })

        habits_data = []
        for habit in habits_qs.order_by("-created_at")[:5]:
            gd = goal_date_tracker(habit)
            habits_data.append({
                "name": habit.name,
                "progress": gd["goal_percentage"],
            })

        streak_info = streak_analytics(target_user)
        tasks_qs = Task.objects.filter(account_user=target_user)
        total_xp = (tasks_qs.filter(status=Task.COMPLETED).aggregate(total=Sum("points"))["total"] or 0) + (skills_qs.aggregate(total=Sum("xp"))["total"] or 0)

        ctx.update({
            "profile": profile,
            "profile_user": target_user,
            "target_user": target_user,
            "skills": skills_qs.order_by("-created_at")[:5],
            "habits": habits_qs.order_by("-created_at")[:5],
            "goals": goals_qs.order_by("due_date")[:5],
            "badges": badges,
            "buddy_form": BuddyRequestForm(),
            "skills_data": skills_data,
            "habits_data": habits_data,
            "login_streak": streak_info.get("login_streak", 0),
            "skills_count": skills_qs.count(),
            "friends": friends,
            "total_xp": total_xp,
            "recent_activity": [],
        })
        return ctx

class UserSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'usersettings.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx.setdefault("user_form", kwargs.get("user_form") or UserForm(instance=self.request.user))
        ctx.setdefault("profile_form", kwargs.get("profile_form") or ProfileForm(instance=profile))
        return ctx

    def post(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("user_settings")
        messages.error(request, "Please fix the errors below.")
        return self.render_to_response(self.get_context_data(user_form=user_form, profile_form=profile_form))


def dm_room_name(user_a_id: int, user_b_id: int) -> str:
    """
    Deterministic room name for a DM between two users.
    Ensures both users join the same room regardless of order.
    """
    a, b = sorted([int(user_a_id), int(user_b_id)])
    return f"dm-{a}-{b}"
class MessageView(LoginRequiredMixin, TemplateView):
    template_name = "messages.html"

    def get_context_data(self, **kwargs):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # ---- 1) Who are we chatting with? ----
        other_id = self.request.GET.get("with")
        other_user = None

        # a) Try ?with=<user_id>
        if other_id:
            try:
                other_user = User.objects.get(pk=int(other_id))
            except (User.DoesNotExist, ValueError):
                other_user = None

        # b) Fallback – first buddy if none selected
        profile = Profile.objects.filter(user=user).first()
        buddies = profile.buddies_list() if profile else []

        if other_user is None and buddies:
            other_user = buddies[0].user

        # c) Final fallback – any other profile
        if other_user is None:
            other_profile = Profile.objects.exclude(user=user).first()
            if other_profile:
                other_user = other_profile.user

        # ---- 2) Compute room name & load messages ----
        if other_user:
            room_name = dm_room_name(user.id, other_user.id)
            messages_qs = (
                ChatMessage.objects
                .filter(room=room_name)
                .select_related("sender")
                .order_by("created_at")
            )
        else:
            room_name = "dm-demo"
            messages_qs = ChatMessage.objects.none()

        # ---- 3) Attach to context for template/JS ----
        ctx["other_user"] = other_user
        ctx["room_name"] = room_name
        ctx["chat_messages"] = messages_qs
        ctx["buddies"] = buddies

        # Mark messages as seen now so we can show an unread dot elsewhere
        self.request.session["messages_last_seen_at"] = timezone.now().isoformat()
        self.request.session.modified = True

        return ctx



#----Skill Views----#
class SkillList(LoginRequiredMixin, ListView):
    model = Skill
    template_name = 'skills/list.html' 
   
    def get_queryset(self):
        return Skill.objects.filter(account_user=self.request.user).order_by('name')
      
    
class SkillCreate(LoginRequiredMixin, CreateView):   
    model = Skill
    form_class = SkillForm
    template_name = 'skills/form.html' 
    success_url = reverse_lazy('disciplinebuilder')  

    
    def form_valid(self, form):
        
        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save() 
        if Skill.objects.filter(account_user=self.request.user).count() == 1:
            award_badge(self.request.user, "FIRST_SKILL", "First Skill")
            

        return redirect(self.success_url)
     

class SkillUpdate(LoginRequiredMixin, UpdateView):
    model = Skill
    form_class = SkillForm
    template_name = 'skills/form.html'
    success_url = reverse_lazy('disciplinebuilder')


class SkillDelete(LoginRequiredMixin, DeleteView):
    model = Skill
    template_name = 'skills/confirm_delete.html'
    success_url = reverse_lazy('disciplinebuilder')







#----Habit Views----#

class HabitList(LoginRequiredMixin, ListView):
    model = Habit
    template_name = 'habits/list.html'

    def get_queryset(self):
        return Habit.objects.filter(account_user=self.request.user).order_by('name')
    

class HabitCreate(LoginRequiredMixin, CreateView):   
    model = Habit
    form_class = HabitForm
    template_name = 'habits/form.html'
    success_url = reverse_lazy('disciplinebuilder')  


    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        if Habit.objects.filter(account_user=self.request.user).count() == 1:
            award_badge(self.request.user, "First_Habit", "First_Habit" )
            
        return redirect(self.success_url)   
    
class HabitUpdate(LoginRequiredMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = 'habits/form.html'
    success_url = reverse_lazy('disciplinebuilder')


class HabitDelete(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = 'habits/confirm_delete.html'
    success_url = reverse_lazy('disciplinebuilder')


#----Journal Views----#
class JournalList(LoginRequiredMixin, ListView):
    model = Journal
    template_name = 'journal/list.html'

    def get_queryset(self):
        return Journal.objects.filter(account_user=self.request.user).order_by('-date', 'id')
    
class JournalCreate(LoginRequiredMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = 'journal/form.html'
    success_url = reverse_lazy('disciplinebuilder')


    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        journal_entry_create(obj)

        post = self.request.POST
        mood_score = post.get("mood_score")
        mood_type = post.get("mood_type")
        energy_level = post.get("energy_level")
        sleep_hours = post.get("sleep_hours")
        stress_level = post.get("stress_level")
        social_interaction = post.get("social_interaction")

        create_mood_entry(
            account_user=self.request.user,
            mood_score=mood_score,
            mood_type=mood_type,
            note=obj.note,
            related_goal=None,
            energy_level=energy_level,
            sleep_hours=sleep_hours,
            stress_level=stress_level,
            social_interaction=social_interaction,
            timestamp=obj.date,
        )
        return redirect(self.success_url)
    

class JournalUpdate(LoginRequiredMixin, UpdateView):
    model = Journal
    form_class = JournalForm
    template_name = 'journal/form.html'
    success_url = reverse_lazy('disciplinebuilder')
class JournalDelete(LoginRequiredMixin, DeleteView):
    model = Journal
    template_name = 'journal/confirm_delete.html'
    success_url = reverse_lazy('disciplinebuilder')
#----Reward Views----#                          

class RewardList(LoginRequiredMixin, ListView):
    model = Reward
    template_name = 'rewards/reward_list.html'

   

class RewardCreate(LoginRequiredMixin, CreateView):
    model = Reward
    form_class = RewardForm
    template_name = 'rewards/form.html'
    success_url = reverse_lazy('reward-list')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        return redirect(self.success_url)

class RewardUpdate(LoginRequiredMixin, UpdateView):
    model = Reward
    form_class = RewardForm
    template_name = 'rewards/form.html'
    success_url = reverse_lazy('reward-list')

class RewardDelete(LoginRequiredMixin, DeleteView):
    model = Reward
    template_name = 'rewards/confirm_delete.html'
    success_url = reverse_lazy('reward-list')

#----Task Views----#   
class TaskList(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/list.html'

    def get_queryset(self):
        return Task.objects.filter(account_user=self.request.user).order_by('-date', 'id')
    
class TaskCreate(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    success_url = reverse_lazy('disciplinebuilder')


    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.account_user = self.request.user
        if obj.status == Task.COMPLETED and obj.completed_at is None:
            obj.completed_at = timezone.now()
        obj.save()
        task_completion_badge(obj)

        post = self.request.POST
        mood_score = post.get("mood_score")
        mood_type = post.get("mood_type")
        energy_level = post.get("energy_level")
        sleep_hours = post.get("sleep_hours")
        stress_level = post.get("stress_level")
        social_interaction = post.get("social_interaction")

        if mood_score:
            create_mood_entry(
                account_user=self.request.user,
                mood_score=mood_score,
                mood_type=mood_type,
                note=obj.description,
                related_goal=None,
                energy_level=energy_level,
                sleep_hours=sleep_hours,
                stress_level=stress_level,
                social_interaction=social_interaction,
                timestamp=obj.date,
            )

        return redirect(self.success_url)
    
class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    success_url = reverse_lazy('disciplinebuilder')

#----- added to award badge and points for task completion mile stones
    def form_valid(self, form):
        prev = Task.objects.get(pk=self.object.pk)
        current = form.save(commit=False)

        # Track completion timestamp
        if current.status == Task.COMPLETED:
            if prev.status != Task.COMPLETED:
                current.completed_at = timezone.now()
        else:
            current.completed_at = None

        current.save()

        if prev.status != Task.COMPLETED and current.status == Task.COMPLETED:
            task_completion_badge(current)
        return redirect(self.success_url)
    

class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'
    success_url = reverse_lazy('disciplinebuilder')



class GoalList(LoginRequiredMixin, ListView):
    model = Goals
    template_name = 'goals/list.html'
    
    
    def get_queryset(self):
        return Goals.objects.filter(account_user=self.request.user).order_by('title')

class GoalCreate(LoginRequiredMixin, CreateView):
    model = Goals
    form_class =  GoalForm
    template_name = 'goals/form.html'
    success_url = reverse_lazy('disciplinebuilder')

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.account_user = self.request.user
      
        obj.save()

        return redirect(self.success_url)
    

class GoalUpdate(LoginRequiredMixin, UpdateView):
    model = Goals
    form_class = GoalForm
    template_name = 'goals/form.html'
    success_url = reverse_lazy('disciplinebuilder')
    
    def form_valid(self, form):
        old_status =  Goals.objects.get(pk=self.object.pk).status
        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save() 
        if old_status != 'completed':
          goal_award_updater(obj)
        return redirect(self.success_url)




class GoalDelete(LoginRequiredMixin, DeleteView):
    model = Goals
    template_name = 'goals/confirm_delete.html'
    success_url = reverse_lazy('disciplinebuilder')



class MoodList(LoginRequiredMixin, ListView):
    model = Mood
    template_name = 'mood/list.html'
    
    
    def get_queryset(self):
        return Mood.objects.filter(user=self.request.user).order_by('mood_score')
    
class MoodCreate(LoginRequiredMixin, CreateView):
    model = Mood
    form_class =  MoodForm
    template_name = 'mood/form.html'

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return redirect(self.success_url)

class MoodUpdate(LoginRequiredMixin, UpdateView):
    model = Mood
    form_class = MoodForm
    template_name = 'mood/form.html'
    success_url = reverse_lazy('disciplinebuilder')

class MoodDelete(LoginRequiredMixin, DeleteView):
    model = Mood
    template_name = 'mood/confirm_delete.html'
    success_url = reverse_lazy('disciplinebuilder')



#----Profile Views----#   

class ProfileList(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'profiles/list.html'

    

class ProfileCreate(LoginRequiredMixin, CreateView):
    model = Profile
    template_name = 'profiles/form.html' 
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return redirect(self.success_url)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'profiles/form.html'
    success_url = reverse_lazy('dashboard')
    
    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        messages.success(self.request, f"Hi, {self.request.user.username}!")
        return redirect(self.success_url)



class ProfileDelete(LoginRequiredMixin, DeleteView):
    model = Profile
    template_name = 'profiles/confirm_delete.html'
    success_url = reverse_lazy('dashboard')

class ForumCreateView(LoginRequiredMixin, CreateView):
    model = Forum
    form_class = ForumForm
    template_name = 'forum/forum_create_form.html'
    success_url = reverse_lazy('community')

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.save()
        messages.success(self.request, "Discussion thread created.")
        return redirect("community_thread", pk=obj.pk)

class ForumDetailView(LoginRequiredMixin, DetailView):
    model= Forum
    template_name = "forum/forum_detail.html"
    context_object_name = "forum"
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum = self.object
        context["posts"] = forum.post_set.select_related("author").order_by("created_at")
        context["form"] = PostForm()
        context["locked"] = forum.locked_forum
        context["up_count"] = ForumVote.objects.filter(forum=forum, value=ForumVote.UP).count()
        context["down_count"] = ForumVote.objects.filter(forum=forum, value=ForumVote.DOWN).count()
        context["user_vote"] = ForumVote.objects.filter(forum=forum, user=self.request.user).values_list("value", flat=True).first()
        return context
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        body = (request.POST.get("body") or "").strip()

        if self.object.locked_forum:
            messages.error(request, "This thread is locked.")
            return redirect("community_thread", pk=self.object.pk)

        if not body:
            messages.error(request, "Reply cannot be empty.")
            return redirect("community_thread", pk=self.object.pk)

        Post.objects.create(
            forum=self.object,
            author=request.user,
            body=body,
        )

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            comment_count = Post.objects.filter(forum=self.object).count()
            return JsonResponse({"ok": True, "comment_count": comment_count})

        messages.success(request, "Reply posted.")
        return redirect("community_thread", pk=self.object.pk)


class ForumDeleteView(LoginRequiredMixin, DeleteView):
    model = Forum
    success_url = reverse_lazy("community")

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user:
            messages.error(request, "You can only delete your own discussion.")
            return redirect("community_thread", pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)


class BuddiesView(LoginRequiredMixin, TemplateView):
    template_name = "buddies.html"
    login_url = "login"  # adjust to your login route name

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx["buddies"] = profile.buddies_list()
        ctx["incoming"] = BuddyRequest.objects.filter(receiver=profile, status=BuddyRequest.PENDING)
        ctx["outgoing"] = BuddyRequest.objects.filter(sender=profile, status=BuddyRequest.PENDING)
        ctx["form"] = BuddyRequestForm()
        ctx["respond_form"] = BuddyRespondForm()
        return ctx

class BuddySendView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        form = BuddyRequestForm(request.POST)
        if form.is_valid():
            receiver = form.cleaned_data["receiver"]
            sender_profile, _ = Profile.objects.get_or_create(user=request.user)
            if receiver == sender_profile:
                messages.error(request, "You cannot buddy yourself.")
            else:
                obj, created = BuddyRequest.objects.get_or_create(
                    sender=sender_profile,
                    receiver=receiver,
                    defaults={"status": BuddyRequest.PENDING},
                )
                if created:
                    messages.success(request, f"Buddy request sent to {receiver.user.username}.")
                else:
                    messages.info(request, "Buddy request already exists.")
        return redirect("buddies")

class BuddyRespondView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, *args, **kwargs):
        form = BuddyRespondForm(request.POST)
        if not form.is_valid():
            return redirect("buddies")

        buddy_req = get_object_or_404(BuddyRequest, pk=form.cleaned_data["request_id"])
        action = form.cleaned_data["action"]
        profile, _ = Profile.objects.get_or_create(user=request.user)

        if action == BuddyRespondForm.ACTION_ACCEPT and buddy_req.receiver == profile:
            buddy_req.accept()
            messages.success(request, f"You are now buddies with {buddy_req.sender.user.username}.")
        elif action == BuddyRespondForm.ACTION_DECLINE and buddy_req.receiver == profile:
            buddy_req.decline()
            messages.info(request, "Buddy request declined.")
        elif action == BuddyRespondForm.ACTION_CANCEL and buddy_req.sender == profile:
            buddy_req.cancel()
            messages.info(request, "Buddy request canceled.")
        else:
            messages.error(request, "Not authorized for that action.")
        return redirect("buddies")

class BuddyRemoveView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request, user_id, *args, **kwargs):
        buddy_profile = get_object_or_404(Profile, pk=user_id)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        Friendship.objects.filter(requester=profile, buddy=buddy_profile).delete()
        Friendship.objects.filter(requester=buddy_profile, buddy=profile).delete()
        messages.info(request, f"Removed {buddy_profile.user.username} from buddies.")
        return redirect("buddies")

