from django.db import models
from django.utils import timezone 
from datetime import date
from django.conf import settings
from django.contrib.auth.models import User


#The following functions were edited  by and completed using GitHub Copilot assistant on October 29th, 2025


# Create your models here.

class Skill(models.Model):
    account_user = models.ForeignKey(User, on_delete=models.CASCADE , null=True, blank=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    level = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    xp = models.PositiveIntegerField(default=0)


    
    def __str__(self):
        return self.name
    
    def add_xp(self, x: int ):
       # x = max(0, int(amount))
       self.xp += x
       
       while self.xp >= self.level * 100:
           self.xp -= self.level * 100
           self.level += 1

       self.save(update_fields=["xp", "level"])
       
    def skill_progress_data(self):
        to_level_up = self.level * 100
        d = to_level_up or 1
        skill_progress_tracked = int(round((self.xp /d) * 100))
        left_over = max(0, (to_level_up - skill_progress_tracked))
        
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
        unique_together = ('habit', 'date')
        unique_together = ('skill', 'date')

    def __str__(self):
        return f"{self.note} - {self.date} "


#-------Rewards Model-------#
class Reward(models.Model):
    account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tokens = models.PositiveIntegerField(default=0)

    def add_token(self, n: int):
        self.tokens = models.F("tokens")+ max(0, n)
        self.save(update_feilds=["tokens"])
        #---check on this---#
        self.refresh_from_db()

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
    

    
    

#-----Task Model-----#
class Task(models.Model):
    NOTSTARTED, INPROGRSS, COMPLETED = ('NOTSTARTED', 'INPROGRESS', 'COMPLETED')
    status_OP = [(NOTSTARTED, 'Not Started'), (INPROGRSS, 'In Progress'), (COMPLETED, 'Completed')]
   
    account_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    points =  models.PositiveIntegerField(default=10)
    skill = models.ForeignKey(Skill, null=True, blank=True, on_delete=models.SET_NULL)
    habit = models.ForeignKey(Habit, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=15, choices=status_OP)
    description = models.TextField(blank=True)
    date =  models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title}"
    


#------User_Profile------#
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pic/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}"
    
