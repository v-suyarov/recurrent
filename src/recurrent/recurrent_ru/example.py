import datetime
from recurrent.recurrent_ru.ru_adapter import RecurringEventAuto

if __name__ == "__main__":
    r = RecurringEventAuto(now_date=datetime.datetime(2025, 1, 1))
    print(r.parse("4 марта в 9 утра"))
    # -> datetime.datetime(2025, 3, 4, 9, 0)
    print(r.parse("March 4th at 9am"))