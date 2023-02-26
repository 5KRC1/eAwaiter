from datetime import datetime, timedelta 

def weeks_in_advance(weeks: int, first_week_school):
    today = datetime.now()
    # if weekends => getmonday | fetches another week in advance = error
    # if today.strftime("%w") == "0":
    #     today -= timedelta(days=6)
    # elif today.strftime("%w") == "6":
    #     today -= timedelta(days=5)
    monday = get_monday(today + timedelta(days=weeks*7))    # gets weeks in advance
    return int(str((monday - first_week_school) / 7).split(" ")[0]), monday

def get_monday(date=datetime.now()):
    first_day_num = int(date.strftime("%w"))
    # if not 1 (monday) => need to find monday
    if first_day_num == 1:  # 1 == monday
        return date

    # if weekend => goes forwards
    if first_day_num == 6:    # 6 == sat
        monday = date + timedelta(days=2)   # goes to mon
    elif first_day_num == 0:    # 0 == sun
        monday = date + timedelta(days=1)   # goes to mon
    # if workday => goes backwards
    else:  # if [tue-fri]
        monday = date - timedelta(days=first_day_num - 1)   # goes to mon
    return monday


