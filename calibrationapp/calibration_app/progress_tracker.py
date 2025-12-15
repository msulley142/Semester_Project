from django.utils import timezone 
from datetime import timedelta
from datetime import date
from .models import Reward, Badge, User_Badge, Journal, Task, Habit, Goals, Skill


# Canonical list of badges to seed in the DB.
BADGE_DEFINITIONS = [
    # Skill level milestones
    {"code": "FIRST_LEVEL_UP", "title": "First Level Up", "description": "Reach level 2 in any skill."},
    {"code": "SKILL_LEVEL_5", "title": "Skill Level 5", "description": "Reach level 5 in a skill."},
    {"code": "SKILL_LEVEL_10", "title": "Skill Level 10", "description": "Reach level 10 in a skill."},
    {"code": "MULTI_SKILL_LEVEL_5", "title": "Multiple Skills at Level 5", "description": "Get at least two skills to level 5."},
    {"code": "MULTI_SKILL_LEVEL_10", "title": "Multiple Skills at Level 10", "description": "Get at least two skills to level 10."},

    # Journal milestones
    {"code": "FIRST_JOURNAL", "title": "First Journal", "description": "Log your first journal entry."},
    {"code": "5TH_JOURNAL", "title": "Fifth Journal", "description": "Log your fifth journal entry."},
    {"code": "10th_Journal", "title": "Tenth Journal", "description": "Log your tenth journal entry."},

    # Practice streaks
    {"code": "3_Practice_Streak", "title": "3-day Practice Streak", "description": "Practice a skill 3 days in a row."},
    {"code": "7_Practice_Streak", "title": "7-day Practice Streak", "description": "Practice a skill 7 days in a row."},

    # Task completions
    {"code": "FIRST_TASK", "title": "1st Task Done", "description": "Complete your first task."},
    {"code": "5TH_TASK", "title": "5th Task Done", "description": "Complete five tasks."},
    {"code": "20TH_TASK", "title": "20th Task Done", "description": "Complete twenty tasks."},

    # Skill creation milestones (legacy + current)
    {"code": "FIRST_SKILL", "title": "1st Skill", "description": "Create your first skill."},
    {"code": "FIFTH_SKILL", "title": "5th Skill", "description": "Create your fifth skill."},
    {"code": "20th_SKILL", "title": "20th Skill", "description": "Create your tenth skill (legacy code name)."},

    # Habit creation
    {"code": "First_Habit", "title": "First_Habit", "description": "Create your first habit."},

    # Abstinence streaks are generated per habit; seed placeholders if desired
    {"code": "ABST_SAMPLE_3", "title": "3-day Abstinence", "description": "Placeholder: abstain from a break habit for 3 days (real codes use habit id)."},
    {"code": "ABST_SAMPLE_7", "title": "7-day Abstinence", "description": "Placeholder: abstain from a break habit for 7 days (real codes use habit id)."},
]











#awards badges when certain conditons are met. 
def award_badge(account_user, code, title, description=''):
    badge,_ = Badge.objects.get_or_create(code= code, defaults={"title": title, "description": description},) 
    User_Badge.objects.get_or_create(account_user=account_user, badge=badge)

#----Badges for skill level ups----#
def skill_level_badges(account_user, skill: Skill, previous_level: int):

    new_level = skill.level

    # Single-skill milestones
    if previous_level < 2 and new_level >= 2:
        award_badge(account_user, "FIRST_LEVEL_UP", "First Level Up")
    if previous_level < 5 and new_level >= 5:
        award_badge(account_user, "SKILL_LEVEL_5", "Skill Level 5")
    if previous_level < 10 and new_level >= 10:
        award_badge(account_user, "SKILL_LEVEL_10", "Skill Level 10")

    # Multi-skill milestones (only when this skill newly qualifies)
    other_level5 = Skill.objects.filter(account_user=account_user, level__gte=5).exclude(pk=skill.pk).count()
    if previous_level < 5 and new_level >= 5 and other_level5 >= 1:
        award_badge(account_user, "MULTI_SKILL_LEVEL_5", "Multiple Skills at Level 5")

    other_level10 = Skill.objects.filter(account_user=account_user, level__gte=10).exclude(pk=skill.pk).count()
    if previous_level < 10 and new_level >= 10 and other_level10 >= 1:
        award_badge(account_user, "MULTI_SKILL_LEVEL_10", "Multiple Skills at Level 10")


#----Badges for journal entries----#
def journal_entry_create(journal: Journal):
    account_user = journal.account_user


#----XP increase for skill practicing----#
    if journal.entry_type == Journal.PRACTICE and journal.skill:
        xp = 5
        previous_level = journal.skill.level
        journal.skill.add_xp(xp)
        skill_level_badges(account_user, journal.skill, previous_level)
    elif journal.entry_type == Journal.REFLECTION and journal.skill:
        xp = 1
        previous_level = journal.skill.level
        journal.skill.add_xp(xp)
        skill_level_badges(account_user, journal.skill, previous_level)
    
#----Badges for journal entries----#
    entry_total = Journal.objects.filter(account_user=account_user).count()
    if entry_total == 1:
        award_badge(account_user, "FIRST_JOURNAL", "First Journal", "Logged your first journal entry!!!")
    elif entry_total == 5:
        award_badge(account_user, "5TH_JOURNAL", "Fifth Journal", "Logged your fifth journal entry!!!")
    elif entry_total == 10:
        award_badge(account_user, "10th_Journal", "Tenth Journal", "Logged your Tenth journal entry!!!")

#----Badges for practice streaks----#
    streak_notify(account_user)
    if journal.habit and journal.habit.habit_type == 'Break':
        abst_badge(account_user, journal.habit)


#----Badges for obtaining streaks----#
def streak_notify(account_user):
    tod = timezone.localdate()
    streak = 0
    days_ago = tod
   
   
    while True:
        practice_skill = Journal.objects.filter(
            account_user=account_user,
            date__date=days_ago,
            entry_type=Journal.PRACTICE,
        ).exists()
        if not practice_skill:
            break
        streak += 1
        days_ago -= timedelta(days=1) #chatgpt suggested the use of timedelta. Good to use when needing to calculate past and future time.

    if streak >= 3:
        award_badge(account_user, "3_Practice_Streak", "3-day Practice Streak" )
    if streak >= 7:
         award_badge(account_user, "7_Practice_Streak", "7-day Practice Streak" )

#----Badges for abstinence streaks----#
def abst_badge(account_user, habit):
    tod = timezone.localdate()
    streak = 0
    days_ago = tod
   
   
    while True:
        if days_ago < habit.goal_start:
            break
        laspe_logged = Journal.objects.filter(
            account_user=account_user,
            habit=habit,
            date__date=days_ago,
            entry_type=Journal.LAPSE,
        ).exists()
        if laspe_logged:
            break
        streak += 1
        days_ago -= timedelta(days=1)

    if streak >= 3:
        award_badge(account_user, f"ABST_{habit.id}_Streak_3", f"3-day Abstinence from {habit.name}" )
    if streak >= 7:
         award_badge(account_user, f"ABST_{habit.id}_Streak_7", f"7-day Abstinence from {habit.name}" )

#----Badges for completing taskss----#
def task_completion_badge(task: Task):
    account_user = task.account_user
  

    if task.status != Task.COMPLETED:
        return
    if task.skill:
        previous_level = task.skill.level
        task.skill.add_xp(10)
        skill_level_badges(account_user, task.skill, previous_level)
    
    task_completed = Task.objects.filter(account_user=account_user, status=Task.COMPLETED).count()
    if task_completed == 1:
        award_badge(account_user, 'FIRST_TASK', '1st Task Done')
    elif task_completed == 5:
        award_badge(account_user, '5TH_TASK', '5th Task Done')
    elif task_completed == 20:
        award_badge(account_user, '20TH_TASK', '20th Task Done')

 #Use to track how well user are adhering to thier goals.
 #Chatgpt suggested the use of min and max while fixing my math.
def goal_date_tracker(habit: Habit):
        today = timezone.localdate()

#set duration of the goal
        if habit.goal_end:
            goal_duration = max(1,(habit.goal_end - habit.goal_start).days + 1)
        else:
            goal_duration = 30

#calculates how many days its been since goal started
        if today < habit.goal_start:
            days_since_start = 0
        else:
            days_since_start = min((today - habit.goal_start).days + 1, goal_duration)

        
        if days_since_start >= goal_duration:
            goal_complete = True
        else:
            goal_complete = False


        days_left = max(0,goal_duration - days_since_start)
        goal_percentage = max(0,min(100, int(round((days_since_start / goal_duration) * 100))))


        return {
            "goal_duration": goal_duration,
            "days_since_start": days_since_start,
            "days_left": days_left,
            "goal_percentage": goal_percentage,
            "goal_complete": goal_complete
        }



def skill_badge_award(skill: Skill):
  account_user = skill.account_user
  skill_count = Skill.objects.filter(account_user=account_user).count()
  
  if skill_count == 1:
      award_badge(account_user, 'FIRST_SKILL', '1st Skill')
  elif skill_count == 5:
      award_badge(account_user, 'FIFTH_SKILL', '5th Skill')
  elif skill_count == 10:
      award_badge(account_user, '20th_SKILL', '20th Skill')






def goal_award_updater(goal: Goals):
    xp = 100
    if goal.skill != None:
        if goal.status == 'completed':
           previous_level = goal.skill.level
           goal.skill.add_xp(xp)
           skill_level_badges(goal.account_user, goal.skill, previous_level)

    else:
        pass

    
