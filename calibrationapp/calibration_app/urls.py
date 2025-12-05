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
    path('goals/', views.GoalList.as_view(), name='goal_list'),
    path('goals/create/', views.GoalCreate.as_view(), name='goal_create'),
    path('goals/<int:pk>/edit/', views.GoalUpdate.as_view(), name='goal_update'),
    path('goals/<int:pk>/delete', views.GoalDelete.as_view(), name= 'goal_delete'),
   


    path('moods/', views.MoodList.as_view(), name='mood_list'),
    path('moods/create/', views.MoodCreate.as_view(), name='mood_create'),
    path('moods/<int:pk>/edit/', views.MoodUpdate.as_view(), name='mood_update'),
    path('moods/<int:pk>/delete', views.MoodDelete.as_view(), name= 'mood_delete'),
   

    path("community/", views.CommunityView.as_view(), name="community"),
    path("community/new/", views.ForumCreateView.as_view(), name="community_new_thread"),
    path("community/thread/<int:pk>/", views.ForumDetailView.as_view(), name="community_thread"),
    path("community/thread/<int:pk>/vote/", views.forum_vote, name="forum_vote"),
    path("community/thread/<int:pk>/delete/", views.ForumDeleteView.as_view(), name="community_thread_delete"),
    path("profile/<int:user_id>/", views.VisitorProfileView.as_view(), name="visitor_profile"),

    path("buddies/", views.BuddiesView.as_view(), name="buddies"),
    path("buddies/send/", views.BuddySendView.as_view(), name="buddy-send"),
    path("buddies/respond/", views.BuddyRespondView.as_view(), name="buddy-respond"),
    path("buddies/remove/<int:user_id>/", views.BuddyRemoveView.as_view(), name="buddy-remove"),


]
