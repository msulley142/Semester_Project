from django import forms
from django.contrib.auth import get_user_model
from .models import Skill, Habit, Journal, Reward, Task, Profile, User




class SkillForm(forms.ModelForm):

    class Meta:
        model = Skill
        fields = ['name', 'description']


class HabitForm(forms.ModelForm):

    class Meta:
        model = Habit
        fields = ['name', 'habit_type', 'goal_start', 'goal_end', 'description']

      

class RewardForm(forms.ModelForm):
    
    class Meta:
        model = Reward
        fields = ['tokens']

class JournalForm(forms.ModelForm):

    class Meta:
        model = Journal
        fields = [ "entry_type", "skill", "habit", "date",
            "trigger", "note"]

        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class TaskForm(forms.ModelForm):
    
    class Meta:
        model = Task
        fields = ["title", "points" ,"skill", "habit", "status", "description", "date"]

class UserForm(forms.ModelForm):
        class Meta:
            model = User
            fields = ["first_name", "last_name", "email"]



class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'profile_picture']

