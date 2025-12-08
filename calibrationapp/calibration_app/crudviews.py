#CRUD class-based views for core app models.

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from calibration_app.mood_tracker import create_mood_entry
from calibration_app.progress_tracker import (
    award_badge,
    goal_award_updater,
    journal_entry_create,
    task_completion_badge,
)
from .forms import HabitForm, GoalForm, JournalForm, MoodForm, ProfileForm, SkillForm, TaskForm
from .models import Goals, Habit, Journal, Mood, Profile, Skill, Task


# ---- Skill Views ----
class SkillList(LoginRequiredMixin, ListView):
    model = Skill
    template_name = "skills/list.html"

    def get_queryset(self):
        return Skill.objects.filter(account_user=self.request.user).order_by("name")


class SkillCreate(LoginRequiredMixin, CreateView):
    model = Skill
    form_class = SkillForm
    template_name = "skills/form.html"
    success_url = reverse_lazy("disciplinebuilder")

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
    template_name = "skills/form.html"
    success_url = reverse_lazy("disciplinebuilder")


class SkillDelete(LoginRequiredMixin, DeleteView):
    model = Skill
    template_name = "skills/confirm_delete.html"
    success_url = reverse_lazy("disciplinebuilder")


# ---- Habit Views ----
class HabitList(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "habits/list.html"

    def get_queryset(self):
        return Habit.objects.filter(account_user=self.request.user).order_by("name")


class HabitCreate(LoginRequiredMixin, CreateView):
    model = Habit
    form_class = HabitForm
    template_name = "habits/form.html"
    success_url = reverse_lazy("disciplinebuilder")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        if Habit.objects.filter(account_user=self.request.user).count() == 1:
            award_badge(self.request.user, "First_Habit", "First_Habit")
        return redirect(self.success_url)


class HabitUpdate(LoginRequiredMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = "habits/form.html"
    success_url = reverse_lazy("disciplinebuilder")


class HabitDelete(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = "habits/confirm_delete.html"
    success_url = reverse_lazy("disciplinebuilder")


# ---- Journal Views ----
class JournalList(LoginRequiredMixin, ListView):
    model = Journal
    template_name = "journal/list.html"

    def get_queryset(self):
        return Journal.objects.filter(account_user=self.request.user).order_by("-date", "id")


class JournalCreate(LoginRequiredMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = "journal/form.html"
    success_url = reverse_lazy("disciplinebuilder")

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
    template_name = "journal/form.html"
    success_url = reverse_lazy("disciplinebuilder")


class JournalDelete(LoginRequiredMixin, DeleteView):
    model = Journal
    template_name = "journal/confirm_delete.html"
    success_url = reverse_lazy("disciplinebuilder")


# ---- Task Views ----
class TaskList(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/list.html"

    def get_queryset(self):
        return Task.objects.filter(account_user=self.request.user).order_by("-date", "-id")


class TaskCreate(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/form.html"
    success_url = reverse_lazy("disciplinebuilder")

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
    template_name = "tasks/form.html"
    success_url = reverse_lazy("disciplinebuilder")

    def form_valid(self, form):
        prev = Task.objects.get(pk=self.object.pk)
        current = form.save(commit=False)

        # Only stamp completed_at the first time a task is marked complete; clear if reopened
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
    template_name = "tasks/confirm_delete.html"
    success_url = reverse_lazy("disciplinebuilder")

# --- Mark Task as Complete View ----
class TaskCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        task = get_object_or_404(Task, pk=pk, account_user=request.user)
        if task.status != Task.COMPLETED:
            task.status = Task.COMPLETED
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "completed_at"])
            task_completion_badge(task)
        return redirect("dashboard")


# ---- Goal Views ----
class GoalList(LoginRequiredMixin, ListView):
    model = Goals
    template_name = "goals/list.html"

    def get_queryset(self):
        return Goals.objects.filter(account_user=self.request.user).order_by("title")


class GoalCreate(LoginRequiredMixin, CreateView):
    model = Goals
    form_class = GoalForm
    template_name = "goals/form.html"
    success_url = reverse_lazy("disciplinebuilder")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        return redirect(self.success_url)


class GoalUpdate(LoginRequiredMixin, UpdateView):
    model = Goals
    form_class = GoalForm
    template_name = "goals/form.html"
    success_url = reverse_lazy("disciplinebuilder")

    def form_valid(self, form):
        old_status = Goals.objects.get(pk=self.object.pk).status
        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        if old_status != "completed":
            goal_award_updater(obj)
        return redirect(self.success_url)


class GoalDelete(LoginRequiredMixin, DeleteView):
    model = Goals
    template_name = "goals/confirm_delete.html"
    success_url = reverse_lazy("disciplinebuilder")


class GoalCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        goal = get_object_or_404(Goals, pk=pk, account_user=request.user)
        if goal.status != "completed":
            goal.status = "completed"
            goal.save(update_fields=["status"])
            goal_award_updater(goal)
        return redirect("dashboard")


# ---- Mood Views ----
class MoodList(LoginRequiredMixin, ListView):
    model = Mood
    template_name = "mood/list.html"

    def get_queryset(self):
        return Mood.objects.filter(user=self.request.user).order_by("mood_score")


class MoodCreate(LoginRequiredMixin, CreateView):
    model = Mood
    form_class = MoodForm
    template_name = "mood/form.html"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return redirect(self.success_url)


class MoodUpdate(LoginRequiredMixin, UpdateView):
    model = Mood
    form_class = MoodForm
    template_name = "mood/form.html"
    success_url = reverse_lazy("disciplinebuilder")


class MoodDelete(LoginRequiredMixin, DeleteView):
    model = Mood
    template_name = "mood/confirm_delete.html"
    success_url = reverse_lazy("disciplinebuilder")


# ---- Profile Views ----
class ProfileList(LoginRequiredMixin, ListView):
    model = Profile
    template_name = "profiles/list.html"


class ProfileCreate(LoginRequiredMixin, CreateView):
    model = Profile
    template_name = "profiles/form.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return redirect(self.success_url)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "profiles/form.html"
    success_url = reverse_lazy("dashboard")

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
    template_name = "profiles/confirm_delete.html"
    success_url = reverse_lazy("dashboard")
