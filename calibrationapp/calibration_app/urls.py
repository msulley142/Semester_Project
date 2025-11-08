from django.urls import path
from . import views

urlpatterns = [

#-----Skill URLs-----#
    path('skills/', views.SkillList.as_view(), name='skill_list'),
    path('skills/create/', views.SkillCreate.as_view(), name='skill_create'),
    path('skills/<int:pk>/edit/', views.SkillUpdate.as_view(), name='skill_update'),
    path('skills/<int:pk>/delete/', views.SkillDelete.as_view(), name='skill_delete'),

#-----Habit URLs-----#
    path('habits/', views.HabitList.as_view(), name='habit_list'),
    path('habits/create/', views.HabitCreate.as_view(), name='habit_create'),
    path('habits/<int:pk>/edit/', views.HabitUpdate.as_view(), name='habit_update'),
    path('habits/<int:pk>/delete/', views.HabitDelete.as_view(), name='habit_delete'),



#-----Journal Entry URLs-----#
    path('journals/', views.JournalList.as_view(), name='journal_list'),
    path('journals/create/', views.JournalCreate.as_view(), name='journal_create'),
    path('journals/<int:pk>/edit/', views.JournalUpdate.as_view(), name='journal_update'),
    path('journals/<int:pk>/delete/', views.JournalDelete.as_view(), name='journal_delete'),

#-----Task Entry URL-----#
    path('tasks/', views.TaskList.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreate.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdate.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete', views.TaskDelete.as_view(), name= 'task_delete'),

#-----Reward Entry URLs----#

   


]