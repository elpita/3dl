from kivy.properties import ObjectProperty, AliasProperty, ListProperty
from datetimewidgets import DatePicker
from kivy.lang import Builder
from uiux import Screen_
import datetime

class DatePickerMiniScreen(Screen_):
    item = ObjectProperty(None)
    datepicker = ObjectProperty(None)
    time = ObjectProperty(datetime.time(12, 00))

    def _get_when(self):
        datepicker = self.datepicker

        if datepicker.day:
            dt = datetime.datetime.combine(datepicker.date, self.time)
            return dt.isoformat()[:16]
        else:
            return ''

    def _set_when(self, when):
        if when:
            dt = datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M")
            self.datepicker.date = dt.date()
            self.time = dt.time()
        else:
            return False

    when = AliasProperty(_get_when, _set_when)

    def on_pre_enter(self, *args):
        if self.item.when:
            self.when = self.item.when
        else:
            #For the timing between sizing and populating days in calendar
            self.when = datetime.date.today() + 'T12:00'

Builder.load_string("""
#:import DatePicker datetimewidgets.DatePicker

<Foobuttons@Button_>:
    state_color: app.no_color
    text_color: app.blue

<DatePickerMiniScreen>:
    datepicker: datepicker_id
    name: 'DatePicker Mini-Screen'
    root_directory: app.db

    DatePicker:
        id: datepicker_id
        pos_hint: {'x': 0, 'top': 0.9648}
        size_hint: 1, 0.5
    BoxLayout:
        pos_hint: {'x': 0, 'y': 0}
        size_hint: 1, 0.0789

        Foobuttons:
            text: 'Cancel'
        Foobuttons:
            text: 'Today'
            on_press: datepicker_id.to_today()
        Foobuttons:
            text: 'Submit'

""")
