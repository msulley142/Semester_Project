
from django.contrib import admin
from .models import Skill,  Habit, Journal, Reward, Badge, User_Badge,  Task, Goals, Mood, Forum, Topics, Post

# The following functions were completed by Githubs coplit assistant. It's sugesstions were acurate and saved time. No prompt used.   
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_user', 'xp', 'created_at')
    search_fields = ('name', 'account_user_username')


class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "account_user", "habit_type", "frequency", "created_at")
    search_fields = ("name", "account_user_username")
    list_filter = ("habit_type",)

class JournalAdmin(admin.ModelAdmin):
    list_display = ("habit", "skill", "date", "value", "completed")
    
    search_fields = ("habit__name", "skill_name", 'completed')
    list_filter = ("completed",)

class RewardAdmin(admin.ModelAdmin):
    list_display = ("user", "tokens")
    search_fields = ("user__username",)

class BadgeAdmin(admin.ModelAdmin):
    list_display = ("title", "code")
    search_fields = ("title", "code")

class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    search_fields = ("user_username", "badge_title") 


class TaskAdmin(admin.ModelAdmin):
    list_display = ("user", 'title', 'points' 'skill', 'habit', 'status', 'descritpion', 'date' )
    search_fields = ("user_username",'title')
    list_filter = ('status')

class GoalAdmin(admin.ModelAdmin):
    list_display = ("user", 'title', 'goal_type' 'skill' 'habit', 'metric', 'target_value', 'current_value', 'start_date', 'due_date',  'status', 'descritpion', 'priority' )
    search_fields = ("user_username",'title')
    list_filter = ('status')


class TopicsAdmin(admin.ModelAdmin):
    list_display = ("name",  "description")
    search_fields = ("name")
    list_filter =("name")

class ForumAdmin(admin.ModelAdmin):
    list_display = ("topic", "author", "title", "body", "created_at", "updated_at", "locked_forum")
    search_fields = ("forum", "author", "title")
    list_filter = ("forum", "author", "title", "created_at", "updated_at")

class PostAdmin(admin.ModelAdmin):
    list_display = ( "forum", "author", "body", "created_at", "updated_at")
    search_fields = ("forum", "created_at", "updated_at")
    list_filter =("forum", "author", "created_at")


# Register your models here.
admin.site.register(Skill)
admin.site.register(Habit)
admin.site.register(Journal)
admin.site.register(Reward)
admin.site.register(Badge)
admin.site.register(User_Badge)
admin.site.register(Task)
admin.site.register(Goals)
admin.site.register(Mood)
admin.site.register(Forum)
admin.site.register(Post)
admin.site.register(Topics)