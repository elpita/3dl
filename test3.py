from kivy.properties import ObjectProperty, ListProperty, NumericProperty, BooleanProperty, StringProperty, AliasProperty
from uiux import Selectable, Button_, DelayedClickable, FreeRotateLayout, Screen_
from customaccordion import AccordionListItem, AccordionListView
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.uix.widget import Widget
from datetimewidgets import Modal
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.app import App

import datetime, itertools, math
from kivy.modules import inspector
from kivy.core.window import Window

class Day(Selectable, Button_):
    week = ObjectProperty(None)
    in_month = BooleanProperty(True)

    def on_touch_down(self, touch):
        if self.disabled:
            return False
        else:
            return super(Day, self).on_touch_down(touch)

    def select(self, *args):
        week = self.week

        if not week.is_selected:
            week.is_selected = True

    def deselect(self, *args):
        week = self.week

        if week.is_selected:
            week.is_selected = False

class DayDropDown(DelayedClickable):
    day = StringProperty('')

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        else:
            return super(DayDropDown, self).on_touch_down(touch)

class Week(AccordionListItem):
    title_height = NumericProperty(0.0)
    content_height = NumericProperty(0.0)

class DatePicker(BoxLayout):
    year = NumericProperty(1)
    month = NumericProperty(1)
    day = NumericProperty(0)
    month_names = ListProperty(('January ', 'February ', 'March ', 'April ', 'May ', 'June ', 'July ', 'August ', 'September ', 'October ', 'November ', 'December '))

    def _get_date(self):
        if self.day:
            day = self.day
        else:
            day = 1

        return datetime.date(self.year, self.month, day)
    
    def _set_date(self, value, timedelta=datetime.timedelta, izip=itertools.izip, repeat=itertools.repeat, ravel=itertools.chain.from_iterable, today=datetime.date.today()):

        def _args_converter(date_cursor, delta):
            date_label = Day(text=str(date_cursor.day))

            if date_cursor < today:
                date_label.disabled = True
            elif ((delta < 0) or (value.month <> date_cursor.month)):
                date_label.in_month = False

            return date_label

        if len(self.body.cached_views) < 6:
            self.body.populate(0,6)
            l = lambda *_: self._set_date(value)
            Clock.schedule_once(l, 0)
            return False

        #self.title.text = self.month_names[value.month-1] + str(value.year)
        self.year, self.month = value.year, value.month
        date = datetime.date(value.year, value.month, 1)
        dt = date.isoweekday()# - instance.type_of_calendar
        cached_views = self.body.cached_views

        for child in cached_views.itervalues():
            child.title.clear_widgets()

        these = ravel(repeat(i, 7) for i in sorted(cached_views.itervalues(), key=cached_views.get))
        those = (_args_converter((date+timedelta(days=delta)), delta) for delta in xrange(-dt, ((7*6)-dt)))
        _on_release = lambda *_: self.body.handle_selection

        for this, that in izip(these, those):
            that.bind(on_release=_on_release(that))
            that.week = this
            this.title.add_widget(that)

    date = AliasProperty(_get_date, _set_date)#, bind=('size', 'pos'))

    def _args_converter(self, i, _):
        return {'index': i,
                'size_hint_y': None,
                'title_height': self.height/6.0,
                'content_height': self.height/6.0,
                'listview': self}
    
    def next_month(self, maxyear=datetime.MAXYEAR):
        self.body.deselect_all()

        if self.date.month == 12:
            new_year = self.date.year + 1

            if new_year <= maxyear:
                self.date = datetime.date(new_year, 1, self.date.day)

        else:
            self.date = datetime.date(self.date.year, self.date.month + 1, self.date.day)

    def previous_month(self, today=datetime.date.today()):
        self.body.deselect_all()

        if self.date.month == 1:
            new_date = datetime.date(self.date.year - 1, 12, self.date.day)
        else:
            new_date = datetime.date(self.date.year, self.date.month - 1, self.date.day)

        if ((new_date.month >= today.month) and (new_date.year >= today.year)):
            self.date = new_date

    def to_today(self, today=datetime.date.today()):
        self.date = today

class Needle(Widget):

    def on_touch_down(self, touch):
        return self.collide_point(*touch.pos)

class HourHand(FreeRotateLayout):
    color = ListProperty([])
    needle = ObjectProperty(None)
    ticks = NumericProperty(12)
    clock = ObjectProperty(None)

    def _rotation(self, touch_pos, center, degrees=math.degrees, atan2=math.atan2):
        y = touch_pos[1] - center[1]
        x = touch_pos[0] - center[0]
        calc = degrees(atan2(y, x))
        new_angle = calc if calc > 0 else 360+calc
        return new_angle

    def on_touch_down(self, touch):
        touch.push()
        touch.apply_transform_2d(self.to_local)
        touched = super(HourHand, self).on_touch_down(touch)
        touch.pop()

        if touched:
            touch.grab(self)            
            touch.ud['prev_angle'] = self._rotation(touch.pos, self.center)
            touch.ud['tmp'] = self.angle

        return touched

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            angle = touch.ud['tmp'] + (self._rotation(touch.pos, self.center)-touch.ud['prev_angle'])%360
            self.dispatch('on_change', angle)
            return True
        else:
            return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            factor = 360./self.ticks
            angle = (factor * round(self.angle/factor))
            self.dispatch('on_release', angle)
            return True
        else:
            return False

    def on_change(self, angle):
        self.angle = angle

    def on_release(self, angle):        
        self.dispatch('on_change', angle)
        self.angle += self.clock.minute_hand.angle/self.ticks

class MinuteHand(HourHand):
    ticks = NumericProperty(60)

    def on_change(self, angle):
        hour_hand = self.clock.hour_hand
        ticks = hour_hand.ticks
        inc = (angle - self.angle)/ticks

        if inc < -ticks:
            inc += 30
        elif inc > ticks:
            inc -= 30

        super(MinuteHand, self).on_change(angle)
        hour_hand.angle += inc

    def on_release(self, angle):
        self.dispatch('on_change', angle)

class ClockWidget(Widget):
    hour_hand = ObjectProperty(None)
    minute_hand = ObjectProperty(None)
    #time_of_day = OptionProperty('PM', options=['PM', 'AM'])

    def _get_hour(self):
        hour_hand = self.hour_hand
        ticks = hour_hand.ticks
        factor = 360./ticks
        #time = (factor * round(self.angle/factor))
        #return ((((360-time)/360.)*ticks) + ticks)%ticks
        angle = (factor * math.ceil(hour_hand.angle/factor))
        return int((angle/360.0)*ticks)

    def _set_hour(self, hour):
        hour_hand = self.hour_hand
        hour_hand.angle = 360.0*(hour%hour_hand.ticks)/hour_hand.ticks

    hour = AliasProperty(_get_hour, _set_hour)

    def _get_minute(self):
        minute_hand = self.minute_hand
        ticks = minute_hand.ticks
        factor = 360./ticks
        angle = (factor * math.ceil(minute_hand.angle/factor))
        return int((angle/360.0)*ticks)

    def _set_minute(self, minute):
        self.minute_hand.angle = (360.0*minute)/self.minute_hand.ticks

    minute = AliasProperty(_get_minute, _set_minute)

    def _get_time(self):
        return datetime.time(self.hour, self.minute)

    def _set_time(self, time):
        if time <> self.time:
            self.hour, self.minute = time.hour, time.minute
        else:
            return False

    time = AliasProperty(_get_time, _set_time, bind=('hour', 'minute'))

class DateTimeModal(Modal):
    datepicker = ObjectProperty(None)
    clock = ObjectProperty(None)

    def _get_when(self):
        datepicker = self.datepicker

        if datepicker.day:
            dt = datetime.datetime.combine(datepicker.date, self.clock.time)
            return dt.isoformat()
        else:
            return ''

    def _set_when(self, when):
        if when:
            dt = datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M:%S")
            self.datepicker.date = dt.date()#, self.clock.time = dt.date(), dt.time()
            self.clock.time = dt.time()
        else:
            return False

    when = AliasProperty(_get_when, _set_when)

class MyApp(App):
    ### Colors ###
    no_color = ListProperty((1.0, 1.0, 1.0, 0.0))
    light_blue = ListProperty([0.498, 0.941, 1.0, 1.0])
    blue = ListProperty((0.0, 0.824, 1.0, 1.0))
    dark_blue = ListProperty([0.004, 0.612, 0.7412, 1.0])
    red = ListProperty([1.0, 0.549, 0.5294, 1.0])
    purple = ListProperty([0.451, 0.4627, 0.561, 1.0])
    white = ListProperty([1.0, 1.0, 1.0, 1.0])
    light_gray = ListProperty([1.0, 0.98, 0.941, 1.0])
    smoke_white = ListProperty([0.95, 0.97, 0.973, 1.0])
    gray = ListProperty([0.9137, 0.933, 0.9451, 1.0])
    dark_gray = ListProperty([0.533, 0.533, 0.533, 1.0])
    shadow_gray = ListProperty([0.8, 0.8, 0.8, 1.0])

    def _open(self, *args):
        dtm = DateTimeModal()
        #self.foobar.opacity = 0.5
        dtm.when = datetime.datetime(2014, 1, 25, 20, 32).isoformat()
        dtm.engage()
        
        Animation(d=0.24, opacity=0.5).start(self.foobar)

    def build(self):
        #app = DatePicker()
        #app.date = datetime.date.today()
        app = Screen_()
        button = Button_(size_hint=(0.1, 0.1),
                         pos_hint={'center_x': 0.5, 'center_y': 0.5},
                         text='Click Me')
        button.bind(on_release=self._open)
        app.add_widget(button)
        inspector.create_inspector(Window, app)
        self.foobar = app
        return app

kv = """
#:import Week test3.Week
#:import datetime datetime.datetime
#:import ScreenManager kivy.uix.screenmanager.ScreenManager

<DayofTheWeek@Label>:
    font_name: 'Walkway Bold.ttf'
    color: app.white
    font_size: self.height*0.7

<Day>:
    opacity: 0.95 if not self.in_month and not self.is_selected else 1.0
    state_color: app.no_color if self.disabled else (app.blue if self.is_selected else app.white)
    text_color: app.white if self.disabled else (app.white if self.is_selected else app.blue)

<-DayDropDown>:
    state_color: app.dark_blue if self.state=='down' else app.blue
    canvas.before:
        Color:
            rgba: self.state_color
        Rectangle:
            size: self.size
            pos: self.pos

    BoxLayout:
        size: 0.9*root.size[0], root.size[1]
        center: root.center
        spacing: 10

        BoxLayout:
            orientation: 'vertical'
            size_hint: 0.49, 1

            Label:
                size_hint: 1, 0.75
                color: app.white
                #text: '[b]' + root.text + '[/b]'
                text: '[b]' + 'Go to the Foobar'.upper() + '[/b]'
                markup: True
                font_size: (self.height*0.58)
                font_name: 'Oswald-Bold.otf'
                shorten: True
                text_size: (self.size[0], None)
            Label:
                size_hint: 1, 0.25
                color: app.white
                #text: 'On ' + root.day + ' at:'
                text: 'On Jan. 13th, 2013 at:'
                markup: True
                font_size: self.height*1.
                font_name: 'Walkway Bold.ttf'
                text_size: (self.size[0], None)

        Label:
            size_hint: 0.49, 0.8
            pos_hint: {'center_y': 0.5}
            text: '12:00'
            font_size: self.height
            color: app.white
            font_name: 'Walkway Bold.ttf'
            halign: 'right'
        BoxLayout:
            orientation: 'vertical'
            size_hint: 0.02, 1

            Label:
                color: app.white
                text: '>'
                font_size: self.height
                font_name: 'Walkway Bold.ttf'
            Label:
                color: app.white
                text: 'PM'
                font_size: self.width
                font_name: 'Oswald-Bold.otf'

<Week>:
    title: title_id
    content: content_id
    shadow_color: app.no_color
    height: self.title.height + (self.content.height*(1-self.collapse_alpha))

    GridLayout:
        id: title_id
        cols: 7
        rows: 1
        size_hint: 1, None
        #height: root.listview.height/7.0
        height: 83 + (1.0/3.0)
    DayDropDown:
        id: content_id
        size_hint: 1, None
        height: 83 + (1.0/3.0)
        top: title_id.y

<DatePicker>:
    title: title_id
    body: body_id
    orientation: 'vertical'
    day: int(body_id.selection[0].text) if body_id.selection else 0

    BoxLayout:
        size_hint: 1, 0.1

        Button_:
            text: '<'
            size_hint: None, 1
            width: self.height
            font_size: self.height*0.7
            on_press: root.previous_month()
        Label:
            id: title_id
            color: app.white
            text: root.month_names[root.month-1] + str(root.year)
            font_name: 'Walkway Bold.ttf'
            font_size: self.height*0.421875
            canvas.before:
                Color:
                    rgba: app.blue
                Rectangle:
                    size: self.size
                    pos: self.pos
        Button_:
            text: '>'
            size_hint: None, 1
            width: self.height
            font_size: self.height*0.7
            on_press: root.next_month()

    BoxLayout:
        size_hint: 1, 0.05

        DayofTheWeek:
            text: 'SUN'
        DayofTheWeek:
            text: 'MON'
        DayofTheWeek:
            text: 'TUE'
        DayofTheWeek:
            text: 'WED'
        DayofTheWeek:
            text: 'THU'
        DayofTheWeek:
            text: 'FRI'
        DayofTheWeek:
            text: 'SAT'

    AccordionListView:
        id: body_id
        spacing: 0, 0
        list_item: Week
        args_converter: root._args_converter
        data: range(6)

<Numeral@Label>:
    font_size: self.height
    text_size: None, self.size[1]
    font_name: 'Walkway Bold.ttf'
    color: app.white
    size_hint: 0.1, 0.08

<HourHand>:
    needle: needle_id
    length: 0.3375
    depth: 0.015

    Needle:
        id: needle_id
        size_hint: root.depth, root.length
        pos_hint: {'center_x': 0.5, 'y': 0.5}
        canvas.before:
            Color:
                rgba: app.white
            Rectangle:    
                size: self.size
                pos: self.pos
            Color:
                rgba: app.purple
            Line:
                points: self.x, self.y, self.x, self.top, self.right, self.top, self.right, self.y

<MinuteHand>:
    length: 0.45
    depth: 0.01

<ClockWidget>:
    minute_hand: minute_hand_id
    hour_hand: hour_hand_id
    canvas.before:
        Color:
            rgba: app.smoke_white
        Rectangle:
            size: self.size
            pos: self.pos

    FloatLayout:
        size: min(root.size), min(root.size)
        pos: 0.5*(root.size[0]-self.size[0]), 0.5*(root.size[1]-self.size[1])
        canvas.before:
            Color:
                rgba: app.blue
            Line:
                width: 0.04*self.height
                ellipse: self.pos[0]+0.045455*self.size[0], self.pos[1]+0.045455*self.size[1], 0.92*self.size[0], 0.92*self.size[1]
            Color:
                rgba: app.dark_blue
            Ellipse:
                size: 0.5*self.size[0], 0.5*self.size[1]
                pos: self.pos[0]+0.25*self.size[0], self.pos[1]+0.25*self.size[1]

        Numeral:
            text: '12'
            pos_hint: {'center_x':0.5, 'center_y':0.95455}
        Numeral:
            text: '1'
            pos_hint: {'center_x':0.727273, 'center_y':0.89365}
        Numeral:
            text: '2'
            pos_hint: {'center_x':0.89365, 'center_y':0.727273}
        Numeral:
            text: '3'
            pos_hint: {'center_x':0.95455, 'center_y':0.5}
        Numeral:
            text: '4'
            pos_hint: {'center_x':0.89365, 'center_y':0.27273}
        Numeral:
            text: '5'
            pos_hint: {'center_x':0.727273, 'center_y':0.1063521}
        Numeral:
            text: '6'
            pos_hint: {'center_x':0.5, 'center_y':0.045455}
        Numeral:
            text: '7'
            pos_hint: {'center_x':0.27273, 'center_y':0.1063521}
        Numeral:
            text: '8'
            pos_hint: {'center_x':0.106352, 'center_y':0.27273}
        Numeral:
            text: '9'
            pos_hint: {'center_x':0.045455, 'center_y':0.5}
        Numeral:
            text: '10'
            pos_hint: {'center_x':0.106352, 'center_y':0.727273}
        Numeral:
            text: '11'
            pos_hint: {'center_x':0.27273, 'center_y':0.89365}
        HourHand:
            id: hour_hand_id
            clock: root
            size_hint: 1, 1
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        MinuteHand:
            id: minute_hand_id
            clock: root
            size_hint: 1, 1
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}

<DateTimeModal>:
    clock: clock_id
    datepicker: datepicker_id
    size_hint: 0.9, 0.9
    pos_hint: {'center_x': 0.5, 'center_y': 0.5}

    DatePicker:
        id: datepicker_id
        pos_hint: {'x': 0, 'top': 1}
        size_hint: 1, None
        height: self.width
    ClockWidget:
        id: clock_id
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        size_hint: 1, None
        height: self.width
        opacity: 0.0

"""

if __name__ == '__main__':
    Builder.load_string(kv)
    MyApp().run()
