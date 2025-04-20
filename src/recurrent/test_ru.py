import unittest
import datetime

from recurrent import RecurringEvent
from recurrent.recurrent_ru.ru_adapter import RecurringEventAuto

NOW = datetime.datetime(2010, 1, 1)


class ParseTestRu(unittest.TestCase):

    def test_return_recurring(self):
        string = 'каждый день'
        date = RecurringEventAuto()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, str))

    def test_return_non_recurring(self):
        string = '3 марта 2001'
        date = RecurringEventAuto()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_recurring2(self):
        string = 'следующая среда'
        date = RecurringEventAuto()
        ret = date.parse(string)
        self.assertTrue(isinstance(ret, datetime.datetime))

    def test_return_non_date(self):
        string = 'позвонить Мише'
        date = RecurringEventAuto()
        ret = date.parse(string)
        self.assertIs(ret, None)

    def test_rrule_string(self):
        string = 'начиная со 2 февраля, каждый день'
        # переведется как "Since February 2, every day",
        # но recurrent не обработает этот запрос, как бы хотелось
        date = RecurringEventAuto(NOW)
        date.parse(string)
        expected1 = """DTSTART:20100202\nRRULE:FREQ=DAILY;INTERVAL=1"""
        expected2 = """DTSTART:20100202\nRRULE:INTERVAL=1;FREQ=DAILY"""
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_date_incrementer(self):
        date = RecurringEventAuto(datetime.date(2012, 2, 29))  # високосный год
        string = 'ежедневно в течение следующего года'
        date.parse(string)
        expected1 = """RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20130301"""
        expected2 = """RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20130301"""
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_until_wrap(self):
        date = RecurringEventAuto(datetime.date(2010, 11, 1))
        # Но при этом "каждый день до февраля" работать не будет,
        # т.к. переведется как прост окаждый день
        string = 'каждый день до месяца февраля'
        date.parse(string)
        expected1 = """RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20110201"""
        expected2 = """RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20110201"""
        a = date.get_RFC_rrule()
        self.assertIn(date.get_RFC_rrule(), [expected1, expected2])

    def test_format_errors(self):
        date = RecurringEventAuto()
        self.assertIs(date.format(None), None)
        self.assertEqual(date.format(''), '')
        self.assertEqual(date.format('abc'), 'abc')
        self.assertEqual(date.format('RRULE:INTERVAL=1'), 'RRULE:INTERVAL=1')
        self.assertEqual(date.format('RRULE:FREQ=WEEKLY'), 'RRULE:FREQ=WEEKLY')
        self.assertEqual(date.format('RRULE:FREQ=WEEKLY;BYDAY=XX'),
                         'RRULE:FREQ=WEEKLY;BYDAY=XX')
        self.assertEqual(date.format('RRULE:FREQ=MONTHLY'),
                         'RRULE:FREQ=MONTHLY')
        self.assertEqual(date.format('RRULE:FREQ=YEARLY'), 'RRULE:FREQ=YEARLY')
        self.assertEqual(date.format('RRULE:FREQ=BADLY'), 'RRULE:FREQ=BADLY')

    def test_format_plus(self):
        date = RecurringEventAuto()
        self.assertEqual(
            date.format('RRULE:INTERVAL=1;FREQ=MONTHLY;BYDAY=+1FR'),
            '1st Fri of every month')
        self.assertEqual(date.format(datetime.datetime(2000, 1, 2, 3, 4, 5)),
                         'Sun Jan 2, 2000 3:04:05am')


if __name__ == '__main__':
    unittest.main(verbosity=2)
