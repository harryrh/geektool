#
# Make the time left a bit more pleasant to read
#
def duration_human(seconds):
    seconds = long(round(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365.242199)
 
    minutes = long(minutes)
    hours = long(hours)
    days = long(days)
    years = long(years)
 
    duration = []
    if years > 0:
        duration.append('%d Year' % years + 's'*(years != 1))
    else:
        if days > 0:
            duration.append('%d Day' % days + 's'*(days != 1))
        if hours > 0:
            duration.append('%d Hour' % hours + 's'*(hours != 1))
        if minutes > 0:
            duration.append('%d Minute' % minutes + 's'*(minutes != 1))
        if seconds > 0:
            duration.append('%d Second' % seconds + 's'*(seconds != 1))
    return ', '.join(duration)

