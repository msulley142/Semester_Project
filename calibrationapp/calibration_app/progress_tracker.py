from django.utils import timezone 
from datetime import timedelta
from .models import Reward, Badge, User_Badge,Journal, Task, Quest


# Awards badges when certain conditons are met. 
def award_badge(account_user, code, title, description=''):
    badge,_ = Badge.objects.get_or_create(code= code, defaults={"title": title, "description": description},)
    User_Badge.objects.get_or_create(account_user=account_user, badge=badge)


def token_wallet(account_user):
    wallet,_ = Reward.objects.get_or_create(account_user=account_user)
    return wallet

def journal_entry_create(journal: Journal):
    account_user = journal.account_user





#----XP increase for skill practicing----#
    if journal.entry_type == Journal.PRACTICE and journal.skill:
        xp = 5 
        journal.skill.add_xp(xp)
    elif journal.entry_type == Journal.REFLECTION and journal.skill:
        xp = 1
    
  


#----Badges for journal entries----#
    entry_total = Journal.objects.filter(account_user=account_user).count()
    if entry_total == 1:
        award_badge(account_user, "FIRST_JOURNAL", "First Journal", "Logged your first journal entry!!!")
    elif entry_total == 5:
        award_badge(account_user, "5TH_JOURNAL", "Fifth Journal", "Logged your fifth journal entry!!!")
    elif entry_total == 10:
        award_badge(account_user, "10th_Journal", "Tenth Journal", "Logged your Tenth journal entry!!!")

    streak_notify(account_user)
    if journal.habit and getattr(journal.habit, "habit_type", ) == 'Break':
        abst_badge(account_user, journal.habit)



def streak_notify(account_user):
    tod = timezone.localdate()
    streak = 0
    days_ago = tod
   
   
    while True:
        practice_skill = Journal.objects.filter(account_user=account_user, date=days_ago, entry_type=Journal.PRACTICE).exists()
        if not practice_skill:
            break
        streak += 1
        days_ago -= timedelta(days=1)

    if streak >= 3:
        award_badge(account_user, "3_Practice_Streak", "3-day Practice Streak" )
    if streak >= 7:
         award_badge(account_user, "7_Practice_Streak", "7-day Practice Streak" )


def abst_badge(account_user, habit):
    tod = timezone.localdate()
    streak = 0
    days_ago = tod
   
   
    while True:
        laspe_logged = Journal.objects.filter(account_user=account_user, habit=habit, date=days_ago, entry_type=Journal.LAPSE).exists()
        if laspe_logged or habit.start_date:
            break
        streak += 1
        days_ago -= timedelta(days=1)

    if streak >= 3:
        award_badge(account_user, f"ABST_{habit.id}_Streak_3", f"3-day Abstinence from {habit.name}" )
    if streak >= 7:
         award_badge(account_user, f"ABST_{habit.id}_Streak_7", f"7-day Abstinence from {habit.name}" )







def task_completion_badge(task: Task):
    account_user = task.account_user

    if task.status != Task.COMPLETED:
        return
    
    if task.skill:
        task.skill.add_xp(task.points)
    
    task_completed = Task.objects.filter(account_user=account_user, status=Task.COMPLETED).count()
    if task_completed == 1:
        award_badge(account_user, 'FIRST_TASK', 'Fist Task Done')
    elif task_completed == 5:
        award_badge(account_user, '5TH_TASK', 'Five Task Done')
    elif task_completed == 20:
        award_badge(account_user, '20TH_TASK', 'Twenty Task Done')

     


#def quest_completion_proc(account_user):
