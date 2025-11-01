from django.db import models
from django.utils import timezone 



# Create your models here.

class Skill(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    xp = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def add_xp(self, amount):
        self.xp += amount

        while self.xp >= 100:
            self.xp -= self.level * 100
            self.level += 1
           
        self.save()


# Not sure if this will be used yet.
class Skill_Log(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    xp_gained = models.IntegerField()

    def __str__(self):
        return f"{self.skill.name} - {self.date} - {self.xp_gained} XP"

#-------Habit Model-------#
class Habit(models.Model):
    Build = 'Build'
    Break = 'Break'
    HABIT_TYPE_CHOICES = [
        (Build, 'Build'),
        (Break, 'Break'),
    ]


    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    frequency = models.CharField(max_length=50)  # e.g., daily, weekly
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    

class Habit_Log(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.habit.name} - {self.date} - {'Completed' if self.completed else 'Not Completed'}"

#-------Rewards Model-------#
class Reward(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    tokens = models.PositiveIntegerField()

class Badge(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title

#-------Quest Model-------#
class Quest(models.Model):
    user  = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    conditions = models.JSONField(default=dict)
    completed = models.BooleanField(default=False)


    title = models.CharField(max_length=200)
