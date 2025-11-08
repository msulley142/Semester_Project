from django.db.models import Max
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView

from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth import login
from .models import Skill,  Habit, Reward, Journal, Badge, User_Badge,Task, Profile
from .forms import SkillForm, HabitForm, JournalForm, RewardForm, TaskForm, ProfileForm, UserForm
from django.contrib import messages
from django.utils.timezone import make_aware
from datetime import datetime
from calibration_app.progress_tracker import task_completion_badge, award_badge, journal_entry_create,  streak_notify, abst_badge, goal_date_tracker




# Create your views here.
#----Landing View---#



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
        latest_skills_t = (Skill.objects.filter(account_user=self.request.user, journal__account_user=self.request.user).annotate(latest_entry=Max('journal__date')).exclude(latest_entry=None).order_by('-latest_entry')[:2]  )
        temp = []
        for skill in latest_skills_t:
            data = skill.skill_progress_data()
            skill.skill_progress_tracked = data["skill_progress_tracked"]
            skill.to_level_up = data["to_level_up"]
            skill.left_over = data["left_over"]
            temp.append(skill)

        context['latest_skills'] = temp

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

        context['recent_habits'] = temp2
        context['recent_badges'] = User_Badge.objects.filter(account_user=self.request.user).order_by('-awarded_at')[:3]
        context['current_task'] =  Task.objects.filter(account_user=self.request.user).order_by('-date', '-id')[:2]
        #context['recent_journal'] = Journal.objects.filter(account_user=self.request.user).order_by('-date', 'id')[:5]
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

    
        return context
     
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
         
         if skill_user:
             try: user_entry.skill = Skill.objects.get(id=skill_user, acount_user=request.user)
             except Skill.DoesNotExist: pass
         if habit_user:
             try: user_entry.habit = Habit.objects.get(id=habit_user, acount_user=request.user)
             except Habit.DoesNotExist: pass

         if skill_user and habit_user:
             messages.error(request, "Only one option is allowed.")
             return redirect('disciplinebuilder')

         user_entry.save()
         messages.success(request, "Journal entry saved")
         return redirect('disciplinebuilder')
        
     
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
             try: user_task.skill = Skill.objects.get(id=user_skill, acount_user=request.user)
             except Skill.DoesNotExist: pass
         if habit_user1:
             try: user_skill.habit = Habit.objects.get(id=habit_user1, acount_user=request.user)
             except Habit.DoesNotExist: pass

         if user_skill and habit_user1:
             messages.error(request, "Only one option is allowed.")
             return redirect('disciplinebuilder')

         user_task.save()
         messages.success(request, "Task entry saved")
         return redirect('disciplinebuilder')
                                                  
         
     


class ProgressTrackerView(LoginRequiredMixin, TemplateView):
    template_name = 'progresstracker.html'

class RewardsTrackerView(LoginRequiredMixin, TemplateView):
    template_name = 'rewards.html'

class CommunityView(LoginRequiredMixin, TemplateView):
    template_name = 'community.html'
class CoachingView(LoginRequiredMixin, TemplateView):
    template_name = 'coaching.html'
class MessageView(LoginRequiredMixin, TemplateView):
    template_name = 'messages.html'
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
            award_badge(self.request.user, "First_Skill", "First_SKill" )
            

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
    success_url = reverse_lazy('disciplinebuilder')


    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.account_user = self.request.user
        obj.save()
        task_completion_badge(obj)
        return redirect(self.success_url)
    
class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    success_url = reverse_lazy('disciplinebuilder')

#----- added to award badge and points for task completion mile stones
    def form_valid(self, form):
        prev_status = Task.objects.get(pk = self.object.pk).status
        current_status = form.save()
        if prev_status != Task.COMPLETED:
            task_completion_badge(current_status)
        return redirect(self.success_url)
    

class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'
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


    
