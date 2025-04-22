import unittest
import datetime
from dateutil import rrule

from recurrent.event_parser import RecurringEvent
from recurrent import parse as rparse
from recurrent import format as rformat
from recurrent.translator import is_ru, WordByWordTranslator

NOW = datetime.datetime(2010, 1, 1)
TOMORROW = (NOW + datetime.timedelta(days=1))


class ExpectedFailure(object):
    def __init__(self, v):
        self.correct_value = v


# Expressions consist of the string to feed to parse, the expected result dict, and optionally the expected format result (default = string)
expressions = [
    # recurring events
    ('daily', dict(freq='daily', interval=1)),
    ('ежедневно', dict(freq='daily', interval=1)),

    ('each day', dict(freq='daily', interval=1), 'daily'),
    ('каждый день', dict(freq='daily', interval=1), 'daily'),

    ('everyday', dict(freq='daily', interval=1), 'daily'),
    ('каждый день', dict(freq='daily', interval=1), 'daily'),

    ('every day twice', dict(freq='daily', interval=1, count=2), 'daily twice'),
    ('каждый день дважды', dict(freq='daily', interval=1, count=2), 'daily twice'),

    ('every day for 3x', dict(freq='daily', interval=1, count=3), 'daily for 3 times'),
    ('каждый день 3 раза', dict(freq='daily', interval=1, count=3), 'daily for 3 times'),

    ('every day for 4 times', dict(freq='daily', interval=1, count=4), 'daily for 4 times'),
    ('каждый день 4 раза', dict(freq='daily', interval=1, count=4), 'daily for 4 times'),

    ('every day for 5 occurrences', dict(freq='daily', interval=1, count=5), 'daily for 5 times'),
    ('каждый день 5 раз', dict(freq='daily', interval=1, count=5), 'daily for 5 times'),

    ('every other day', dict(freq='daily', interval=2)),
    ('через день', dict(freq='daily', interval=2)),

    ('every 4 days', dict(freq='daily', interval=4)),
    ('каждые 4 дня', dict(freq='daily', interval=4)),

    ('every 4th day', dict(freq='daily', interval=4), 'every 4 days'),
    ('каждый 4-й день', dict(freq='daily', interval=4), 'every 4 days'),

    ('daily except for tomorrow', dict(freq='daily', interval=1, exdate=[TOMORROW.date()]), 'daily except on Sat Jan 2, 2010'),
    ('ежедневно кроме завтрашнего дня', dict(freq='daily', interval=1, exdate=[TOMORROW.date()]), 'daily except on Sat Jan 2, 2010'),

    ('daily except on weekends', dict(freq='daily', interval=1, exrule='BYDAY=SA,SU;INTERVAL=1;FREQ=WEEKLY'), 'daily except weekends'),
    ('ежедневно кроме выходных', dict(freq='daily', interval=1, exrule='BYDAY=SA,SU;INTERVAL=1;FREQ=WEEKLY'), 'daily except weekends'),

    ('daily except in may', dict(freq='daily', interval=1, exdate=[[5, NOW.year]]), 'daily except in May'),
    ('ежедневно кроме мая', dict(freq='daily', interval=1, exdate=[[5, NOW.year]]), 'daily except in May'),

    ('daily except in may %s' % NOW.year, dict(freq='daily', interval=1, exdate=[[5, NOW.year]]), 'daily except in May'),
    ('ежедневно кроме мая %s' % NOW.year, dict(freq='daily', interval=1, exdate=[[5, NOW.year]]), 'daily except in May'),

    ('tuesdays', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),
    ('по вторникам', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),

    ('weekends', dict(freq='weekly', interval=1, byday='SA,SU')),
    ('по выходным', dict(freq='weekly', interval=1, byday='SA,SU')),

    ('every other weekend', dict(freq='weekly', interval=2, byday='SA,SU'), 'every other week on weekend'),
    ('через выходные', dict(freq='weekly', interval=2, byday='SA,SU'), 'every other week on weekend'),

    ('every other week on weekend', dict(freq='weekly', interval=2, byday='SA,SU')),
    ('каждую вторую неделю по выходным', dict(freq='weekly', interval=2, byday='SA,SU')),

    ('every 4 weekends', dict(freq='weekly', interval=4, byday='SA,SU'), 'every 4 weeks on weekend'),
    ('каждые 4 выходных', dict(freq='weekly', interval=4, byday='SA,SU'), 'every 4 weeks on weekend'),

    ('every 4 weekends except in july and sept', dict(freq='weekly', interval=4, byday='SA,SU', exdate=[[7, NOW.year], [9, NOW.year]]), 'every 4 weeks on weekend except in Jul and Sep'),
    ('каждые 4 выходных кроме июля и сентября', dict(freq='weekly', interval=4, byday='SA,SU', exdate=[[7, NOW.year], [9, NOW.year]]), 'every 4 weeks on weekend except in Jul and Sep'),

    ('every 4 weeks on weekends', dict(freq='weekly', interval=4, byday='SA,SU'), 'every 4 weeks on weekend'),
    ('каждые 4 недели по выходным', dict(freq='weekly', interval=4, byday='SA,SU'), 'every 4 weeks on weekend'),

    ('every 4th week on weekends', dict(freq='weekly', interval=4, byday='SA,SU'), 'every 4 weeks on weekend'),
    ('каждую 4-ю неделю по выходным', dict(freq='weekly', interval=4, byday='SA,SU'), 'every 4 weeks on weekend'),

    ('weekdays', dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR')),
    ('по будням', dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR')),

    ('every weekday', dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR'), 'weekdays'),
    ('каждый будний день', dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR'), 'weekdays'),

    ('tuesdays and thursdays', dict(freq='weekly', interval=1, byday='TU,TH'), 'every Tue and Thu'),
    ('по вторникам и четвергам', dict(freq='weekly', interval=1, byday='TU,TH'), 'every Tue and Thu'),

    ('weekly on wednesdays', dict(freq='weekly', interval=1, byday='WE'), 'every Wed'),
    ('еженедельно по средам', dict(freq='weekly', interval=1, byday='WE'), 'every Wed'),

    ('weekly on wednesdays and fridays', dict(freq='weekly', interval=1, byday='WE,FR'), 'every Wed and Fri'),
    ('еженедельно по средам и пятницам', dict(freq='weekly', interval=1, byday='WE,FR'), 'every Wed and Fri'),

    ('every sunday and saturday', dict(freq='weekly', interval=1, byday='SU,SA'), 'every Sun and Sat'),
    ('каждое воскресенье и субботу', dict(freq='weekly', interval=1, byday='SU,SA'), 'every Sun and Sat'),

    ('every wed', dict(freq='weekly', interval=1, byday='WE'), 'every Wed'),
    ('каждую среду', dict(freq='weekly', interval=1, byday='WE'), 'every Wed'),

    ('every week on tues', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),
    ('раз в неделю во вторник', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),

    ('once a week on sunday', dict(freq='weekly', interval=1, byday='SU'), 'every Sun'),
    ('раз в неделю в воскресенье', dict(freq='weekly', interval=1, byday='SU'), 'every Sun'),

    ('every week on the 4th day', dict(freq='weekly', interval=1, byday='WE'), 'every Wed'),
    ('каждую неделю на 4-й день', dict(freq='weekly', interval=1, byday='WE'), 'every Wed'),

    ('every other week on mon', dict(freq='weekly', interval=2, byday='MO'), 'every other week on Mon'),
    ('через неделю по понедельникам', dict(freq='weekly', interval=2, byday='MO'), 'every other week on Mon'),

    ('every 3 weeks on mon', dict(freq='weekly', interval=3, byday='MO'), 'every 3 weeks on Mon'),
    ('каждые 3 недели по понедельникам', dict(freq='weekly', interval=3, byday='MO'), 'every 3 weeks on Mon'),

    ('every other week on mon and fri', dict(freq='weekly', interval=2, byday='MO,FR'), 'every other week on Mon and Fri'),
    ('через неделю по понедельникам и пятницам', dict(freq='weekly', interval=2, byday='MO,FR'), 'every other week on Mon and Fri'),

    ('every 3 weeks on mon and fri', dict(freq='weekly', interval=3, byday='MO,FR'), 'every 3 weeks on Mon and Fri'),
    ('каждые 3 недели по понедельникам и пятницам', dict(freq='weekly', interval=3, byday='MO,FR'), 'every 3 weeks on Mon and Fri'),

    ('every 3 days', dict(freq='daily', interval=3)),
    ('каждые 3 дня', dict(freq='daily', interval=3)),

    ('every 2nd of the month', dict(freq='monthly', interval=1, bymonthday='2'), '2nd of every month'),
    ('каждое 2-е число месяца', dict(freq='monthly', interval=1, bymonthday='2'), '2nd of every month'),

    ('every 4th of the month', dict(freq='monthly', interval=1, bymonthday='4'), '4th of every month'),
    ('каждое 4-е число месяца', dict(freq='monthly', interval=1, bymonthday='4'), '4th of every month'),

    ('4th of every month', dict(freq='monthly', interval=1, bymonthday='4')),
    ('4-е каждого месяца', dict(freq='monthly', interval=1, bymonthday='4')),

    ('every month on the 4th', dict(freq='monthly', interval=1, bymonthday='4'), '4th of every month'),
    ('каждый месяц 4-го числа', dict(freq='monthly', interval=1, bymonthday='4'), '4th of every month'),

    ('every month on the 4th day', dict(freq='monthly', interval=1, bymonthday='4'), '4th of every month'),
    ('каждый месяц на 4-й день', dict(freq='monthly', interval=1, bymonthday='4'), '4th of every month'),

    ('the 4th of every other month', dict(freq='monthly', interval=2, bymonthday='4'), '4th of every other month'),
    ('4-е через месяц', dict(freq='monthly', interval=2, bymonthday='4'), '4th of every other month'),

    ('the 4th of every 3 months', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),
    ('4-е каждые 3 месяца', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),

    ('every other month on the 4th', dict(freq='monthly', interval=2, bymonthday='4'), '4th of every other month'),
    ('каждый второй месяц 4-го числа', dict(freq='monthly', interval=2, bymonthday='4'), '4th of every other month'),

    ('every 3 months on the 4th', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),
    ('каждые 3 месяца 4-го числа', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),

    ('the 4th of every 3rd month', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),
    ('4-е каждого третьего месяца', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),

    ('every 3rd month on the 4th', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),
    ('каждый 3-й месяц 4-го числа', dict(freq='monthly', interval=3, bymonthday='4'), '4th of every 3 months'),

    ('every 4th and 10th of the month', dict(freq='monthly', interval=1, bymonthday='4,10'), '4th and 10th of every month'),
    ('4-го и 10-го числа каждого месяца', dict(freq='monthly', interval=1, bymonthday='4,10'), '4th and 10th of every month'),

    ('every 4th and 10th of the month up to 7x', dict(freq='monthly', interval=1, bymonthday='4,10', count=7), '4th and 10th of every month for 7 times'),
    ('4-го и 10-го числа каждого месяца до 7 раз', dict(freq='monthly', interval=1, bymonthday='4,10', count=7), '4th and 10th of every month for 7 times'),

    ('every first friday of the month', dict(freq='monthly', interval=1, byday='1FR'), '1st Fri of every month'),
    ('каждую первую пятницу месяца', dict(freq='monthly', interval=1, byday='1FR'), '1st Fri of every month'),

    ('monthly on fri', dict(freq='monthly', interval=1, byday='FR'), 'Fri of every month'),
    ('ежемесячно по пятницам', dict(freq='monthly', interval=1, byday='FR'), 'Fri of every month'),

    ('monthly on tue and fri', dict(freq='monthly', interval=1, byday='TU,FR'), 'Tue and Fri of every month'),
    ('ежемесячно по вторникам и пятницам', dict(freq='monthly', interval=1, byday='TU,FR'), 'Tue and Fri of every month'),

    ('monthly on the first and last instance of tue and fri', dict(freq='monthly', interval=1, byday='TU,FR', bysetpos='1,-1'), 'for the 1st and last instance of Tue and Fri of every month'),
    ('ежемесячно в первый и последний вторник и пятницу', dict(freq='monthly', interval=1, byday='TU,FR', bysetpos='1,-1'), 'for the 1st and last instance of Tue and Fri of every month'),

    ('every last friday of the month', dict(freq='monthly', interval=1, byday='-1FR'), 'last Fri of every month'),
    ('каждую последнюю пятницу месяца', dict(freq='monthly', interval=1, byday='-1FR'), 'last Fri of every month'),

    ('2nd to the last friday of each month', dict(freq='monthly', interval=1, byday='-2FR'), '2nd to the last Fri of every month'),
    ('вторая с конца пятница каждого месяца', dict(freq='monthly', interval=1, byday='-2FR'), '2nd to the last Fri of every month'),

    ('2nd and last fri of each month', dict(freq='monthly', interval=1, byday='2FR,-1FR'), '2nd and last Fri of every month'),
    ('вторая и последняя пятница каждого месяца', dict(freq='monthly', interval=1, byday='2FR,-1FR'), '2nd and last Fri of every month'),

    ('2nd and 2nd to the last fri of each month', dict(freq='monthly', interval=1, byday='2FR,-2FR'), '2nd and 2nd to the last Fri of every month'),
    ('вторая и предпоследняя пятница каждого месяца', dict(freq='monthly', interval=1, byday='2FR,-2FR'), '2nd and 2nd to the last Fri of every month'),

    ('2nd and last fridays of each month', dict(freq='monthly', interval=1, byday='2FR,-1FR'), '2nd and last Fri of every month'),
    ('вторая и последняя пятницы каждого месяца', dict(freq='monthly', interval=1, byday='2FR,-1FR'), '2nd and last Fri of every month'),

    ('first day of each month', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('первый день каждого месяца', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('beginning of each month', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('начало каждого месяца', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('begin of each month', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('начало месяца', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('start of each month', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('старт каждого месяца', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('every month on the 1st day', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('каждый месяц в первый день', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('every month at the beginning', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('каждый месяц в начале', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('every month at the begin', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('каждый месяц в начале', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('every month at the start', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('каждый месяц на старте', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('first of each month', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),
    ('первое число каждого месяца', dict(freq='monthly', interval=1, bymonthday='1'), '1st of every month'),

    ('last of each month', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),
    ('последнее число каждого месяца', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),

    ('end of each month', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),
    ('конец каждого месяца', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),

    ('2nd to the last of each month', dict(freq='monthly', interval=1, bymonthday='-2'), '2nd to the last of every month'),
    ('второй с конца день каждого месяца', dict(freq='monthly', interval=1, bymonthday='-2'), '2nd to the last of every month'),

    ('last day of each month', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),
    ('последний день каждого месяца', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),

    ('each month at the end', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),
    ('в конце каждого месяца', dict(freq='monthly', interval=1, bymonthday='-1'), 'last of every month'),

    ('2nd friday of each month', dict(freq='monthly', interval=1, byday='2FR'), '2nd Fri of every month'),
    ('вторая пятница каждого месяца', dict(freq='monthly', interval=1, byday='2FR'), '2nd Fri of every month'),

    ('second friday of each month', dict(freq='monthly', interval=1, byday='2FR'), '2nd Fri of every month'),
    ('вторая пятница месяца', dict(freq='monthly', interval=1, byday='2FR'), '2nd Fri of every month'),

    ('first friday of every month', dict(freq='monthly', interval=1, byday='1FR'), '1st Fri of every month'),
    ('первая пятница каждого месяца', dict(freq='monthly', interval=1, byday='1FR'), '1st Fri of every month'),

    ('first friday of each month', dict(freq='monthly', interval=1, byday='1FR'), '1st Fri of every month'),
    ('первая пятница месяца', dict(freq='monthly', interval=1, byday='1FR'), '1st Fri of every month'),

    ('first friday of every other month', dict(freq='monthly', interval=2, byday='1FR'), '1st Fri of every other month'),
    ('первая пятница через месяц', dict(freq='monthly', interval=2, byday='1FR'), '1st Fri of every other month'),

    ('first friday of every 3 months', dict(freq='monthly', interval=3, byday='1FR'), '1st Fri of every 3 months'),
    ('первая пятница каждые 3 месяца', dict(freq='monthly', interval=3, byday='1FR'), '1st Fri of every 3 months'),

    ('first friday of every 3rd month', dict(freq='monthly', interval=3, byday='1FR'), '1st Fri of every 3 months'),
    ('первая пятница каждого третьего месяца', dict(freq='monthly', interval=3, byday='1FR'), '1st Fri of every 3 months'),

    ('first and third friday of each month', dict(freq='monthly', interval=1, byday='1FR,3FR'), '1st and 3rd Fri of every month'),
    ('первая и третья пятница каждого месяца', dict(freq='monthly', interval=1, byday='1FR,3FR'), '1st and 3rd Fri of every month'),

    ('first, second, and third friday of each month', dict(freq='monthly', interval=1, byday='1FR,2FR,3FR'), '1st and 2nd and 3rd Fri of every month'),
    ('первая, вторая и третья пятница каждого месяца', dict(freq='monthly', interval=1, byday='1FR,2FR,3FR'), '1st and 2nd and 3rd Fri of every month'),

    ('first and third friday and second tuesday of each month', dict(freq='monthly', interval=1, byday='1FR,3FR,2TU'), '1st and 3rd Fri and 2nd Tue of every month'),
    ('первая и третья пятница и второй вторник каждого месяца', dict(freq='monthly', interval=1, byday='1FR,3FR,2TU'), '1st and 3rd Fri and 2nd Tue of every month'),

    ('yearly on the fourth thursday in november', dict(freq='yearly', interval=1, byday='4TH', bymonth='11'), 'every 4th Thu in Nov'),
    ('каждый год в четвёртый четверг ноября', dict(freq='yearly', interval=1, byday='4TH', bymonth='11'), 'every 4th Thu in Nov'),

    ('every year on the fourth thursday in november', dict(freq='yearly', interval=1, byday='4TH', bymonth='11'), 'every 4th Thu in Nov'),
    ('каждый год на четвёртый четверг ноября', dict(freq='yearly', interval=1, byday='4TH', bymonth='11'), 'every 4th Thu in Nov'),

    ('every fourth thursday in november', dict(freq='yearly', interval=1, byday='4TH', bymonth='11'), 'every 4th Thu in Nov'),
    ('каждый четвёртый четверг ноября', dict(freq='yearly', interval=1, byday='4TH', bymonth='11'), 'every 4th Thu in Nov'),

    ('every other year on the fourth thursday in november', dict(freq='yearly', interval=2, byday='4TH', bymonth='11'), 'every other 4th Thu in Nov'),
    ('через год в четвёртый четверг ноября', dict(freq='yearly', interval=2, byday='4TH', bymonth='11'), 'every other 4th Thu in Nov'),

    ('every 3 years on the fourth thursday in november', dict(freq='yearly', interval=3, byday='4TH', bymonth='11'), 'every 3 years on the 4th Thu in Nov'),
    ('каждые 3 года в четвёртый четверг ноября', dict(freq='yearly', interval=3, byday='4TH', bymonth='11'), 'every 3 years on the 4th Thu in Nov'),

    ('every 3rd year on the fourth thursday in november', dict(freq='yearly', interval=3, byday='4TH', bymonth='11'), 'every 3 years on the 4th Thu in Nov'),
    ('каждый третий год в четвёртый четверг ноября', dict(freq='yearly', interval=3, byday='4TH', bymonth='11'), 'every 3 years on the 4th Thu in Nov'),

    ('once a year on december 25th', dict(freq='yearly', interval=1, bymonthday='25', bymonth='12'), 'every Dec 25th'),
    ('раз в год 25 декабря', dict(freq='yearly', interval=1, bymonthday='25', bymonth='12'), 'every Dec 25th'),

    ('every year on december 21st and 31st', dict(freq='yearly', interval=1, bymonthday='21,31', bymonth='12'), 'every Dec 21st and 31st'),
    ('каждый год 21 и 31 декабря', dict(freq='yearly', interval=1, bymonthday='21,31', bymonth='12'), 'every Dec 21st and 31st'),

    ('every year on december 31st', dict(freq='yearly', interval=1, bymonthday='31', bymonth='12'), 'every Dec 31st'),
    ('каждый год 31 декабря', dict(freq='yearly', interval=1, bymonthday='31', bymonth='12'), 'every Dec 31st'),

    ('every year on the 31st', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),
    ('каждый год на 31-й день', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),

    ('31st of every year', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),
    ('31-й день каждого года', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),

    ('31st day of every year', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),
    ('31-й день в году', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),

    ('every year on the 31st day', dict(freq='yearly', interval=1, byyearday='31')),
    ('каждый год в 31-й день', dict(freq='yearly', interval=1, byyearday='31')),

    ('every year on the day 31', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),
    ('каждый год в день 31', dict(freq='yearly', interval=1, byyearday='31'), 'every year on the 31st day'),

    ('every july 4th', dict(freq='yearly', interval=1, bymonthday='4', bymonth='7'), 'every Jul 4th'),
    ('каждый год 4 июля', dict(freq='yearly', interval=1, bymonthday='4', bymonth='7'), 'every Jul 4th'),

    ('every aug 30', dict(freq='yearly', interval=1, bymonthday='30', bymonth='8'), 'every Aug 30th'),
    ('каждый год 30 августа', dict(freq='yearly', interval=1, bymonthday='30', bymonth='8'), 'every Aug 30th'),

    ('every aug 20 and 30', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),
    ('каждый год 20 и 30 августа', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),

    ('every aug on day 20 and 30', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),
    ('каждый год в августе 20-го и 30-го числа', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),

    ('every 20th and 30th of aug', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),
    ('20-е и 30-е августа каждого года', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),

    ('every year in week 12', dict(freq='yearly', interval=1, byweekno='12'), 'every year in week 12'),
    ('каждый год в 12-й неделе', dict(freq='yearly', interval=1, byweekno='12'), 'every year in week 12'),

    ('every 3 years on Fri in week 12', dict(freq='yearly', interval=3, byday='FR', byweekno='12'), 'every 3 years on Fri in week 12'),
    ('каждые 3 года в пятницу 12-й недели', dict(freq='yearly', interval=3, byday='FR', byweekno='12'), 'every 3 years on Fri in week 12'),

    ('every Fri in week 12', dict(freq='yearly', interval=1, byday='FR', byweekno='12'), 'every Fri in week 12'),
    ('каждая пятница 12-й недели', dict(freq='yearly', interval=1, byday='FR', byweekno='12'), 'every Fri in week 12'),

    ('every Fri in week 12 and 14', dict(freq='yearly', interval=1, byday='FR', byweekno='12,14'), 'every Fri in week 12 and 14'),
    ('каждая пятница 12-й и 14-й недели', dict(freq='yearly', interval=1, byday='FR', byweekno='12,14'), 'every Fri in week 12 and 14'),

    ('every 20th and 30th of aug', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),
    ('каждое 20-е и 30-е августа', dict(freq='yearly', interval=1, bymonthday='20,30', bymonth='8'), 'every Aug 20th and 30th'),

    # with start and end dates
    ('daily starting march 3rd', dict(dtstart='%d0303' % NOW.year, freq='daily', interval=1), 'daily starting Wed Mar 3, 2010'),
    ('ежедневно начиная с 3 марта', dict(dtstart='%d0303' % NOW.year, freq='daily', interval=1), 'daily starting Wed Mar 3, 2010'),

    ('starting in april, daily until march', dict(dtstart='%d0401' % NOW.year, freq='daily', interval=1, until='%d0301' % (NOW.year + 1)), 'daily from Thu Apr 1, 2010 to Tue Mar 1, 2011'),
    ('начиная с апреля ежедневно до марта', dict(dtstart='%d0401' % NOW.year, freq='daily', interval=1, until='%d0301' % (NOW.year + 1)), 'daily from Thu Apr 1, 2010 to Tue Mar 1, 2011'),

    ('daily starting in april until march', dict(dtstart='%d0401' % NOW.year, freq='daily', interval=1, until='%d0301' % (NOW.year + 1)), 'daily from Thu Apr 1, 2010 to Tue Mar 1, 2011'),
    ('ежедневно начиная с апреля до марта', dict(dtstart='%d0401' % NOW.year, freq='daily', interval=1, until='%d0301' % (NOW.year + 1)), 'daily from Thu Apr 1, 2010 to Tue Mar 1, 2011'),

    ('daily starting march 3rd except on march 6th and march 8th', dict(dtstart='%d0303' % NOW.year, freq='daily', interval=1, exdate=[datetime.date(NOW.year, 3, 6), datetime.date(NOW.year, 3, 8)]), 'daily starting Wed Mar 3, 2010 except on Sat Mar 6, 2010 and Mon Mar 8, 2010'),
    ('ежедневно начиная с 3 марта, кроме 6 и 8 марта', dict(dtstart='%d0303' % NOW.year, freq='daily', interval=1, exdate=[datetime.date(NOW.year, 3, 6), datetime.date(NOW.year, 3, 8)]), 'daily starting Wed Mar 3, 2010 except on Sat Mar 6, 2010 and Mon Mar 8, 2010'),

    ('starting tomorrow on weekends', dict(dtstart='%d0102' % NOW.year, freq='weekly', interval=1, byday='SA,SU'), 'weekends'),
    ('начиная с завтрашнего дня по выходным', dict(dtstart='%d0102' % NOW.year, freq='weekly', interval=1, byday='SA,SU'), 'weekends'),

    ('daily starting march 3rd until april 5th', dict(dtstart='%d0303' % NOW.year, until='%d0405' % NOW.year, freq='daily', interval=1), 'daily from Wed Mar 3, 2010 to Mon Apr 5, 2010'),
    ('ежедневно начиная с 3 марта до 5 апреля', dict(dtstart='%d0303' % NOW.year, until='%d0405' % NOW.year, freq='daily', interval=1), 'daily from Wed Mar 3, 2010 to Mon Apr 5, 2010'),

    ('daily starting march 3rd for 8 times', dict(dtstart='%d0303' % NOW.year, count=8, freq='daily', interval=1), 'daily starting Wed Mar 3, 2010 for 8 times'),
    ('ежедневно начиная с 3 марта 8 раз', dict(dtstart='%d0303' % NOW.year, count=8, freq='daily', interval=1), 'daily starting Wed Mar 3, 2010 for 8 times'),

    ('every wed until november', dict(until='%d1101' % NOW.year, freq='weekly', interval=1, byday='WE'), 'every Wed until Mon Nov 1, 2010'),
    ('каждую среду до ноября', dict(until='%d1101' % NOW.year, freq='weekly', interval=1, byday='WE'), 'every Wed until Mon Nov 1, 2010'),

    ('every wed until november except in march and may', dict(until='%d1101' % NOW.year, freq='weekly', interval=1, byday='WE', exdate=[[3, NOW.year], [5, NOW.year]]), 'every Wed until Mon Nov 1, 2010 except in Mar and May'),
    ('каждую среду до ноября, кроме марта и мая', dict(until='%d1101' % NOW.year, freq='weekly', interval=1, byday='WE', exdate=[[3, NOW.year], [5, NOW.year]]), 'every Wed until Mon Nov 1, 2010 except in Mar and May'),

    ('every wed from november until june except in march and may', dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1), freq='weekly', interval=1, byday='WE', exdate=[[3, NOW.year + 1], [5, NOW.year + 1]]), 'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Mar 2011 and May 2011'),
    ('каждую среду с ноября по июнь, кроме марта и мая', dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1), freq='weekly', interval=1, byday='WE', exdate=[[3, NOW.year + 1], [5, NOW.year + 1]]), 'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Mar 2011 and May 2011'),

    ('every wed from november until june except in december and may',
     dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1),
          freq='weekly', interval=1, byday='WE', exdate=[[12, NOW.year], [5, NOW.year + 1]]),
     'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Dec and May 2011'),

    ('каждую среду с ноября по июнь, кроме декабря и мая',
     dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1),
          freq='weekly', interval=1, byday='WE', exdate=[[12, NOW.year], [5, NOW.year + 1]]),
     'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Dec and May 2011'),

    ('every wed from november until june except in december and mar and may',
     dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1),
          freq='weekly', interval=1, byday='WE', exdate=[[12, NOW.year], [3, NOW.year + 1], [5, NOW.year + 1]]),
     'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Dec and Mar 2011 and May 2011'),

    ('каждую среду с ноября по июнь, кроме декабря, марта и мая',
     dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1),
          freq='weekly', interval=1, byday='WE', exdate=[[12, NOW.year], [3, NOW.year + 1], [5, NOW.year + 1]]),
     'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Dec and Mar 2011 and May 2011'),

    ('every wed from november until june except in march %d and may %d' % (NOW.year + 1, NOW.year + 1),
     dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1),
          freq='weekly', interval=1, byday='WE', exdate=[[3, NOW.year + 1], [5, NOW.year + 1]]),
     'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Mar 2011 and May 2011'),

    ('каждую среду с ноября по июнь, кроме марта %d и мая %d' % (NOW.year + 1, NOW.year + 1),
     dict(dtstart='%d1101' % NOW.year, until='%d0601' % (NOW.year + 1),
          freq='weekly', interval=1, byday='WE', exdate=[[3, NOW.year + 1], [5, NOW.year + 1]]),
     'every Wed from Mon Nov 1, 2010 to Wed Jun 1, 2011 except in Mar 2011 and May 2011'),

    ('every 4th of the month starting next tuesday',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4'),
     '4th of every month starting Tue Jan 5, 2010'),

    ('каждое 4-е число месяца начиная со следующего вторника',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4'),
     '4th of every month starting Tue Jan 5, 2010'),

    ('4th of each month starting next tuesday',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4'),
     '4th of every month starting Tue Jan 5, 2010'),

    ('4-е каждого месяца начиная со следующего вторника',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4'),
     '4th of every month starting Tue Jan 5, 2010'),

    ('starting next tuesday on the 4th of each month',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4'),
     '4th of every month starting Tue Jan 5, 2010'),

    ('начиная со следующего вторника 4-го числа каждого месяца',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4'),
     '4th of every month starting Tue Jan 5, 2010'),

    ('every 4th of the month starting next tuesday for 3 occurrences',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4', count=3),
     '4th of every month starting Tue Jan 5, 2010 for 3 times'),

    ('каждое 4-е число месяца начиная со следующего вторника 3 раза',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4', count=3),
     '4th of every month starting Tue Jan 5, 2010 for 3 times'),

    ('starting next tuesday the 4th of each month for 3 occurrences',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4', count=3),
     '4th of every month starting Tue Jan 5, 2010 for 3 times'),

    ('начиная со следующего вторника 4-е число каждого месяца 3 раза',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4', count=3),
     '4th of every month starting Tue Jan 5, 2010 for 3 times'),

    ('4th of each month starting next tuesday for 3 occurrences',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4', count=3),
     '4th of every month starting Tue Jan 5, 2010 for 3 times'),

    ('4-е каждого месяца начиная со следующего вторника 3 раза',
     dict(dtstart=(NOW + datetime.timedelta(days=(1 - NOW.weekday()) % 7)).strftime('%Y%m%d'),
          freq='monthly', interval=1, bymonthday='4', count=3),
     '4th of every month starting Tue Jan 5, 2010 for 3 times'),

    ('mondays and thursdays from jan 1 to march 25th',
     dict(dtstart='%d0101' % NOW.year, until='%d0325' % NOW.year,
          freq='weekly', interval=1, byday='MO,TH'),
     'every Mon and Thu until Thu Mar 25, 2010'),

    ('по понедельникам и четвергам с 1 января по 25 марта',
     dict(dtstart='%d0101' % NOW.year, until='%d0325' % NOW.year,
          freq='weekly', interval=1, byday='MO,TH'),
     'every Mon and Thu until Thu Mar 25, 2010'),

    ('mondays and thursdays starting jan 1 for 6 times',
     dict(dtstart='%d0101' % NOW.year, count=6,
          freq='weekly', interval=1, byday='MO,TH'),
     'every Mon and Thu for 6 times'),

    ('по понедельникам и четвергам начиная с 1 января 6 раз',
     dict(dtstart='%d0101' % NOW.year, count=6,
          freq='weekly', interval=1, byday='MO,TH'),
     'every Mon and Thu for 6 times'),

    # time recurrences
    ('every 5 minutes', dict(freq='minutely', interval=5)),
    ('каждые 5 минут', dict(freq='minutely', interval=5)),

    ('every 1 second', dict(freq='secondly', interval=1), 'every second'),
    ('каждую секунду', dict(freq='secondly', interval=1), 'every second'),

    ('every second', dict(freq='secondly', interval=1)),
    ('каждую секунду', dict(freq='secondly', interval=1)),

    ('every 30 seconds', dict(freq='secondly', interval=30)),
    ('каждые 30 секунд', dict(freq='secondly', interval=30)),

    ('every 90 secs', dict(freq='secondly', interval=90), 'every 90 seconds'),
    ('каждые 90 секунд', dict(freq='secondly', interval=90), 'every 90 seconds'),

    ('every other hour', dict(freq='hourly', interval=2)),
    ('через час', dict(freq='hourly', interval=2)),

    ('every 2 hours', dict(freq='hourly', interval=2), 'every other hour'),
    ('каждые 2 часа', dict(freq='hourly', interval=2), 'every other hour'),

    ('every 2 hours twice', dict(freq='hourly', interval=2, count=2), 'every other hour twice'),
    ('каждые 2 часа 2 раза', dict(freq='hourly', interval=2, count=2), 'every other hour twice'),

    ('every 8 hours except tomorrow',
     dict(freq='hourly', interval=8, exdate=[TOMORROW.date()]),
     'every 8 hours except on Sat Jan 2, 2010 and Sat Jan 2, 2010 8am and Sat Jan 2, 2010 4pm'),
    ('каждые 8 часов кроме завтрашнего дня',
     dict(freq='hourly', interval=8, exdate=[TOMORROW.date()]),
     'every 8 hours except on Sat Jan 2, 2010 and Sat Jan 2, 2010 8am and Sat Jan 2, 2010 4pm'),

    ('every 8 hours except daily at 12am',
     dict(freq='hourly', interval=8, exrule='BYHOUR=0;BYMINUTE=0;INTERVAL=1;FREQ=DAILY'),
     'every 8 hours except daily at 12am'),
    ('каждые 8 часов кроме ежедневного времени в 00:00',
     dict(freq='hourly', interval=8, exrule='BYHOUR=0;BYMINUTE=0;INTERVAL=1;FREQ=DAILY'),
     'every 8 hours except daily at 12am'),

    ('every 12 hours except 1/2 and 1/3',
     dict(freq='hourly', interval=12, exdate=[datetime.date(NOW.year, 1, 2), datetime.date(NOW.year, 1, 3)]),
     'every 12 hours except on Sat Jan 2, 2010 and Sat Jan 2, 2010 12pm and Sun Jan 3, 2010 and Sun Jan 3, 2010 12pm'),
    ('каждые 12 часов кроме 2 и 3 января',
     dict(freq='hourly', interval=12, exdate=[datetime.date(NOW.year, 1, 2), datetime.date(NOW.year, 1, 3)]),
     'every 12 hours except on Sat Jan 2, 2010 and Sat Jan 2, 2010 12pm and Sun Jan 3, 2010 and Sun Jan 3, 2010 12pm'),

    ('every 8 hours except tomorrow at 8am',
     dict(freq='hourly', interval=8, exdate=[TOMORROW + datetime.timedelta(hours=8)]),
     'every 8 hours except on Sat Jan 2, 2010 8am'),
    ('каждые 8 часов, кроме завтра в 8 утра',
     dict(freq='hourly', interval=8, exdate=[TOMORROW + datetime.timedelta(hours=8)]),
     'every 8 hours except on Sat Jan 2, 2010 8am'),

    ('every 8 hours except tomorrow at 8am and 1/5 at 4pm',
     dict(freq='hourly', interval=8, exdate=[
         TOMORROW + datetime.timedelta(hours=8),
         datetime.datetime(NOW.year, 1, 5, 16)]),
     'every 8 hours except on Sat Jan 2, 2010 8am and Tue Jan 5, 2010 4pm'),
    ('каждые 8 часов, кроме завтра в 8 утра и 5 января в 16:00',
     dict(freq='hourly', interval=8, exdate=[
         TOMORROW + datetime.timedelta(hours=8),
         datetime.datetime(NOW.year, 1, 5, 16)]),
     'every 8 hours except on Sat Jan 2, 2010 8am and Tue Jan 5, 2010 4pm'),

    ('every 8 hours except tomorrow and 1/5 at 4pm and Jan 7th at 8am',
     dict(freq='hourly', interval=8, exdate=[
         TOMORROW.date(),
         datetime.datetime(NOW.year, 1, 5, 16),
         datetime.datetime(NOW.year, 1, 7, 8)]),
     'every 8 hours except on Sat Jan 2, 2010 and Sat Jan 2, 2010 8am and Sat Jan 2, 2010 4pm and Tue Jan 5, 2010 4pm and Thu Jan 7, 2010 8am'),
    ('каждые 8 часов, кроме завтра, 5 января в 16:00 и 7 января в 8:00',
     dict(freq='hourly', interval=8, exdate=[
         TOMORROW.date(),
         datetime.datetime(NOW.year, 1, 5, 16),
         datetime.datetime(NOW.year, 1, 7, 8)]),
     'every 8 hours except on Sat Jan 2, 2010 and Sat Jan 2, 2010 8am and Sat Jan 2, 2010 4pm and Tue Jan 5, 2010 4pm and Thu Jan 7, 2010 8am'),

    ('every 20 min', dict(freq='minutely', interval=20), 'every 20 minutes'),
    ('каждые 20 минут', dict(freq='minutely', interval=20), 'every 20 minutes'),

    ('every 45 mins', dict(freq='minutely', interval=45), 'every 45 minutes'),
    ('каждые 45 минут', dict(freq='minutely', interval=45), 'every 45 minutes'),

    # with times
    ('daily at 12am', dict(freq='daily', interval=1, byhour='0', byminute='0')),
    ('ежедневно в 00:00', dict(freq='daily', interval=1, byhour='0', byminute='0')),

    ('daily at 12a', dict(freq='daily', interval=1, byhour='0', byminute='0'), 'daily at 12am'),
    ('ежедневно в 12 ночи', dict(freq='daily', interval=1, byhour='0', byminute='0'), 'daily at 12am'),

    ('daily at 3am', dict(freq='daily', interval=1, byhour='3', byminute='0')),
    ('ежедневно в 3 утра', dict(freq='daily', interval=1, byhour='3', byminute='0')),

    ('daily at 3am 10x', dict(freq='daily', interval=1, byhour='3', byminute='0', count=10), 'daily at 3am for 10 times'),
    ('ежедневно в 3 утра 10 раз', dict(freq='daily', interval=1, byhour='3', byminute='0', count=10), 'daily at 3am for 10 times'),

    ('daily at 3:00am', dict(freq='daily', interval=1, byhour='3', byminute='0'), 'daily at 3am'),
    ('ежедневно в 3:00 утра', dict(freq='daily', interval=1, byhour='3', byminute='0'), 'daily at 3am'),

    ('daily at 3:01am', dict(freq='daily', interval=1, byhour='3', byminute='1')),
    ('ежедневно в 3:01 утра', dict(freq='daily', interval=1, byhour='3', byminute='1')),

    ('daily at 12pm', dict(freq='daily', interval=1, byhour='12', byminute='0')),
    ('ежедневно в 12:00 дня', dict(freq='daily', interval=1, byhour='12', byminute='0')),

    ('daily at 12p', dict(freq='daily', interval=1, byhour='12', byminute='0'), 'daily at 12pm'),
    ('ежедневно в 12 дня', dict(freq='daily', interval=1, byhour='12', byminute='0'), 'daily at 12pm'),

    ('daily at 3pm', dict(freq='daily', interval=1, byhour='15', byminute='0')),
    ('ежедневно в 15:00', dict(freq='daily', interval=1, byhour='15', byminute='0')),

    ('daily at 3 pm', dict(freq='daily', interval=1, byhour='15', byminute='0'), 'daily at 3pm'),
    ('ежедневно в 3 дня', dict(freq='daily', interval=1, byhour='15', byminute='0'), 'daily at 3pm'),

    ('daily at 3p', dict(freq='daily', interval=1, byhour='15', byminute='0'), 'daily at 3pm'),
    ('ежедневно в 3p.m.', dict(freq='daily', interval=1, byhour='15', byminute='0'), 'daily at 3pm'),

    ('daily at 3:00pm', dict(freq='daily', interval=1, byhour='15', byminute='0'), 'daily at 3pm'),
    ('ежедневно в 15:00', dict(freq='daily', interval=1, byhour='15', byminute='0'), 'daily at 3pm'),

    ('daily at 3:01pm', dict(freq='daily', interval=1, byhour='15', byminute='1')),
    ('ежедневно в 15:01', dict(freq='daily', interval=1, byhour='15', byminute='1')),

    ('at 10 am on 15th of every month', dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'), '15th of every month at 10am'),
    ('15-го числа каждого месяца в 10 утра', dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'), '15th of every month at 10am'),

    ('every other saturdays through tuesdays', dict(freq='weekly', interval=2, byday='MO,TU,SA,SU'), 'every other week on Mon and Tue and weekend'),
    ('через неделю с субботы по вторник', dict(freq='weekly', interval=2, byday='MO,TU,SA,SU'), 'every other week on Mon and Tue and weekend'),

    ('each week on saturday thru tuesday', dict(freq='weekly', interval=1, byday='SA,SU,MO,TU'), 'every weekend and Mon and Tue'),
    ('каждую неделю с субботы по вторник', dict(freq='weekly', interval=1, byday='SA,SU,MO,TU'), 'every weekend and Mon and Tue'),

    ('each week on tuesday-saturday', dict(freq='weekly', interval=1, byday='TU,WE,TH,FR,SA'), 'every Tue and Wed and Thu and Fri and Sat'),
    ('каждую неделю со вторника по субботу', dict(freq='weekly', interval=1, byday='TU,WE,TH,FR,SA'), 'every Tue and Wed and Thu and Fri and Sat'),

    ('each week on tuesday-tue', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),
    ('каждую неделю по вторникам', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),

    ('tuesdays-tue', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),
    ('по вторникам', dict(freq='weekly', interval=1, byday='TU'), 'every Tue'),

    ('saturdays through tuesdays', dict(freq='weekly', interval=1, byday='MO,TU,SA,SU'), 'every Mon and Tue and weekend'),
    ('с субботы по вторник', dict(freq='weekly', interval=1, byday='MO,TU,SA,SU'), 'every Mon and Tue and weekend'),

    ('every thursday for the next three weeks', dict(freq='weekly', interval=1, byday='TH', until='%d0122' % NOW.year), 'every Thu until Fri Jan 22, 2010'),
    ('каждый четверг в течение следующих трёх недель', dict(freq='weekly', interval=1, byday='TH', until='%d0122' % NOW.year), 'every Thu until Fri Jan 22, 2010'),

    ('every mon and fri for the next month', dict(freq='weekly', interval=1, byday='MO,FR', until='%d0201' % NOW.year), 'every Mon and Fri until Mon Feb 1, 2010'),
    ('каждый понедельник и пятницу в течение следующего месяца', dict(freq='weekly', interval=1, byday='MO,FR', until='%d0201' % NOW.year), 'every Mon and Fri until Mon Feb 1, 2010'),

    ('every sat for 2 months', dict(freq='weekly', interval=1, byday='SA', until='%d0301' % NOW.year), 'every Sat until Mon Mar 1, 2010'),
    ('каждую субботу в течение 2 месяцев', dict(freq='weekly', interval=1, byday='SA', until='%d0301' % NOW.year), 'every Sat until Mon Mar 1, 2010'),

    ('every sat for up to 2 months', dict(freq='weekly', interval=1, byday='SA', until='%d0301' % NOW.year), 'every Sat until Mon Mar 1, 2010'),
    ('по субботам до 2 месяцев', dict(freq='weekly', interval=1, byday='SA', until='%d0301' % NOW.year), 'every Sat until Mon Mar 1, 2010'),

    ('every other sat for up to 14 months', dict(freq='weekly', interval=2, byday='SA', until='%d0301' % (NOW.year + 1)), 'every other week on Sat until Tue Mar 1, 2011'),
    ('через неделю по субботам в течение 14 месяцев', dict(freq='weekly', interval=2, byday='SA', until='%d0301' % (NOW.year + 1)), 'every other week on Sat until Tue Mar 1, 2011'),

    ('every other fri for the next year', dict(freq='weekly', interval=2, byday='FR', until='%d0101' % (NOW.year + 1)), 'every other week on Fri until Sat Jan 1, 2011'),
    ('через неделю по пятницам в течение следующего года', dict(freq='weekly', interval=2, byday='FR', until='%d0101' % (NOW.year + 1)), 'every other week on Fri until Sat Jan 1, 2011'),

    ('every 5th fri for the next 3 years', dict(freq='weekly', interval=5, byday='FR', until='%d0101' % (NOW.year + 3)), 'every 5 weeks on Fri until Tue Jan 1, 2013'),
    ('каждую 5-ю пятницу в течение 3 лет', dict(freq='weekly', interval=5, byday='FR', until='%d0101' % (NOW.year + 3)), 'every 5 weeks on Fri until Tue Jan 1, 2013'),

    # non-recurring
    ('march 3rd', datetime.datetime(NOW.year, 3, 3).date(), 'Wed Mar 3, 2010'),
    ('3 марта', datetime.datetime(NOW.year, 3, 3).date(), 'Wed Mar 3, 2010'),

    ('mar 2 2012', datetime.datetime(2012, 3, 2).date(), 'Fri Mar 2, 2012'),
    ('2 марта 2012', datetime.datetime(2012, 3, 2).date(), 'Fri Mar 2, 2012'),

    ('this sunday', (NOW + datetime.timedelta(days=(6 - NOW.weekday()) % 7)).date(), 'Sun Jan 3, 2010 9am'),
    ('в это воскресенье', (NOW + datetime.timedelta(days=(6 - NOW.weekday()) % 7)).date(), 'Sun Jan 3, 2010 9am'),

    ('thursday, february 18th', datetime.datetime(NOW.year, 2, 18).date(), 'Thu Feb 18, 2010'),
    ('четверг, 18 февраля', datetime.datetime(NOW.year, 2, 18).date(), 'Thu Feb 18, 2010'),

    ('2nd of feb', datetime.datetime(NOW.year, 2, 2), 'Tue Feb 2, 2010'),
    ('2 февраля', datetime.datetime(NOW.year, 2, 2), 'Tue Feb 2, 2010'),

    ('2nd fri in feb', datetime.datetime(NOW.year, 2, 12), 'Fri Feb 12, 2010'),
    ('вторая пятница февраля', datetime.datetime(NOW.year, 2, 12), 'Fri Feb 12, 2010'),

    ('last fri in feb', datetime.datetime(NOW.year, 2, 26), 'Fri Feb 26, 2010'),
    ('последняя пятница февраля', datetime.datetime(NOW.year, 2, 26), 'Fri Feb 26, 2010'),

    ('2nd to last fri in feb', datetime.datetime(NOW.year, 2, 19), 'Fri Feb 19, 2010'),
    ('вторая с конца пятница февраля', datetime.datetime(NOW.year, 2, 19), 'Fri Feb 19, 2010'),

    ('2nd fri of feb 2010', datetime.datetime(2010, 2, 12), 'Fri Feb 12, 2010'),
    ('вторая пятница февраля 2010', datetime.datetime(2010, 2, 12), 'Fri Feb 12, 2010'),

    ('1st fri in feb 2011', datetime.datetime(2011, 2, 4), 'Fri Feb 4, 2011'),
    ('первая пятница февраля 2011', datetime.datetime(2011, 2, 4), 'Fri Feb 4, 2011'),

    ('35th day', datetime.datetime(2010, 2, 4), 'Thu Feb 4, 2010'),
    ('35-й день', datetime.datetime(2010, 2, 4), 'Thu Feb 4, 2010'),

    ('35th day in 2010', datetime.datetime(2010, 2, 4), 'Thu Feb 4, 2010'),
    ('35-й день 2010 года', datetime.datetime(2010, 2, 4), 'Thu Feb 4, 2010'),

    ('36th day of 2011', datetime.datetime(2011, 2, 5), 'Sat Feb 5, 2011'),
    ('36-й день 2011 года', datetime.datetime(2011, 2, 5), 'Sat Feb 5, 2011'),

    # From the documentation:
    ("next tuesday", datetime.date(NOW.year, 1, 5), 'Tue Jan 5, 2010 9am'),
    ("в следующий вторник", datetime.date(NOW.year, 1, 5), 'Tue Jan 5, 2010 9am'),

    ('tomorrow', datetime.date(NOW.year, NOW.month, NOW.day + 1), 'Sat Jan 2, 2010 9am'),
    ('завтра', datetime.date(NOW.year, NOW.month, NOW.day + 1), 'Sat Jan 2, 2010 9am'),

    ("in an hour", NOW + datetime.timedelta(hours=1), 'Fri Jan 1, 2010 1am'),
    ("через час", NOW + datetime.timedelta(hours=1), 'Fri Jan 1, 2010 1am'),

    ("in 15 mins", NOW + datetime.timedelta(minutes=15), 'Fri Jan 1, 2010 12:15am'),
    ("через 15 минут", NOW + datetime.timedelta(minutes=15), 'Fri Jan 1, 2010 12:15am'),

    ("Mar 4th at 9am", datetime.datetime(NOW.year, 3, 4, 9), 'Thu Mar 4, 2010 9am'),
    ("4 марта в 9 утра", datetime.datetime(NOW.year, 3, 4, 9), 'Thu Mar 4, 2010 9am'),

    ("3rd Thu in Apr at 10 o'clock", datetime.datetime(NOW.year, 4, 15, 10), 'Thu Apr 15, 2010 10am'),
    ("третья четверг апреля в 10 часов", datetime.datetime(NOW.year, 4, 15, 10), 'Thu Apr 15, 2010 10am'),

    ("40th day of 2020", datetime.date(2020, 2, 9), 'Sun Feb 9, 2020'),
    ("40-й день 2020 года", datetime.date(2020, 2, 9), 'Sun Feb 9, 2020'),

    ("on weekdays", dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR'), 'weekdays'),
    ("по будням", dict(freq='weekly', interval=1, byday='MO,TU,WE,TH,FR'), 'weekdays'),

    ("every fourth of the month from jan 1 2010 to dec 25th 2020",
     dict(dtstart='20100101', interval=1, freq='monthly', bymonthday='4', until='20201225'),
     '4th of every month until Fri Dec 25, 2020'),
    ("каждое 4-е число месяца с 1 января 2010 до 25 декабря 2020",
     dict(dtstart='20100101', interval=1, freq='monthly', bymonthday='4', until='20201225'),
     '4th of every month until Fri Dec 25, 2020'),

    ("each thurs until next month",
     dict(freq='weekly', interval=1, byday='TH', until='%d0201' % NOW.year),
     'every Thu until Mon Feb 1, 2010'),
    ("каждый четверг до следующего месяца",
     dict(freq='weekly', interval=1, byday='TH', until='%d0201' % NOW.year),
     'every Thu until Mon Feb 1, 2010'),

    ("once a year on the fourth thursday in november",
     dict(freq='yearly', interval=1, bymonth='11', byday='4TH'),
     'every 4th Thu in Nov'),
    ("раз в год в четвёртый четверг ноября",
     dict(freq='yearly', interval=1, bymonth='11', byday='4TH'),
     'every 4th Thu in Nov'),

    ("tuesdays and thursdays at 3:15",
     dict(freq='weekly', interval=1, byday='TU,TH', byhour='15', byminute='15'),
     'every Tue and Thu at 3:15pm'),
    ("по вторникам и четвергам в 15:15",
     dict(freq='weekly', interval=1, byday='TU,TH', byhour='15', byminute='15'),
     'every Tue and Thu at 3:15pm'),

    ("wednesdays at 9 o'clock",
     dict(freq='weekly', interval=1, byday='WE', byhour='9', byminute='0'),
     'every Wed at 9am'),
    ("по средам в 9 часов",
     dict(freq='weekly', interval=1, byday='WE', byhour='9', byminute='0'),
     'every Wed at 9am'),

    ("fridays at 11am",
     dict(freq='weekly', interval=1, byday='FR', byhour='11', byminute='0'),
     'every Fri at 11am'),
    ("по пятницам в 11 утра",
     dict(freq='weekly', interval=1, byday='FR', byhour='11', byminute='0'),
     'every Fri at 11am'),

    ("daily except in June",
     dict(freq='daily', interval=1, exdate=[[6, NOW.year]]),
     'daily except in Jun'),
    ("ежедневно, кроме июня",
     dict(freq='daily', interval=1, exdate=[[6, NOW.year]]),
     'daily except in Jun'),

    ("daily except on June 23rd and July 4th",
     dict(freq='daily', interval=1, exdate=[
         datetime.date(NOW.year, 6, 23),
         datetime.date(NOW.year, 7, 4)]),
     'daily except on Wed Jun 23, 2010 and Sun Jul 4, 2010'),
    ("ежедневно, кроме 23 июня и 4 июля",
     dict(freq='daily', interval=1, exdate=[
         datetime.date(NOW.year, 6, 23),
         datetime.date(NOW.year, 7, 4)]),
     'daily except on Wed Jun 23, 2010 and Sun Jul 4, 2010'),

    ("every monday except for the 2nd monday in March",
     dict(freq='weekly', interval=1, byday='MO', exdate=[datetime.date(2010, 3, 8)]),
     'every Mon except on Mon Mar 8, 2010'),
    ("каждый понедельник, кроме второго понедельника марта",
     dict(freq='weekly', interval=1, byday='MO', exdate=[datetime.date(2010, 3, 8)]),
     'every Mon except on Mon Mar 8, 2010'),

    ("every monday except each 2nd monday in March",
     dict(freq='weekly', interval=1, byday='MO', exrule='BYDAY=2MO;BYMONTH=3;INTERVAL=1;FREQ=YEARLY'),
     'every Mon except every 2nd Mon in Mar'),
    ("каждый понедельник, кроме каждого второго понедельника марта",
     dict(freq='weekly', interval=1, byday='MO', exrule='BYDAY=2MO;BYMONTH=3;INTERVAL=1;FREQ=YEARLY'),
     'every Mon except every 2nd Mon in Mar'),

    ("fridays twice", dict(freq='weekly', interval=1, byday='FR', count=2), 'every Fri twice'),
    ("по пятницам дважды", dict(freq='weekly', interval=1, byday='FR', count=2), 'every Fri twice'),

    ("fridays 3x", dict(freq='weekly', interval=1, byday='FR', count=3), 'every Fri for 3 times'),
    ("по пятницам 3 раза", dict(freq='weekly', interval=1, byday='FR', count=3), 'every Fri for 3 times'),

    ("every other friday for 5 times", dict(freq='weekly', interval=2, byday='FR', count=5), 'every other week on Fri for 5 times'),
    ("через неделю по пятницам 5 раз", dict(freq='weekly', interval=2, byday='FR', count=5), 'every other week on Fri for 5 times'),

    ("every 3 fridays from november until february",
     dict(freq='weekly', interval=3, dtstart='%d1101' % NOW.year, byday='FR', until='%d0201' % (NOW.year + 1)),
     'every 3 weeks on Fri from Mon Nov 1, 2010 to Tue Feb 1, 2011'),
    ("каждые 3 пятницы с ноября по февраль",
     dict(freq='weekly', interval=3, dtstart='%d1101' % NOW.year, byday='FR', until='%d0201' % (NOW.year + 1)),
     'every 3 weeks on Fri from Mon Nov 1, 2010 to Tue Feb 1, 2011'),

    ("fridays starting in may for 10 occurrences",
     dict(freq='weekly', interval=1, dtstart='%d0501' % NOW.year, byday='FR', count=10),
     'every Fri starting Sat May 1, 2010 for 10 times'),
    ("по пятницам начиная с мая 10 раз",
     dict(freq='weekly', interval=1, dtstart='%d0501' % NOW.year, byday='FR', count=10),
     'every Fri starting Sat May 1, 2010 for 10 times'),

    ("tuesdays for the next six weeks",
     dict(freq='weekly', interval=1, byday='TU', until='%d0212' % NOW.year),
     'every Tue until Fri Feb 12, 2010'),
    ("по вторникам в течение следующих шести недель",
     dict(freq='weekly', interval=1, byday='TU', until='%d0212' % NOW.year),
     'every Tue until Fri Feb 12, 2010'),

    ("every Mon-Wed for the next 2 months",
     dict(freq='weekly', interval=1, byday='MO,TU,WE', until='%d0301' % NOW.year),
     'every Mon and Tue and Wed until Mon Mar 1, 2010'),
    ("с понедельника по среду в течение 2 месяцев",
     dict(freq='weekly', interval=1, byday='MO,TU,WE', until='%d0301' % NOW.year),
     'every Mon and Tue and Wed until Mon Mar 1, 2010'),

    ("every Mon thru Wed for the next year",
     dict(freq='weekly', interval=1, byday='MO,TU,WE', until='%d0101' % (NOW.year + 1)),
     'every Mon and Tue and Wed until Sat Jan 1, 2011'),
    ("с понедельника по среду в течение года",
     dict(freq='weekly', interval=1, byday='MO,TU,WE', until='%d0101' % (NOW.year + 1)),
     'every Mon and Tue and Wed until Sat Jan 1, 2011'),

    ("every other Fri for the next three years",
     dict(freq='weekly', interval=2, byday='FR', until='%d0101' % (NOW.year + 3)),
     'every other week on Fri until Tue Jan 1, 2013'),
    ("через неделю по пятницам в течение трёх лет",
     dict(freq='weekly', interval=2, byday='FR', until='%d0101' % (NOW.year + 3)),
     'every other week on Fri until Tue Jan 1, 2013'),

    ('monthly on the first and last instance of wed and fri',
     dict(freq='monthly', interval=1, byday='WE,FR', bysetpos='1,-1'),
     'for the 1st and last instance of Wed and Fri of every month'),
    ('ежемесячно в первую и последнюю среду и пятницу',
     dict(freq='monthly', interval=1, byday='WE,FR', bysetpos='1,-1'),
     'for the 1st and last instance of Wed and Fri of every month'),

    ('every Tue and Fri in week 14',
     dict(freq='yearly', interval=1, byday='TU,FR', byweekno='14'),
     'every Tue and Fri in week 14'),
    ('каждый вторник и пятницу в 14-й неделе',
     dict(freq='yearly', interval=1, byday='TU,FR', byweekno='14'),
     'every Tue and Fri in week 14'),

    ("every year on Dec 25",
     dict(freq='yearly', interval=1, bymonth='12', bymonthday='25'),
     'every Dec 25th'),
    ("каждый год 25 декабря",
     dict(freq='yearly', interval=1, bymonth='12', bymonthday='25'),
     'every Dec 25th'),
    # TODO:
    # every monday except on holidays
    # every friday except on good friday
    # every holiday
    # every easter
    # every first Tuesday after the first Monday in November
    # every first business day of the month
    # every last business day of the month
    # every business day
    # every day except on weekends and holidays

]

time_expressions = [
    ('march 3rd at 12:15am', datetime.datetime(NOW.year, 3, 3, 0, 15), 'Wed Mar 3, 2010 12:15am'),
    ('3 марта в 00:15', datetime.datetime(NOW.year, 3, 3, 0, 15), 'Wed Mar 3, 2010 12:15am'),

    ('8/1/2100 at 12:15am', datetime.datetime(2100, 8, 1, 0, 15), 'Sun Aug 1, 2100 12:15am'),
    ('1 августа 2100 в 00:15', datetime.datetime(2100, 8, 1, 0, 15), 'Sun Aug 1, 2100 12:15am'),

    ('8/1/2100 at 1am', datetime.datetime(2100, 8, 1, 1, 0), 'Sun Aug 1, 2100 1am'),
    ('1 августа 2100 в 1:00 утра', datetime.datetime(2100, 8, 1, 1, 0), 'Sun Aug 1, 2100 1am'),

    ('8/1/2100 at 1:01', datetime.datetime(2100, 8, 1, 13, 1), 'Sun Aug 1, 2100 1:01pm'),
    ('1 августа 2100 в 13:01', datetime.datetime(2100, 8, 1, 13, 1), 'Sun Aug 1, 2100 1:01pm'),

    ('8/1/2100 at 1:02am', datetime.datetime(2100, 8, 1, 1, 2), 'Sun Aug 1, 2100 1:02am'),
    ('1 августа 2100 в 1:02 утра', datetime.datetime(2100, 8, 1, 1, 2), 'Sun Aug 1, 2100 1:02am'),

    ('8/1/2100 at 12pm', datetime.datetime(2100, 8, 1, 12, 0), 'Sun Aug 1, 2100 12pm'),
    ('1 августа 2100 в 12 дня', datetime.datetime(2100, 8, 1, 12, 0), 'Sun Aug 1, 2100 12pm'),

    ('8/1/2100 at 12p', datetime.datetime(2100, 8, 1, 12, 0), 'Sun Aug 1, 2100 12pm'),
    ('1 августа 2100 в 12p.m.', datetime.datetime(2100, 8, 1, 12, 0), 'Sun Aug 1, 2100 12pm'),

    ('8/1/2100 at 1 pm', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),
    ('1 августа 2100 в 13:00', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),

    ('at 1 pm on 8/1/2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),
    ('в 13:00 1 августа 2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),

    ('1pm on 8/1/2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),
    ('1p.m. 1 августа 2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),

    ('1 pm on 8/1/2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),
    ('13:00 1 августа 2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),

    ('8/1/2100 at 1:01pm', datetime.datetime(2100, 8, 1, 13, 1), 'Sun Aug 1, 2100 1:01pm'),
    ('1 августа 2100 в 13:01', datetime.datetime(2100, 8, 1, 13, 1), 'Sun Aug 1, 2100 1:01pm'),

    ('8/1/2100 at 2:01pm', datetime.datetime(2100, 8, 1, 14, 1), 'Sun Aug 1, 2100 2:01pm'),
    ('1 августа 2100 в 14:01', datetime.datetime(2100, 8, 1, 14, 1), 'Sun Aug 1, 2100 2:01pm'),

    ('8/1/2100 2:01pm', datetime.datetime(2100, 8, 1, 14, 1), 'Sun Aug 1, 2100 2:01pm'),
    ('1 августа 2100 в 14:01', datetime.datetime(2100, 8, 1, 14, 1), 'Sun Aug 1, 2100 2:01pm'),

    ('tomorrow at 3:30', datetime.datetime(NOW.year, NOW.month, NOW.day + 1, 15, 30), 'Sat Jan 2, 2010 3:30pm'),
    ('завтра в 15:30', datetime.datetime(NOW.year, NOW.month, NOW.day + 1, 15, 30), 'Sat Jan 2, 2010 3:30pm'),

    ('in 30 minutes', NOW.replace(minute=NOW.minute + 30), 'Fri Jan 1, 2010 12:30am'),
    ('через 30 минут', NOW.replace(minute=NOW.minute + 30), 'Fri Jan 1, 2010 12:30am'),

    ('at 4', NOW.replace(hour=16), 'Fri Jan 1, 2010 4pm'),
    ('в 4 часа', NOW.replace(hour=16), 'Fri Jan 1, 2010 4pm'),

    ('2 hours from now', NOW.replace(hour=NOW.hour + 2), 'Fri Jan 1, 2010 2am'),
    ('через 2 часа', NOW.replace(hour=NOW.hour + 2), 'Fri Jan 1, 2010 2am'),

    ('sunday at 2', (NOW + datetime.timedelta(days=(6 - NOW.weekday()) % 7)).replace(hour=14), 'Sun Jan 3, 2010 2pm'),
    ('в воскресенье в 14:00', (NOW + datetime.timedelta(days=(6 - NOW.weekday()) % 7)).replace(hour=14), 'Sun Jan 3, 2010 2pm'),

    ('at 9am on the 2nd fri in feb', datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),
    ('в 9 утра во вторую пятницу февраля', datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),

    ("2nd fri in feb at 9", datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),
    ("вторая пятница февраля в 9", datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),

    ("2nd fri in feb at 9am", datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),
    ("вторая пятница февраля в 9 утра", datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),

    ("2nd fri in feb at 9 o'clock", datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),
    ("вторая пятница февраля в 9 часов", datetime.datetime(NOW.year, 2, 12, 9), 'Fri Feb 12, 2010 9am'),

    ('1st fri in feb 2011 at 2pm', datetime.datetime(2011, 2, 4, 14), 'Fri Feb 4, 2011 2pm'),
    ('первая пятница февраля 2011 в 14:00', datetime.datetime(2011, 2, 4, 14), 'Fri Feb 4, 2011 2pm'),
]
expressions += time_expressions

ambiguous_expressions = (
    ('weekly', dict(interval=1, freq='weekly'), None),
    ('еженедельно', dict(interval=1, freq='weekly'), None),

    ('twice weekly', None, None),
    ('дважды в неделю', None, None),

    # Sometimes passes, sometimes fails depending on if other words are passed in:
    # ('three times a week', ExpectedFailure(None), None),
    # ('три раза в неделю', ExpectedFailure(None), None),

    ('monthly', dict(interval=1, freq='monthly'), None),
    ('ежемесячно', dict(interval=1, freq='monthly'), None),

    ('once a month', ExpectedFailure(None), None),
    ('раз в месяц', ExpectedFailure(None), None),

    ('yearly', dict(interval=1, freq='yearly'), None),
    ('ежегодно', dict(interval=1, freq='yearly'), None),
)

expressions += ambiguous_expressions

non_dt_expressions = (
    ('Once in a while.', None, None),
    ('Время от времени.', None, None),

    ('Every time i hear that i apreciate it.', None, None),
    ('Каждый раз, когда я это слышу, я ценю это.', None, None),

    ('Once every ones in', None, None),
    ('Один раз среди всех', None, None),

    # 'wait a minute' is properly parsed
    # ('first time for everything. wait a minute', None),
    # ('всему своё время. подожди минутку.', None),

    ('may this test pass.', ExpectedFailure(None), None),
    ('пусть этот тест пройдёт.', ExpectedFailure(None), None),

    ('seconds anyone?', None, None),
    ('секунды, кто-нибудь?', None, None),

    ('from september to november', None, None),
    ('с сентября по ноябрь', None, None),

    ('except for tomorrow', None, None),
    ('кроме завтра', None, None),

    ('starting 3/1', ExpectedFailure(None), None),
    ('начиная с 1 марта', ExpectedFailure(None), None),

    ('for 3x', None, None),
    ('на 3 раза', None, None),

    ('starting 3/1 twice', ExpectedFailure(None), None),
    ('начиная с 1 марта дважды', ExpectedFailure(None), None),

    ('starting 3/1 for 3 times', ExpectedFailure(None), None),
    ('начиная с 1 марта 3 раза', ExpectedFailure(None), None),

    ('Mar 99th', ExpectedFailure(None), None),
    ('99 марта', ExpectedFailure(None), None),

    ('Mar 9th at 28pm', ExpectedFailure(None), None),
    ('9 марта в 28:00', ExpectedFailure(None), None),

    ('Mar 9th at 10:99', ExpectedFailure(None), None),
    ('9 марта в 10:99', ExpectedFailure(None), None),

    ('2nd and 4th Thu of Aug', ExpectedFailure(None), None),
    ('второй и четвёртый четверг августа', ExpectedFailure(None), None),

    ('2nd and 4th of Aug', ExpectedFailure(None), None),
    ('второе и четвёртое августа', ExpectedFailure(None), None),

    ('2nd and 4th day of 2010', ExpectedFailure(None), None),
    ('2-й и 4-й день 2010 года', ExpectedFailure(None), None),

    ('2nd week day of 2010', ExpectedFailure(None), None),
    ('2-й будний день 2010 года', ExpectedFailure(None), None),

    ('2nd week of 2010', ExpectedFailure(None), None),
    ('2-я неделя 2010 года', ExpectedFailure(None), None),

    ('2nd week', datetime.datetime(NOW.year, 1, 4), 'Mon Jan 4, 2010'),
    ('2-я неделя', datetime.datetime(NOW.year, 1, 4), 'Mon Jan 4, 2010'),

    ('2nd month', datetime.datetime(NOW.year, 1, 2), 'Sat Jan 2, 2010'),
    ('2-й месяц', datetime.datetime(NOW.year, 1, 2), 'Sat Jan 2, 2010'),

    ('2nd month of 2010', ExpectedFailure(None), None),
    ('2-й месяц 2010 года', ExpectedFailure(None), None),

    ('3rd day Aug', ExpectedFailure(None), None),
    ('3-й день августа', ExpectedFailure(None), None),

    ('4th year month Mar week', ExpectedFailure(None), None),
    ('4-й год месяц март неделя', ExpectedFailure(None), None),

    ('2nd year month instance', None, None),
    ('2-й год месяц экземпляр', None, None),

    ('', None, None),
)

extra_expressions = (  # We test these exactly, not in phrases
    ('1 oclock on 8/1/2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),
    ('1 час 1 августа 2100', datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),

    ("1 o'clock on 8/1/2100", datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),
    ("1 час дня 1 августа 2100", datetime.datetime(2100, 8, 1, 13, 0), 'Sun Aug 1, 2100 1pm'),

    ('10:00 on the 15th of every month',
     dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'),
     '15th of every month at 10am'),
    ('10:00 15-го числа каждого месяца',
     dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'),
     '15th of every month at 10am'),

    ('10am on the 15th of every month',
     dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'),
     '15th of every month at 10am'),
    ('10 утра 15-го числа каждого месяца',
     dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'),
     '15th of every month at 10am'),

    ('10 am on the 15th of every month',
     dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'),
     '15th of every month at 10am'),
    ('10 a.m. 15-го числа каждого месяца',
     dict(freq='monthly', interval=1, byhour='10', byminute='0', bymonthday='15'),
     '15th of every month at 10am'),
)


def fixup_default(*args):
    if len(args) == 3:
        return (args[0], args[2], args[1])
    else:
        return (args[0], *args[2:])


embedded_expressions = [fixup_default('im available ' + s, s, *v) for s, *v in expressions] + [
    fixup_default(s + ' would work best for me', s, *v) for s, *v in expressions] + [
                           fixup_default('remind me to move car ' + s + ' would work best for me', s, *v) for s, *v in expressions]

expressions += embedded_expressions
expressions += non_dt_expressions
expressions += extra_expressions  # Issue #13


class ParseTest(unittest.TestCase):

    def test_return_recurring(self):
        string = 'every day'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, str))

    def test_return_non_recurring(self):
        string = 'march 3rd, 2001'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_recurring2(self):
        string = 'next wednesday'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_date(self):
        string = 'remember to call mitchell'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertIs(ret, None)

    def test_rrule_string(self):
        string = 'every day starting feb 2'
        date = RecurringEvent(NOW)
        date.parse(string)
        expected1 = """DTSTART:20100202\nRRULE:FREQ=DAILY;INTERVAL=1"""
        expected2 = """DTSTART:20100202\nRRULE:INTERVAL=1;FREQ=DAILY"""
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_date_incrementer(self):
        date = RecurringEvent(datetime.date(2012, 2, 29))  # Leap year
        string = 'daily for the next year'
        date.parse(string)
        expected1 = """RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20130301"""
        expected2 = """RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20130301"""
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])
        string = 'daily for the next 12 months'
        date.parse(string)
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_until_wrap(self):
        date = RecurringEvent(datetime.date(2010, 11, 1))
        string = 'daily until Feb'
        date.parse(string)
        expected1 = """RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20110201"""
        expected2 = """RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20110201"""
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_format_errors(self):
        date = RecurringEvent()
        self.assertIs(date.format(None), None)
        self.assertEqual(date.format(''), '')
        self.assertEqual(date.format('abc'), 'abc')  # No RRULE
        self.assertEqual(date.format('RRULE:INTERVAL=1'), 'RRULE:INTERVAL=1')  # No FREQ
        self.assertEqual(date.format('RRULE:FREQ=WEEKLY'), 'RRULE:FREQ=WEEKLY')  # No BYDAY
        self.assertEqual(date.format('RRULE:FREQ=WEEKLY;BYDAY=XX'), 'RRULE:FREQ=WEEKLY;BYDAY=XX')  # Bad BYDAY
        self.assertEqual(date.format('RRULE:FREQ=MONTHLY'), 'RRULE:FREQ=MONTHLY')  # No BYMONTHDAY or BYDAY
        self.assertEqual(date.format('RRULE:FREQ=YEARLY'), 'RRULE:FREQ=YEARLY')  # No BYMONTHDAY or BYDAY or BYMONTH
        self.assertEqual(date.format('RRULE:FREQ=BADLY'), 'RRULE:FREQ=BADLY')

    def test_format_plus(self):
        date = RecurringEvent()
        self.assertEqual(date.format('RRULE:INTERVAL=1;FREQ=MONTHLY;BYDAY=+1FR'), '1st Fri of every month')
        self.assertEqual(date.format(datetime.datetime(2000, 1, 2, 3, 4, 5)), 'Sun Jan 2, 2000 3:04:05am')

    def test_high_level(self):
        self.assertEqual(rformat(rparse('daily')), 'daily')

    def test_return_recurring_ru(self):
        string = 'ежедневно'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, str))

    def test_return_non_recurring_ru(self):
        string = '3 марта 2001'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_recurring_ru2(self):
        string = 'в следующую среду'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_date_ru(self):
        string = 'позвони митчеллу'
        date = RecurringEvent()
        ret = date.parse(string)
        self.assertIs(ret, None)

    def test_rrule_string_ru(self):
        string = 'ежедневно начиная с 2 февраля'
        date = RecurringEvent(NOW)
        date.parse(string)
        expected1 = "DTSTART:20100202\nRRULE:FREQ=DAILY;INTERVAL=1"
        expected2 = "DTSTART:20100202\nRRULE:INTERVAL=1;FREQ=DAILY"
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_date_incrementer_ru(self):
        date = RecurringEvent(datetime.date(2012, 2, 29))  # Leap year
        string = 'ежедневно в течение следующего года'
        date.parse(string)
        expected1 = "RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20130301"
        expected2 = "RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20130301"
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])
        string = 'ежедневно в течение следующих 12 месяцев'
        date.parse(string)
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_until_wrap_ru(self):
        date = RecurringEvent(datetime.date(2010, 11, 1))
        string = 'ежедневно до февраля'
        date.parse(string)
        expected1 = "RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20110201"
        expected2 = "RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20110201"
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_format_errors_ru(self):
        date = RecurringEvent()
        self.assertIs(date.format(None), None)
        self.assertEqual(date.format(''), '')
        self.assertEqual(date.format('abc'), 'abc')
        self.assertEqual(date.format('RRULE:INTERVAL=1'), 'RRULE:INTERVAL=1')
        self.assertEqual(date.format('RRULE:FREQ=WEEKLY'), 'RRULE:FREQ=WEEKLY')
        self.assertEqual(date.format('RRULE:FREQ=WEEKLY;BYDAY=XX'), 'RRULE:FREQ=WEEKLY;BYDAY=XX')
        self.assertEqual(date.format('RRULE:FREQ=MONTHLY'), 'RRULE:FREQ=MONTHLY')
        self.assertEqual(date.format('RRULE:FREQ=YEARLY'), 'RRULE:FREQ=YEARLY')
        self.assertEqual(date.format('RRULE:FREQ=BADLY'), 'RRULE:FREQ=BADLY')

    def test_format_plus_ru(self):
        date = RecurringEvent()
        self.assertEqual(date.format('RRULE:INTERVAL=1;FREQ=MONTHLY;BYDAY=+1FR'), '1st Fri of every month')
        self.assertEqual(date.format(datetime.datetime(2000, 1, 2, 3, 4, 5)), 'Sun Jan 2, 2000 3:04:05am')

    def test_high_level_ru(self):
        self.assertEqual(rformat(rparse('ежедневно')), 'daily')


def tst_expression(string, expected, de):
    tr = WordByWordTranslator()
    def test_(self):
        date = RecurringEvent(NOW)
        ru_str = tr.translate_text(string)
        val = date.parse(string)
        back_again = date.format(val)
        expected_params = expected
        known_failure = False

        if isinstance(expected, ExpectedFailure):
            known_failure = True
            expected_params = expected.correct_value

        try:
            if expected_params is None:
                self.assertTrue(
                    val is None or list(date.get_params().keys()) == ['interval'],
                    f"❌ Non-date error:\n"
                    f"🔤 Original: '{string}'\n"
                    f"🌐 Translated: '{ru_str}'\n"
                    f"↪ Parsed to: {val}\n"
                    f"🆚 Expected: {expected_params}"
                )
            elif isinstance(expected_params, (datetime.datetime, datetime.date)):
                if isinstance(expected_params, datetime.datetime):
                    self.assertEqual(
                        val, expected_params,
                        f"❌ Date mismatch:\n"
                        f"🔤 Original: '{string}'\n"
                        f"🌐 Translated: '{ru_str}'\n"
                        f"🗓 Got: {val}\n"
                        f"🆚 Expected: {expected_params}"
                    )
                else:
                    self.assertEqual(
                        val.date(), expected_params,
                        f"❌ Date mismatch:\n"
                        f"🔤 Original: '{string}'\n"
                        f"🌐 Translated: '{ru_str}'\n"
                        f"🗓 Got: {val.date()}\n"
                        f"🆚 Expected: {expected_params}"
                    )
            else:
                actual_params = date.get_params()
                for k, v in expected_params.items():
                    av = actual_params.pop(k, None)
                    self.assertEqual(
                        av, v,
                        f"❌ Rule mismatch:\n"
                        f"🔤 Original: '{string}'\n"
                        f"🌐 Translated: '{ru_str}'\n"
                        f"🔑 Rule: {k}\n"
                        f"🆚 Expected: {v}\n"
                        f"📥 Got: {av}\n"
                        f"📋 All parsed: {date.get_params()}"
                    )
                for k, v in actual_params.items():
                    self.assertFalse(v)
                rrule.rrulestr(val)
        except AssertionError as e:
            if known_failure:
                print("✅ Expected failure (passed correctly):", expected_params)
                return
            raise e

        if known_failure:
            raise AssertionError("❗ Known failure unexpectedly passed:", expected_params, string)

        self.maxDiff = 1000
        if de is not None:
            translated_de = tr.translate_text(de)
            self.assertEqual(
                translated_de, back_again,
                f"❌ Final formatting mismatch:\n"
                f"🔤 Original: '{string}'\n"
                f"🌐 Translated: '{ru_str}'\n"
                f"📝 Expected format: '{translated_de}'\n"
                f"🛑 Got: '{back_again}'"
            )
            if back_again is not None and back_again != string:
                self.assertEqual(
                    back_again, date.format(date.parse(back_again)),
                    "Re-parsing the formatted result should be idempotent"
                )

    return test_


# add a test for each expression
for i, expr in enumerate(expressions):
    if len(expr) == 2:
        string, params = expr
        de = string
    else:
        string, params, de = expr
    setattr(ParseTest, 'test_%03d_%s' % (i, string.replace(' ', '_')), tst_expression(string, params, de))

if __name__ == '__main__':  # pragma nocover
    print("Dates relative to %s" % NOW)
    unittest.main(verbosity=2)
