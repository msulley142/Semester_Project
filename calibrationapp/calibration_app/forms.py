from django import forms
from django.contrib.auth.models import User
from .models import Skill, Habit, Journal, Task, Profile, Mood, Goals, Forum,  Post, BuddyRequest

from .models import CommunityGroup



class SkillForm(forms.ModelForm):

    class Meta:
        model = Skill
        fields = ['name', 'description']


class HabitForm(forms.ModelForm):

    class Meta:
        model = Habit
        fields = ['name', 'habit_type', 'goal_start', 'goal_end', 'description']




class JournalForm(forms.ModelForm):

    class Meta:
        model = Journal
        fields = [ "entry_type", "skill", "habit", "date", "trigger", "note"]

        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class TaskForm(forms.ModelForm):
    
    class Meta:
        model = Task
        fields = ["title", "points" ,"skill", "habit", "status", "description", "date"]




class GoalForm(forms.ModelForm):

    class Meta:
        model = Goals
        fields = ["title", "description", "goal_type","skill", "habit", "start_date", "due_date", "status", "priority", "reason", "reflection", "target_value", "current_value"]


class MoodForm(forms.ModelForm):

    class Meta:
        model = Mood
        fields = ["mood_score", "mood_type", "note", "energy_level", "stress_level", "related_goal" , "timestamp"] 

class UserForm(forms.ModelForm):
        class Meta:
            model = User
            fields = ["first_name", "last_name", "email"]



class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['phone_number', 'bio', 'profile_picture']





class ForumForm(forms.ModelForm):

   class Meta:
        model = Forum
        fields = ["topic", "title", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 6}),
        }
 
class PostForm(forms.ModelForm):
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


class CommunityGroupForm(forms.ModelForm):
    class Meta:
        model = CommunityGroup
        fields = ["name", "category", "tagline", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
