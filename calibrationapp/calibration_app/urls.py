from django.urls import path
from . import crudviews, socialview, views

urlpatterns = [

#-----Skill URLs-----#
    path('skills/', crudviews.SkillList.as_view(), name='skill_list'),
    path('skills/create/', crudviews.SkillCreate.as_view(), name='skill_create'),
    path('skills/<int:pk>/edit/', crudviews.SkillUpdate.as_view(), name='skill_update'),
    path('skills/<int:pk>/delete/', crudviews.SkillDelete.as_view(), name='skill_delete'),

#-----Habit URLs-----#
    path('habits/', crudviews.HabitList.as_view(), name='habit_list'),
    path('habits/create/', crudviews.HabitCreate.as_view(), name='habit_create'),
    path('habits/<int:pk>/edit/', crudviews.HabitUpdate.as_view(), name='habit_update'),
    path('habits/<int:pk>/delete/', crudviews.HabitDelete.as_view(), name='habit_delete'),



#-----Journal Entry URLs-----#
    path('journals/', crudviews.JournalList.as_view(), name='journal_list'),
    path('journals/create/', crudviews.JournalCreate.as_view(), name='journal_create'),
    path('journals/<int:pk>/edit/', crudviews.JournalUpdate.as_view(), name='journal_update'),
    path('journals/<int:pk>/delete/', crudviews.JournalDelete.as_view(), name='journal_delete'),

#-----Task Entry URL-----#
    path('tasks/', crudviews.TaskList.as_view(), name='task_list'),
    path('tasks/create/', crudviews.TaskCreate.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', crudviews.TaskUpdate.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete', crudviews.TaskDelete.as_view(), name= 'task_delete'),
    path('tasks/<int:pk>/complete/', crudviews.TaskCompleteView.as_view(), name='task_complete'),

#-----Reward Entry URLs----#
    path('goals/', crudviews.GoalList.as_view(), name='goal_list'),
    path('goals/create/', crudviews.GoalCreate.as_view(), name='goal_create'),
    path('goals/<int:pk>/edit/', crudviews.GoalUpdate.as_view(), name='goal_update'),
    path('goals/<int:pk>/delete', crudviews.GoalDelete.as_view(), name= 'goal_delete'),
    path('goals/<int:pk>/complete/', crudviews.GoalCompleteView.as_view(), name='goal_complete'),
   


    path('moods/', crudviews.MoodList.as_view(), name='mood_list'),
    path('moods/create/', crudviews.MoodCreate.as_view(), name='mood_create'),
    path('moods/<int:pk>/edit/', crudviews.MoodUpdate.as_view(), name='mood_update'),
    path('moods/<int:pk>/delete', crudviews.MoodDelete.as_view(), name= 'mood_delete'),
   

    path("community/", socialview.CommunityView.as_view(), name="community"),
    path("community/new/", socialview.ForumCreateView.as_view(), name="community_new_thread"),
    path("community/thread/<int:pk>/", socialview.ForumDetailView.as_view(), name="community_thread"),
    path("community/thread/<int:pk>/vote/", socialview.forum_vote, name="forum_vote"),
    path("community/thread/<int:pk>/delete/", socialview.ForumDeleteView.as_view(), name="community_thread_delete"),
    path("community/group/<int:pk>/join/", socialview.GroupJoinView.as_view(), name="group_join"),
    path("community/group/<int:pk>/leave/", socialview.GroupLeaveView.as_view(), name="group_leave"),
    path("community/groups/create/", socialview.GroupCreateView.as_view(), name="group_create"),
    path("groups/<int:group_id>/threads/new/", socialview.GroupThreadCreateView.as_view(), name="group_thread_create"),
    path("groups/<int:group_id>/threads/<int:pk>/", socialview.GroupThreadDetailView.as_view(), name="group_thread_detail"),
    path("groups/<int:group_id>/threads/<int:thread_id>/reply/", socialview.GroupThreadReplyView.as_view(), name="group_thread_reply"),
    path("groups/<int:pk>/", socialview.GroupDetailView.as_view(), name="group_detail"),
    path("groups/", socialview.GroupsView.as_view(), name="groups"),
    path("profile/<int:user_id>/", socialview.VisitorProfileView.as_view(), name="visitor_profile"),

    path("buddies/", socialview.BuddiesView.as_view(), name="buddies"),
    path("buddies/send/", socialview.BuddySendView.as_view(), name="buddy-send"),
    path("buddies/respond/", socialview.BuddyRespondView.as_view(), name="buddy-respond"),
    path("buddies/remove/<int:user_id>/", socialview.BuddyRemoveView.as_view(), name="buddy-remove"),
    path("blocks/<int:user_id>/", socialview.BlockUserView.as_view(), name="block-user"),
    path("blocks/<int:user_id>/unblock/", socialview.UnblockUserView.as_view(), name="unblock-user"),


]
