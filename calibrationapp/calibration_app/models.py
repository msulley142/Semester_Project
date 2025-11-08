from django.db import models
from django.utils import timezone 
from datetime import date
from django.conf import settings
from django.contrib.auth.models import User





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
    


    

#-----Task Model-----#
class Task(models.Model):
    NOTSTARTED, INPROGRESS, COMPLETED = ('NOTSTARTED', 'INPROGRESS', 'COMPLETED')
    status_OP = [(NOTSTARTED, 'Not Started'), (INPROGRESS, 'In Progress'), (COMPLETED, 'Completed')]
   
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
    
