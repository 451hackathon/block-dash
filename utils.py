
import datetime

__all__ = ['get_start_current_month','get_start_current_year','get_start_next_month']

def get_start_current_month():
    return datetime.date.today().replace(day=1) # start of current month

def get_start_current_year():
    return datetime.date.today().replace(day=1, month=1) # start of current year

def get_start_next_month():
    today = datetime.date.today()
    return today.replace(month=today.month+1, day=1) 
