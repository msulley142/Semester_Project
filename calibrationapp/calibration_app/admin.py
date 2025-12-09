from django.contrib import admin

from .models import (
    Badge,
    BuddyRequest,
    ChatMessage,
    CommunityGroup,
    Forum,
    ForumVote,
    Friendship,
    Goals,
    Habit,
    Journal,
    Mood,
    Post,
    Profile,
    Reward,
    Skill,
    Task,
    Topics,
    UserBlock,
    User_Badge,
)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "account_user", "level", "xp", "created_at")
    search_fields = ("name", "account_user__username")
    list_filter = ("level",)
    ordering = ("-created_at",)


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "account_user", "habit_type", "goal_start", "goal_end", "created_at")
    search_fields = ("name", "account_user__username")
    list_filter = ("habit_type",)
    ordering = ("-created_at",)


@admin.register(Goals)
class GoalsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "account_user",
        "goal_type",
        "status",
        "priority",
        "start_date",
        "due_date",
        "target_value",
        "current_value",
    )
    search_fields = ("title", "account_user__username")
    list_filter = ("goal_type", "status", "priority")
    ordering = ("-updated_at",)


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("account_user", "tokens")
    search_fields = ("account_user__username",)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("title", "code")
    search_fields = ("title", "code")


@admin.register(User_Badge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("account_user", "badge", "awarded_at")
    search_fields = ("account_user__username", "badge__title", "badge__code")
    list_filter = ("badge",)
    ordering = ("-awarded_at",)


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ("user", "mood_score", "mood_type", "related_goal", "timestamp")
    search_fields = ("user__username", "note")
    list_filter = ("mood_type", "timestamp")
    ordering = ("-timestamp",)


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("account_user", "entry_type", "skill", "habit", "date")
    search_fields = ("account_user__username", "trigger", "note")
    list_filter = ("entry_type",)
    ordering = ("-date",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "account_user", "status", "points", "date", "completed_at")
    search_fields = ("title", "account_user__username")
    list_filter = ("status",)
    ordering = ("-date", "-id")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number")
    search_fields = ("user__username", "phone_number")


@admin.register(Topics)
class TopicsAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "member_total", "created_at")
    search_fields = ("name", "tagline")
    list_filter = ("category",)
    ordering = ("name",)

    def member_total(self, obj):
        return obj.members.count()

    member_total.short_description = "Members"


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "topic", "group", "created_at", "locked_forum")
    search_fields = ("title", "author__username", "body")
    list_filter = ("locked_forum", "topic", "group")
    ordering = ("-created_at",)


@admin.register(ForumVote)
class ForumVoteAdmin(admin.ModelAdmin):
    list_display = ("forum", "user", "value", "created_at")
    search_fields = ("forum__title", "user__username")
    list_filter = ("value",)
    ordering = ("-created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("forum", "author", "created_at")
    search_fields = ("body", "author__username", "forum__title")
    ordering = ("created_at",)


@admin.register(BuddyRequest)
class BuddyRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at", "updated_at")
    search_fields = ("sender__user__username", "receiver__user__username")
    list_filter = ("status",)
    ordering = ("-created_at",)


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("requester", "buddy", "created_at")
    search_fields = ("requester__user__username", "buddy__user__username")
    ordering = ("-created_at",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("room", "sender", "created_at")
    search_fields = ("room", "sender__username", "body")
    ordering = ("-created_at",)


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked", "created_at")
    search_fields = ("blocker__username", "blocked__username")
    ordering = ("-created_at",)
