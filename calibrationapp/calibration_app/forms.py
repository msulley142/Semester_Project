from django import forms
from django.contrib.auth.models import User
from .models import Skill, Habit, Journal, Task, Profile, Mood, Goals, Forum,  Post, BuddyRequest
from .models import CommunityGroup
from .utils import sanitize_text

# Mixin to sanitize specified text fields in forms
class SanitizedFormMixin:
    sanitize_fields = []

    def clean(self):
        cleaned = super().clean()
        for field in self.sanitize_fields:
            if field in cleaned:
                cleaned[field] = sanitize_text(cleaned.get(field))
        return cleaned



class SkillForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["name", "description"]

    class Meta:
        model = Skill
        fields = ['name', 'description']


class HabitForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["name", "description"]

    class Meta:
        model = Habit
        fields = ['name', 'habit_type', 'goal_start', 'goal_end', 'description']




class JournalForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["trigger", "note"]

    class Meta:
        model = Journal
        fields = [ "entry_type", "skill", "habit", "date", "trigger", "note"]

        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class TaskForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["title", "description"]

    class Meta:
        model = Task
        fields = ["title", "points" ,"skill", "habit", "status", "description", "date"]




class GoalForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["title", "description", "reason", "reflection"]

    class Meta:
        model = Goals
        fields = ["title", "description", "goal_type","skill", "habit", "start_date", "due_date", "status", "priority", "reason", "reflection", "target_value", "current_value"]


class MoodForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["note"]

    class Meta:
        model = Mood
        fields = ["mood_score", "mood_type", "note", "energy_level", "stress_level", "related_goal" , "timestamp"] 

class UserForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["first_name", "last_name", "email"]

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]



class ProfileForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["phone_number", "bio"]

    class Meta:
        model = Profile
        fields = ['phone_number', 'bio', 'profile_picture']





class ForumForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["title", "body"]

    class Meta:
        model = Forum
        fields = ["topic", "title", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 6}),
        }
 
class PostForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["body"]

    class Meta:
        model = Post
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4, "placeholder": "Share your thoughts"}),
        }



class BuddyRequestForm(forms.ModelForm):
    class Meta:
        model = BuddyRequest
        fields = ["receiver"]

class BuddyRespondForm(forms.Form):
    ACTION_ACCEPT, ACTION_DECLINE, ACTION_CANCEL = ("accept", "decline", "cancel")
    ACTION_CHOICES = [
        (ACTION_ACCEPT, "Accept"),
        (ACTION_DECLINE, "Decline"),
        (ACTION_CANCEL, "Cancel"),
    ]
    request_id = forms.IntegerField(widget=forms.HiddenInput)
    action = forms.ChoiceField(choices=ACTION_CHOICES)


class CommunityGroupForm(SanitizedFormMixin, forms.ModelForm):
    sanitize_fields = ["name", "tagline", "description"]

    class Meta:
        model = CommunityGroup
        fields = ["name", "category", "tagline", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
