from django.db import models
from django.utils import timezone 
from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator






#----skill----#

class Skill(models.Model):
    account_user = models.ForeignKey(User, on_delete=models.CASCADE , null=True, blank=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    level = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    xp = models.PositiveIntegerField(default=0)


    
    def __str__(self):
        return self.name
    
   #levels users up after conditions are met. 
   #I asked for chatGPT's assitance due to logic errors causing the progress bar not to move.  
    def add_xp(self, x: int ):

       self.xp += x
       
       while self.xp >= self.level * 100:
           self.xp -= self.level * 100
           self.level += 1

       self.save(update_fields=["xp", "level"])
    #used to calculate percenatge for progress bar and left over xp for users. 
    def skill_progress_data(self):
        to_level_up = self.level * 100
        d = to_level_up or 1 #suggested by chatgpt to prevent errors from diving by zero 
        skill_progress_tracked = int(round((self.xp /d) * 100)) 
        left_over = max(0, (to_level_up - skill_progress_tracked)) # Chatgpt fixed mistake and told me to use round and  max(0, n) so that numbers stay postives and are handled well in the database. prompt:my progress bars are off. 
        
        return { "to_level_up": to_level_up , "skill_progress_tracked": skill_progress_tracked, "left_over": left_over }
    
    

    
#-------Habit Model-------#
class Habit(models.Model):
    Build = 'Build'
    Break = 'Break'
    HABIT_TYPE_CHOICES = [
        (Build, 'Build'),
        (Break, 'Break'),
    ]
    

    account_user = models.ForeignKey(User, on_delete=models.CASCADE , null=True, blank=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    habit_type = models.CharField(max_length=5, choices=HABIT_TYPE_CHOICES, default=Build)
    #frequency = models.CharField(max_length=50)  # e.g., daily, weekly
    goal_start = models.DateField(default=date.today)
    goal_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.name} [{self.habit_type}]"
    
    

    

#NOT IN USE YET# Suggested by chatgpt. Prompt: I asked for ways to make the app more ineresting. 
#-------Quest Model-------#
class Quest(models.Model):
    account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    conditions = models.JSONField(default=dict)
    completed = models.BooleanField(default=False)
    reward_tokens = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} - {'Completed' if self.completed else 'In Progress'}" 
    

  
class Goals(models.Model):
  Short_Term,Long_Term ,LifeStyle = ('Short Term' ,'Long Term', 'Lifestyle')
  goal_OP = [(Short_Term, 'Short Term'),  (Long_Term, 'Long Term'), (LifeStyle, 'Lifestyle')]

  account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
  title = models.CharField(max_length=150)
  description = models.TextField(blank=True, null=True)
  goal_type = models.CharField(max_length=20, choices=goal_OP, default='Short Term')
  skill = models.ForeignKey(Skill, null=True, blank=True, on_delete=models.SET_NULL)
  habit = models.ForeignKey(Habit, null=True, blank=True, on_delete=models.SET_NULL)
  metric = models.CharField(max_length=100, blank=True, null=True) 
  target_value = models.FloatField(blank=True, null=True)  
  current_value = models.FloatField(default=0, blank=True, null=True)
  start_date = models.DateField(default=date.today)
  due_date = models.DateField(blank=True, null=True)
  STATUS = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
    ]
  status = models.CharField(max_length=20, choices=STATUS, default="not_started")

  priority = models.IntegerField(default=1)  # 1 = low, 5 = critical

  reason = models.TextField(blank=True, null=True)  # personal motivation
  reflection = models.TextField(blank=True, null=True)  # end of goal review


  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.title





#-------Rewards Model-------#
class Reward(models.Model):
    account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tokens = models.PositiveIntegerField(default=0)
     #This function was edited by AI
    def add_token(self, n: int):
        self.tokens = models.F("tokens")+ max(0, n)
        self.save(update_fields=["tokens"])
     
        self.refresh_from_db() # This and the use of .f was suggested by chatgpt to stop race conditons



class Badge(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.title} - {self.code}"
    


class User_Badge(models.Model):
    account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('account_user', 'badge')

    def __str__(self):
        return f"{self.account_user.username} - {self.badge.title}"





class Mood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # core mood rating
    mood_score = models.IntegerField()  # e.g., 1–10 or -5 to +5

    # optional mood category
    MOOD_TYPES = [
        ("happy", "Happy"),
        ("sad", "Sad"),
        ("angry", "Angry"),
        ("anxious", "Anxious"),
        ("tired", "Tired"),
        ("motivated", "Motivated"),
        ("neutral", "Neutral"),
    ]
    mood_type = models.CharField(max_length=30, choices=MOOD_TYPES, blank=True, null=True)

    note = models.TextField(blank=True, null=True)  # journal-like free text

  
    energy_level = models.IntegerField(blank=True, null=True)  # 1–10
    sleep_hours = models.FloatField(blank=True, null=True)
    stress_level = models.IntegerField(blank=True, null=True)  # 1–10
    social_interaction = models.IntegerField(blank=True, null=True)  # e.g., 1–5 scale

    related_goal = models.ForeignKey(Goals, on_delete=models.SET_NULL, null=True, blank=True)

    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.mood_score} ({self.timestamp.date()})"
    





class Journal(models.Model):
    PRACTICE, REFLECTION, URGE, LAPSE, SUCCESS = ("PRACTICE","REFLECTION","URGE","LAPSE","SUCCESS")
    ENTRY_TYPES = [(PRACTICE,"Practice"),(REFLECTION,"Reflection"),(URGE,"Urge"),(LAPSE,"Lapse"),(SUCCESS,"Success")]
  #  OP_Skill, OP_Habit = ("SKILL","HABIT")
   # Journal_TYPES = [(OP_Skill,"Skill"),(OP_Habit,"Habit")]
    
    account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    skill = models.ForeignKey(Skill, null=True, blank=True, on_delete=models.SET_NULL)
    habit = models.ForeignKey(Habit, null=True, blank=True, on_delete=models.SET_NULL)
    entry_type = models.CharField(max_length=12, choices=ENTRY_TYPES)
    trigger = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)

    
    class Meta:
        unique_together = ('habit', 'date') # suggested by github's copilot assitant to avoid duplicate entries.
        
    
       

    def __str__(self):
        return f"{self.note} - {self.date} "


    

#-----Task Model-----#
class Task(models.Model):
    NOTSTARTED, INPROGRESS, COMPLETED = ('NOTSTARTED', 'INPROGRESS', 'COMPLETED')
    status_OP = [(NOTSTARTED, 'Not Started'), (INPROGRESS, 'In Progress'), (COMPLETED, 'Completed')]
   
    account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    points =  models.PositiveIntegerField(default=10)
    skill = models.ForeignKey(Skill, null=True, blank=True, on_delete=models.SET_NULL)
    habit = models.ForeignKey(Habit, null=True, blank=True, on_delete=models.SET_NULL)
    goals = models.ForeignKey(Goals, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=15, choices=status_OP)
    description = models.TextField(blank=True)
    date =  models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title}"
    







#------User_Profile------#

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pic/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif"])],
    )
    buddies = models.ManyToManyField(
        "self",
        through="Friendship",
        through_fields=("requester", "buddy"),
        symmetrical=False,
        related_name="friends_of",
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username}"

    def buddies_list(self):
        return Profile.objects.filter(
            models.Q(friendships_sent__buddy=self) | models.Q(friendships_received__requester=self)
        ).distinct()

    def clean(self):
        super().clean()
        if self.profile_picture:
            max_bytes = 2 * 1024 * 1024  # 2 MB limit for uploads
            size = getattr(self.profile_picture, "size", 0) or 0
            if size > max_bytes:
                raise ValidationError({"profile_picture": "Profile picture must be 2MB or smaller."})


class Topics(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CommunityGroup(models.Model):
    CATEGORY_CHOICES = [
        ("General", "General"),
        ("Habit", "Habit"),
        ("Skill", "Skill"),
        ("Goal", "Goal"),
    ]

    name = models.CharField(max_length=120, unique=True)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(Profile, related_name="community_groups", blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="General")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()


class Forum(models.Model):
    topic = models.ForeignKey(Topics, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    locked_forum = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ForumVote(models.Model):
    UP = 1
    DOWN = -1
    VALUE_CHOICES = ((UP, "Upvote"), (DOWN, "Downvote"))

    forum = models.ForeignKey(Forum, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="forum_votes", on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("forum", "user")

    def __str__(self):
        return f"{self.user} -> {self.forum} ({self.value})"


class Post(models.Model):
    forum = models.ForeignKey(Forum, blank=True, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    body = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.author} on {self.forum}"


class BuddyRequest(models.Model):
    PENDING, ACCEPTED, DECLINED, CANCELED = ("pending", "accepted", "declined", "canceled")
    buddy_status = [(PENDING, "pending"), (ACCEPTED, "accepted"), (DECLINED, "declined"), (CANCELED, "canceled")]

    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="buddy_requests_sent")
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="buddy_requests_received")
    status = models.CharField(max_length=10, choices=buddy_status, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("sender", "receiver")

    def __str__(self):
        return f"{self.sender.user.username} -> {self.receiver.user.username} ({self.status})"

    def accept(self):
        self.status = self.ACCEPTED
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "updated_at"])
        Friendship.objects.get_or_create(requester=self.sender, buddy=self.receiver)
        Friendship.objects.get_or_create(requester=self.receiver, buddy=self.sender)

    def decline(self):
        self.status = self.DECLINED
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "updated_at"])

    def cancel(self):
        self.status = self.CANCELED
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "updated_at"])


class Friendship(models.Model):
    requester = models.ForeignKey(Profile, related_name="friendships_sent", on_delete=models.CASCADE)
    buddy = models.ForeignKey(Profile, related_name="friendships_received", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("requester", "buddy")

    def clean(self):
        if self.requester_id == self.buddy_id:
            raise ValidationError("Cannot friend yourself")

    def __str__(self):
        return f"{self.requester.user.username} -> {self.buddy.user.username}"



class ChatMessage(models.Model):
    room = models.CharField(max_length=100, db_index=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.body[:30]}"
