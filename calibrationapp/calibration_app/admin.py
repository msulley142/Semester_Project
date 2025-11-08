
from django.contrib import admin
from .models import Skill,  Habit, Journal, Reward, Badge, User_Badge, Quest, Task

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

class QuestAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "description", "is_completed", "created_at")
    search_fields = ("user__username", "title")
    list_filter = ("is_completed")


class TaskAdmin(admin.ModelAdmin):
    list_display = ("user", 'title', 'points' 'skill', 'habit', 'status', 'descritpion', 'date' )
    search_fields = ("user_username",'title')
    list_filter = ('status')

# Register your models here.
admin.site.register(Skill)
admin.site.register(Habit)
admin.site.register(Journal)
admin.site.register(Reward)
admin.site.register(Badge)
admin.site.register(User_Badge)
admin.site.register(Quest)

admin.site.register(Task)