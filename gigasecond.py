from datetime import datetime, timedelta

def add(moment):
    giga_second_date = moment + timedelta(days=11_574, hours=1, minutes=46, seconds=40) 
    return giga_second_date

print(add(datetime(2011, 4, 25, 0, 0)))


