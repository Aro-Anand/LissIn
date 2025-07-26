'''
This file contain information about greeting options, Hoe the assistant can greet the user.
'''

from datetime import datetime

def get_time_based_greeting()-> str:
    time = int(datetime.now().strftime("%H"))

    if time <=12:
        return "Good Morning"
    elif time <15 and time >12:
        return "Good Afternoon"
    else:
        return "Good Evening"
    
def create_greeting(name, time_greet, query=""):
    if query:
        return f"{str(time_greet).lower()} {name}. This is LissIn, your AI support assistant. how can I help you today?"
    else:
        return f"{str(time_greet).lower()}{name}. This is LisstIn, your AI support assistant. How can I help you today?"
    