from recurrent.event_parser import RecurringEvent
from recurrent.recurrent_ru.translator import is_ru, translate_ru_en


class RecurringEventAuto(RecurringEvent):
    def parse(self, s: str):
        if is_ru(s):
            s = translate_ru_en(s)
        return super().parse(s)

