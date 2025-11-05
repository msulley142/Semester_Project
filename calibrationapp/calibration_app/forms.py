from django import forms
from .models import Skill, Habit, Journal, Reward, Task




class SkillForm(forms.ModelForm):

    class Meta:
        model = Skill
        fields = ['name', 'description']


class HabitForm(forms.ModelForm):

    class Meta:
        model = Habit
        fields = ['name',  'description', 'habit_type', 'frequency']

      

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
