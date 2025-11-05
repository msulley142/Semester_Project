from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView



from django.urls import reverse_lazy
from django.shortcuts import redirect
from .models import Skill,  Habit, Reward, Journal, Badge, User_Badge,Task
from .forms import SkillForm, HabitForm, JournalForm, RewardForm, TaskForm
from calibration_app.progress_tracker import task_completion_badge, award_badge, journal_entry_create, streak_notify, abst_badge 



# Create your views here.

#----Login View----#

class LoginView(FormView):
    template_name = 'auth/login.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)


#----Signup View----#

class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('login')


#----Dashboard View----#

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_skills'] = Skill.objects.filter(account_user=self.request.user).order_by('-created_at')[:5]
        context['recent_habits'] = Habit.objects.filter(account_user=self.request.user).order_by('-created_at')[:5]
        context['recent_badges'] = User_Badge.objects.filter(account_user=self.request.user).order_by('-awarded_at')[:5]
        context['recent_journal'] = Journal.objects.filter(account_user=self.request.user).order_by('-date', 'id')[:5]
        return context

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
    success_url = reverse_lazy('skill_list')  

    
    

    def form_valid(self, form):
        
        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save() 
        if Skill.objects.filter(account_user=self.request.user).count() == 1:
            award_badge(self.request.user, "First_Skill", "First_SKill" )
            

        return redirect(self.success_url)
    
 

class SkillUpdate(LoginRequiredMixin, UpdateView):
    model = Skill
    form_class = SkillForm
    template_name = 'skills/form.html'
    success_url = reverse_lazy('skill_list')


class SkillDelete(LoginRequiredMixin, DeleteView):
    model = Skill
    template_name = 'skills/confirm_delete.html'
    success_url = reverse_lazy('skill_list')


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
    success_url = reverse_lazy('habit_list')  


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
    success_url = reverse_lazy('habit_list')


class HabitDelete(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = 'habits/confirm_delete.html'
    success_url = reverse_lazy('habit_list')


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
    success_url = reverse_lazy('journal_list')


    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        journal_entry_create(obj)
        return redirect(self.success_url)
    

class JournalUpdate(LoginRequiredMixin, UpdateView):
    model = Journal
    form_class = JournalForm
    template_name = 'journal/form.html'
    success_url = reverse_lazy('journal_list')
class JournalDelete(LoginRequiredMixin, DeleteView):
    model = Journal
    template_name = 'journal/confirm_delete.html'
    success_url = reverse_lazy('journal_list')
#----Reward Views----#                          

class RewardList(LoginRequiredMixin, ListView):
    model = Reward
    template_name = 'rewards/reward_list.html'

    def get_queryset(self):
        return Reward.objects.filter(account_user=self.request.user).order_by('-awarded_at')

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
    success_url = reverse_lazy('task_list')


    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        return redirect(self.success_url)
    
class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    success_url = reverse_lazy('task_list')

class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'
    success_url = reverse_lazy('task_list')
    
