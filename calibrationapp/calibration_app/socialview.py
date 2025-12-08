from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ( CreateView, DeleteView, DetailView, TemplateView,)
from calibration_app.analytics import streak_analytics
from calibration_app.progress_tracker import goal_date_tracker
from .forms import ( BuddyRequestForm, BuddyRespondForm, CommunityGroupForm, ForumForm, PostForm, UserForm,)
from .models import ( BuddyRequest, ChatMessage, CommunityGroup, Forum, ForumVote, Friendship, Goals, Habit, Journal, Mood, Post, Profile, Reward, Skill,Task, Topics, UserBlock, User_Badge,)
from django.db.models import Sum
from django.contrib.auth import get_user_model
from .utils import sanitize_text
#The following code is heavily edited by ChatGPT.
# Social/communication views: forums, groups, buddies, messaging, and profile displays .


class CommunityView(LoginRequiredMixin, TemplateView):
    template_name = 'community.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)

        selected_topic = self.request.GET.get("topic")

        # Public threads with optional topic filter
        context["topics"] = Topics.objects.all().order_by("name")
        threads = (
            Forum.objects.select_related("topic", "author")
            .annotate(
                comment_count=Count("post"),
                up_count=Count("votes", filter=Q(votes__value=ForumVote.UP)),
                down_count=Count("votes", filter=Q(votes__value=ForumVote.DOWN)),
            )
            .filter(group__isnull=True)
            .order_by("-created_at")
        )
        if selected_topic:
            threads = threads.filter(topic_id=selected_topic)

        context["selected_topic"] = selected_topic
        context["threads"] = threads[:50]
        # Buddy request widgets on community page
        context["buddies"] = profile.buddies_list()
        context["incoming"] = BuddyRequest.objects.filter(receiver=profile, status=BuddyRequest.PENDING)
        context["outgoing"] = BuddyRequest.objects.filter(sender=profile, status=BuddyRequest.PENDING)
        context["buddy_form"] = BuddyRequestForm()
        context["respond_form"] = BuddyRespondForm()
        context["user_votes"] = dict(
            ForumVote.objects.filter(user=self.request.user).values_list("forum_id", "value")
        )
        # Simple group cards with membership flag
        groups_payload = []
        groups = CommunityGroup.objects.all().order_by("name")
        for g in groups:
            groups_payload.append({
                "obj": g,
                "is_member": g.members.filter(pk=profile.pk).exists(),
                "member_count": g.members.count(),
            })
        context["groups"] = groups_payload
        context["group_form"] = CommunityGroupForm()

        return context 

    def post(self, request, *args, **kwargs):
        # Create a new public forum thread (or topic on the fly)
        topic_id = request.POST.get("topic")
        topic_name = sanitize_text((request.POST.get("topic_name") or "").strip())
        title = sanitize_text((request.POST.get("title") or "").strip())
        body = sanitize_text((request.POST.get("body") or "").strip())

        if not topic_id and not topic_name:
            messages.error(request, "Pick an existing topic or create a new one.")
            return redirect("community")

        topic = None
        if topic_id:
            topic = Topics.objects.filter(id=topic_id).first()
            if not topic:
                messages.error(request, "Topic not found.")
                return redirect("community")
        elif topic_name:
            topic, _ = Topics.objects.get_or_create(name=topic_name)

        if not title or not body:
            messages.error(request, "Title and body are required to post.")
            return redirect("community")

        Forum.objects.create(
            topic=topic,
            author=request.user,
            title=title,
            body=body,
        )

        messages.success(request, "Your discussion has been posted.")
        return redirect("community")

#--- Forum Vote View ----#
def forum_vote(request, pk):
    if not request.user.is_authenticated:
        return redirect("login")
    forum = get_object_or_404(Forum, pk=pk)

    # Group threads require membership to vote
    if forum.group_id:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not forum.group.members.filter(pk=profile.pk).exists():
            messages.error(request, "Join the group to vote on this thread.")
            return redirect("group_detail", pk=forum.group_id)

    value = request.POST.get("vote")
    if value == "up":
        vote_val = ForumVote.UP
    elif value == "down":
        vote_val = ForumVote.DOWN
    else:
        messages.error(request, "Invalid vote.")
        return redirect(request.META.get("HTTP_REFERER", "community"))

    existing, created = ForumVote.objects.get_or_create(forum=forum, user=request.user, defaults={"value": vote_val})
    if not created:
        if existing.value == vote_val:
            existing.delete()
        else:
            existing.value = vote_val
            existing.save(update_fields=["value"])

    up_count = ForumVote.objects.filter(forum=forum, value=ForumVote.UP).count()
    down_count = ForumVote.objects.filter(forum=forum, value=ForumVote.DOWN).count()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "up": up_count, "down": down_count})

    return redirect(request.META.get("HTTP_REFERER", "community"))


#--- Group Join View ----#
class GroupJoinView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        group = get_object_or_404(CommunityGroup, pk=pk)
        group.members.add(profile)
        return redirect(request.META.get("HTTP_REFERER", "community"))

#--- Group Leave View ----#
class GroupLeaveView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        group = get_object_or_404(CommunityGroup, pk=pk)
        group.members.remove(profile)
        return redirect(request.META.get("HTTP_REFERER", "community"))

#--- Group Create View ----#
class GroupCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = CommunityGroupForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please fix errors before creating a group.")
            return redirect(request.META.get("HTTP_REFERER", "community"))

        group, created = CommunityGroup.objects.get_or_create(
            name=form.cleaned_data["name"],
            defaults={
                "tagline": form.cleaned_data.get("tagline") or "",
                "description": form.cleaned_data.get("description") or "",
                "category": form.cleaned_data.get("category") or "General",
            },
        )
        group.members.add(profile)
        if created:
            messages.success(request, f"Group '{group.name}' created and joined.")
        else:
            messages.info(request, f"You joined '{group.name}'.")
        return redirect(request.META.get("HTTP_REFERER", "community"))


def build_group_context_payload(group, user):
    # Shared helper to load group detail/chat/thread data.
    profile, _ = Profile.objects.get_or_create(user=user)
    is_member = group.members.filter(pk=profile.pk).exists()

    room_name = f"group-{group.pk}"
    chat_messages = (
        ChatMessage.objects.filter(room=room_name)
        .select_related("sender")
        .order_by("created_at")[:200]
    )

    threads = (
        Forum.objects.filter(group=group)
        .select_related("author", "topic")
        .annotate(comment_count=Count("post"))
        .order_by("-created_at")
    )

    members = group.members.select_related("user").all()
    payload = {
        "group": group,
        "group_is_member": is_member,
        "group_is_owner": False,
        "group_members": members,
        "member_count": members.count(),
        "group_threads": threads,
        "group_activity": [],
        "chat_messages": chat_messages,
        "group_messages": chat_messages, 
        "group_chat_room": room_name,
    }
    # Convenience attribute on the object for templates
    group.chat_room_name = room_name
    group.is_member = is_member
    return payload

#--- Group Detail View ----#
class GroupDetailView(LoginRequiredMixin, DetailView):
    model = CommunityGroup
    template_name = "group_detail.html"
    context_object_name = "group"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        context.update(build_group_context_payload(group, self.request.user))
        return context

#--- Groups List View ----#
class GroupsView(LoginRequiredMixin, TemplateView):
    template_name = "groups.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        all_groups = list(CommunityGroup.objects.all().prefetch_related("members").order_by("name"))
        my_groups = list(profile.community_groups.all().prefetch_related("members").order_by("name"))
        # Flag membership and gather a few suggestions
        for g in all_groups:
            g.is_member = g.members.filter(pk=profile.pk).exists()
        suggested = [g for g in all_groups if not g.is_member][:6]

        context["all_groups"] = all_groups
        context["my_groups"] = my_groups
        context["suggested_groups"] = suggested
        context["group_form"] = CommunityGroupForm()
        return context

#--- Group Thread Create View ----#
class GroupThreadCreateView(LoginRequiredMixin, View):
    #--- Handle Group Thread Creation Post ----#
    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(CommunityGroup, pk=group_id)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not group.members.filter(pk=profile.pk).exists():
            messages.error(request, "Join this group to start a thread.")
            return redirect("group_detail", pk=group.id)

        title = sanitize_text((request.POST.get("title") or "").strip())
        body = sanitize_text((request.POST.get("body") or "").strip())
        if not title or not body:
            messages.error(request, "Title and body are required.")
            return redirect("group_detail", pk=group.id)

        topic, _ = Topics.objects.get_or_create(name="General")
        forum = Forum.objects.create(
            topic=topic,
            group=group,
            author=request.user,
            title=title,
            body=body,
        )
        messages.success(request, "Group discussion created.")
        return redirect("group_thread_detail", group_id=group.id, pk=forum.id)

#--- Group Thread Detail View ----#
class GroupThreadDetailView(LoginRequiredMixin, DetailView):
    model = Forum
    template_name = "forum/forum_detail.html"
    context_object_name = "forum"

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(CommunityGroup, pk=kwargs.get("group_id"))
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not self.group.members.filter(pk=profile.pk).exists():
            messages.error(request, "Join this group to view this thread.")
            return redirect("group_detail", pk=self.group.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Forum.objects.filter(group=self.group)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum = self.object
        context["group"] = self.group
        context["posts"] = forum.post_set.select_related("author").order_by("created_at")
        context["form"] = PostForm()
        context["locked"] = forum.locked_forum
        context["up_count"] = ForumVote.objects.filter(forum=forum, value=ForumVote.UP).count()
        context["down_count"] = ForumVote.objects.filter(forum=forum, value=ForumVote.DOWN).count()
        context["user_vote"] = ForumVote.objects.filter(forum=forum, user=self.request.user).values_list("value", flat=True).first()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.locked_forum:
            messages.error(request, "This thread is locked.")
            return redirect("group_thread_detail", group_id=self.group.pk, pk=self.object.pk)

        body = sanitize_text((request.POST.get("body") or "").strip())
        if not body:
            messages.error(request, "Reply cannot be empty.")
            return redirect("group_thread_detail", group_id=self.group.pk, pk=self.object.pk)

        Post.objects.create(
            forum=self.object,
            author=request.user,
            body=body,
        )

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            comment_count = Post.objects.filter(forum=self.object).count()
            return JsonResponse({"ok": True, "comment_count": comment_count})

        messages.success(request, "Reply posted.")
        return redirect("group_thread_detail", group_id=self.group.pk, pk=self.object.pk)


class GroupThreadReplyView(LoginRequiredMixin, View):

    def post(self, request, group_id, thread_id, *args, **kwargs):
        group = get_object_or_404(CommunityGroup, pk=group_id)
        forum = get_object_or_404(Forum, pk=thread_id, group=group)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not group.members.filter(pk=profile.pk).exists():
            messages.error(request, "Join this group to reply.")
            return redirect("group_detail", pk=group.id)

        if forum.locked_forum:
            messages.error(request, "This thread is locked.")
            return redirect("group_thread_detail", group_id=group.id, pk=forum.id)

        body = sanitize_text((request.POST.get("body") or "").strip())
        if not body:
            messages.error(request, "Reply cannot be empty.")
            return redirect("group_detail", pk=group.id)

        Post.objects.create(forum=forum, author=request.user, body=body)
        comment_count = Post.objects.filter(forum=forum).count()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "comment_count": comment_count})

        messages.success(request, "Reply posted.")
        return redirect("group_detail", pk=group.id)





class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'userprofile.html'

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)

        tasks_qs = Task.objects.filter(account_user=user)
        skills_qs = Skill.objects.filter(account_user=user)
        habits_qs = Habit.objects.filter(account_user=user)

        task_points = tasks_qs.filter(status=Task.COMPLETED).aggregate(total=Sum("points"))["total"] or 0
        skill_xp = skills_qs.aggregate(total=Sum("xp"))["total"] or 0
        total_xp = task_points + skill_xp

        streak_info = streak_analytics(user)

        skills_data = []
        for skill in skills_qs.order_by('-created_at')[:5]:
            data = skill.skill_progress_data()
            skills_data.append({
                "name": skill.name,
                "level": skill.level,
                "progress": data["skill_progress_tracked"],
            })

        habits_data = []
        for habit in habits_qs.order_by('-created_at')[:5]:
            gd = goal_date_tracker(habit)
            habits_data.append({
                "name": habit.name,
                "progress": gd["goal_percentage"],
            })

        badges = User_Badge.objects.filter(account_user=user).select_related("badge").order_by('-awarded_at')[:6]
        friends = profile.buddies_list().select_related("user")
        token_balance = Reward.objects.filter(account_user=user).aggregate(total=Sum("tokens"))["total"] or 0
        my_groups = profile.community_groups.all().prefetch_related("members").order_by("name")

        latest_journal = Journal.objects.filter(account_user=user).order_by('-date').first()
        mood_recent = Mood.objects.filter(user=user).order_by('-timestamp')[:5]

        activity = []
        for task in tasks_qs.filter(status=Task.COMPLETED).order_by('-date')[:3]:
            activity.append({
                "title": f"Completed {task.title}",
                "meta": task.date.strftime("%b %d, %Y"),
                "type": "Task",
            })
        for j in Journal.objects.filter(account_user=user).order_by('-date')[:2]:
            activity.append({
                "title": f"Journal entry: {j.entry_type.title()}",
                "meta": j.date.strftime("%b %d, %Y"),
                "type": "Journal",
            })
        for b in badges[:2]:
            activity.append({
                "title": f"Badge unlocked: {b.badge.title}",
                "meta": b.awarded_at.strftime("%b %d, %Y"),
                "type": "Badge",
            })

        context.update({
            "profile": profile,
            "skills_data": skills_data,
            "habits_data": habits_data,
            "badges": badges,
            "friends": friends,
            "token_balance": token_balance,
            "total_xp": total_xp,
            "login_streak": streak_info.get("login_streak", 0),
            "skills_count": skills_qs.count(),
            "latest_journal": latest_journal,
            "mood_recent": mood_recent,
            "recent_activity": activity,
            "incoming": BuddyRequest.objects.filter(receiver=profile, status=BuddyRequest.PENDING),
            "outgoing": BuddyRequest.objects.filter(sender=profile, status=BuddyRequest.PENDING),
            "buddy_form": BuddyRequestForm(),
            "respond_form": BuddyRespondForm(),
            "my_groups": my_groups,
        })
        return context


class VisitorProfileView(LoginRequiredMixin, TemplateView):
    template_name = "visitorprofile.html"

    def get_context_data(self, **kwargs):
        
       
        context = super().get_context_data(**kwargs)
        target_user = get_object_or_404(User, pk=kwargs.get("user_id"))
        profile, _ = Profile.objects.get_or_create(user=target_user)

        skills_qs = Skill.objects.filter(account_user=target_user)
        habits_qs = Habit.objects.filter(account_user=target_user)
        goals_qs = Goals.objects.filter(account_user=target_user)
        badges = User_Badge.objects.filter(account_user=target_user).select_related("badge").order_by("-awarded_at")[:6]
        friends = profile.buddies_list().select_related("user")

        skills_data = []
        for skill in skills_qs.order_by("-created_at")[:5]:
            data = skill.skill_progress_data()
            skills_data.append({
                "name": skill.name,
                "level": skill.level,
                "progress": data["skill_progress_tracked"],
            })

        habits_data = []
        for habit in habits_qs.order_by("-created_at")[:5]:
            gd = goal_date_tracker(habit)
            habits_data.append({
                "name": habit.name,
                "progress": gd["goal_percentage"],
            })

        streak_info = streak_analytics(target_user)
        tasks_qs = Task.objects.filter(account_user=target_user)
        total_xp = (tasks_qs.filter(status=Task.COMPLETED).aggregate(total=Sum("points"))["total"] or 0) + (skills_qs.aggregate(total=Sum("xp"))["total"] or 0)
        # Recent public-ish activity stream
        activity_items = []
        for s in skills_qs.order_by("-created_at")[:5]:
            activity_items.append({
                "title": f"New skill: {s.name}",
                "meta": s.created_at.strftime("%b %d, %Y"),
                "type": "Skill",
                "body": f"Level {s.level} Â· {s.xp} XP"
            })
        for h in habits_qs.order_by("-created_at")[:5]:
            gd = goal_date_tracker(h)
            activity_items.append({
                "title": f"Habit started: {h.name}",
                "meta": h.created_at.strftime("%b %d, %Y"),
                "type": "Habit",
                "body": f"Goal {gd.get('goal_percentage', 0) or 0}%"
            })
        for g in goals_qs.order_by("-due_date")[:5]:
            activity_items.append({
                "title": f"Goal: {g.title}",
                "meta": g.due_date.strftime("%b %d, %Y") if g.due_date else "Goal set",
                "type": "Goal",
                "body": g.status
            })
        for b in badges:
            activity_items.append({
                "title": f"Badge earned: {b.badge.title}",
                "meta": b.awarded_at.strftime("%b %d, %Y") if hasattr(b, "awarded_at") and b.awarded_at else "",
                "type": "Badge",
                "body": getattr(b.badge, "description", "") or ""
            })
        activity_items = sorted(activity_items, key=lambda x: x.get("meta", ""), reverse=True)[:12]

        context.update({
            "profile": profile,
            "profile_user": target_user,
            "target_user": target_user,
            "skills": skills_qs.order_by("-created_at")[:5],
            "habits": habits_qs.order_by("-created_at")[:5],
            "goals": goals_qs.order_by("due_date")[:5],
            "badges": badges,
            "groups": profile.community_groups.all(),
            "buddy_form": BuddyRequestForm(),
            "skills_data": skills_data,
            "habits_data": habits_data,
            "login_streak": streak_info.get("login_streak", 0),
            "skills_count": skills_qs.count(),
            "friends": friends,
            "total_xp": total_xp,
            "recent_activity": activity_items,
        })
        return context

class UserSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'usersettings.html'
    #--- User Settings View ----#
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        context.setdefault("user_form", kwargs.get("user_form") or UserForm(instance=self.request.user))
        context.setdefault("profile_form", kwargs.get("profile_form") or ProfileForm(instance=profile))
        return context
    #--- Handle Profile Update Post ----#   
    def post(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("user_settings")
        messages.error(request, "Please fix the errors below.")
        return self.render_to_response(self.get_context_data(user_form=user_form, profile_form=profile_form))


#Generated by ChatGPT
def dm_room_name(user_a_id: int, user_b_id: int) -> str:
    """
    Deterministic room name for a DM between two users.
    Ensures both users join the same room regardless of order.
    """
    a, b = sorted([int(user_a_id), int(user_b_id)])
    return f"dm-{a}-{b}"

#Generated by ChatGPT
def users_blocked(user_a_id: int, user_b_id: int) -> bool:
    """
    Returns True if either user has blocked the other.
    """
    return UserBlock.objects.filter(
        Q(blocker_id=user_a_id, blocked_id=user_b_id)
        | Q(blocker_id=user_b_id, blocked_id=user_a_id)
    ).exists()

class MessageView(LoginRequiredMixin, TemplateView):
    template_name = "messages.html"

    def get_context_data(self, **kwargs):
       
        User = get_user_model()

        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ---- 1) Who are we chatting with? ----
        other_id = self.request.GET.get("with")
        other_user = None

        # a) Try ?with=<user_id>
        if other_id:
            try:
                other_user = User.objects.get(pk=int(other_id))
            except (User.DoesNotExist, ValueError):
                other_user = None

        # b) Fallback - first buddy if none selected
        profile = Profile.objects.filter(user=user).first()
        buddies = profile.buddies_list() if profile else []
        safe_buddies = [b for b in buddies if not users_blocked(user.id, b.user_id)]

        if other_user is None and safe_buddies:
            other_user = safe_buddies[0].user

        # c) Final fallback - any other profile
        if other_user is None:
            other_profile = Profile.objects.exclude(user=user).first()
            if other_profile:
                other_user = other_profile.user

        # ---- 2) Compute room name & load messages ----
        if other_user and not users_blocked(user.id, other_user.id):
            room_name = dm_room_name(user.id, other_user.id)
            messages_qs = (
                ChatMessage.objects
                .filter(room=room_name)
                .select_related("sender")
                .order_by("created_at")
            )
        else:
            room_name = "dm-demo"
            messages_qs = ChatMessage.objects.none()
            other_user = None

     
        context["other_user"] = other_user
        context["room_name"] = room_name
        context["chat_messages"] = messages_qs
        context["buddies"] = safe_buddies

        # Mark messages as seen now so we can show an unread dot elsewhere
        self.request.session["messages_last_seen_at"] = timezone.now().isoformat()
        self.request.session.modified = True

        return context



#--- Forum Views ----#
class ForumCreateView(LoginRequiredMixin, CreateView):
    model = Forum
    form_class = ForumForm
    template_name = 'forum/forum_create_form.html'
    success_url = reverse_lazy('community')

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.save()
        messages.success(self.request, "Discussion thread created.")
        return redirect("community_thread", pk=obj.pk)

class ForumDetailView(LoginRequiredMixin, DetailView):
    model= Forum
    template_name = "forum/forum_detail.html"
    context_object_name = "forum"

    def get_queryset(self):
        return Forum.objects.filter(group__isnull=True)

    #--- Handle displaying posts and adding new posts ---#
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum = self.object
        context["posts"] = forum.post_set.select_related("author").order_by("created_at")
        context["form"] = PostForm()
        context["locked"] = forum.locked_forum
        context["up_count"] = ForumVote.objects.filter(forum=forum, value=ForumVote.UP).count()
        context["down_count"] = ForumVote.objects.filter(forum=forum, value=ForumVote.DOWN).count()
        context["user_vote"] = ForumVote.objects.filter(forum=forum, user=self.request.user).values_list("value", flat=True).first()
        return context
    #edited by ChatGPT
    #--- Handle new post submission ---#
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        body = sanitize_text((request.POST.get("body") or "").strip())

        if self.object.locked_forum:
            messages.error(request, "This thread is locked.")
            return redirect("community_thread", pk=self.object.pk)

        if not body:
            messages.error(request, "Reply cannot be empty.")
            return redirect("community_thread", pk=self.object.pk)

        Post.objects.create(
            forum=self.object,
            author=request.user,
            body=body,
        )

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            comment_count = Post.objects.filter(forum=self.object).count()
            return JsonResponse({"ok": True, "comment_count": comment_count})

        messages.success(request, "Reply posted.")
        return redirect("community_thread", pk=self.object.pk)


class ForumDeleteView(LoginRequiredMixin, DeleteView):
    model = Forum
    success_url = reverse_lazy("community")
    # Only allow authors to delete their own threads
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user:
            messages.error(request, "You can only delete your own discussion.")
            return redirect("community_thread", pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)


class BuddiesView(LoginRequiredMixin, TemplateView):
    template_name = "buddies.html"
    login_url = "login"  # adjust to your login route name
    #--- Display buddy list and requests ---#
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        context["buddies"] = profile.buddies_list()
        context["incoming"] = BuddyRequest.objects.filter(receiver=profile, status=BuddyRequest.PENDING)
        context["outgoing"] = BuddyRequest.objects.filter(sender=profile, status=BuddyRequest.PENDING)
        context["form"] = BuddyRequestForm()
        context["respond_form"] = BuddyRespondForm()
        context["blocked_users"] = set(
            UserBlock.objects.filter(blocker=self.request.user).values_list("blocked_id", flat=True)
        )
        return context
#edited by ChatGPT
class BuddySendView(LoginRequiredMixin, View):
    login_url = "login"
    #--- Send a buddy request ---#
    def post(self, request, *args, **kwargs):
        form = BuddyRequestForm(request.POST)
        if form.is_valid():
            receiver = form.cleaned_data["receiver"]
            sender_profile, _ = Profile.objects.get_or_create(user=request.user)
            if users_blocked(request.user.id, receiver.user_id):
                messages.error(request, "You cannot send a buddy request to this user.")
                return redirect("buddies")
            if receiver == sender_profile:
                messages.error(request, "You cannot buddy yourself.")
            else:
                obj, created = BuddyRequest.objects.get_or_create(
                    sender=sender_profile,
                    receiver=receiver,
                    defaults={"status": BuddyRequest.PENDING},
                )
                if created:
                    messages.success(request, f"Buddy request sent to {receiver.user.username}.")
                else:
                    messages.info(request, "Buddy request already exists.")
        return redirect("buddies")
#edited by ChatGPT
class BuddyRespondView(LoginRequiredMixin, View):
    login_url = "login"
    #--- Respond to a buddy request ---#
    def post(self, request, *args, **kwargs):
        form = BuddyRespondForm(request.POST)
        if not form.is_valid():
            return redirect("buddies")

        buddy_req = get_object_or_404(BuddyRequest, pk=form.cleaned_data["request_id"])
        action = form.cleaned_data["action"]
        profile, _ = Profile.objects.get_or_create(user=request.user)

        if users_blocked(request.user.id, buddy_req.sender.user_id) or users_blocked(request.user.id, buddy_req.receiver.user_id):
            messages.error(request, "Action blocked by user preferences.")
            return redirect("buddies")

        if action == BuddyRespondForm.ACTION_ACCEPT and buddy_req.receiver == profile:
            buddy_req.accept()
            messages.success(request, f"You are now buddies with {buddy_req.sender.user.username}.")
        elif action == BuddyRespondForm.ACTION_DECLINE and buddy_req.receiver == profile:
            buddy_req.decline()
            messages.info(request, "Buddy request declined.")
        elif action == BuddyRespondForm.ACTION_CANCEL and buddy_req.sender == profile:
            buddy_req.cancel()
            messages.info(request, "Buddy request canceled.")
        else:
            messages.error(request, "Not authorized for that action.")
        return redirect("buddies")

class BuddyRemoveView(LoginRequiredMixin, View):
    login_url = "login"
    #--- Remove a buddy ---#
    def post(self, request, user_id, *args, **kwargs):
        buddy_profile = get_object_or_404(Profile, pk=user_id)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        Friendship.objects.filter(requester=profile, buddy=buddy_profile).delete()
        Friendship.objects.filter(requester=buddy_profile, buddy=profile).delete()
        messages.info(request, f"Removed {buddy_profile.user.username} from buddies.")
        return redirect("buddies")


class BlockUserView(LoginRequiredMixin, View):
    #--- Block a user ---#
    def post(self, request, user_id, *args, **kwargs):
        target = get_object_or_404(User, pk=user_id)
        if target == request.user:
            messages.error(request, "You cannot block yourself.")
            return redirect(request.META.get("HTTP_REFERER", "buddies"))

        UserBlock.objects.get_or_create(blocker=request.user, blocked=target)

        # remove buddy relationship if exists
        profile, _ = Profile.objects.get_or_create(user=request.user)
        target_profile = Profile.objects.filter(user=target).first()
        if target_profile:
            Friendship.objects.filter(requester=profile, buddy=target_profile).delete()
            Friendship.objects.filter(requester=target_profile, buddy=profile).delete()

        messages.info(request, f"Blocked {target.username}.")
        return redirect(request.META.get("HTTP_REFERER", "buddies"))

#--- Unblock User View ----#
class UnblockUserView(LoginRequiredMixin, View):
    def post(self, request, user_id, *args, **kwargs):
        UserBlock.objects.filter(blocker=request.user, blocked_id=user_id).delete()
        messages.success(request, "User unblocked.")
        return redirect(request.META.get("HTTP_REFERER", "buddies"))

