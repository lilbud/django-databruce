# Create your tests here.
import calendar as cal


def weekdays(weekday):
    start = list(cal.day_name).index(weekday)
    return [(i, cal.day_name[(i + start) % 7]) for i in range(7)]


print(weekdays("Sunday"))
