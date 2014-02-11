from kivy.properties import ListProperty, BooleanProperty, StringProperty, NumericProperty, ObjectProperty, AliasProperty
from uiux import Selectable, Button_, DelayedClickable, FreeRotateLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
#from kivy.uix.widget import Widget
#from uiux import FreeRotateLayout
from kivy.lang import Builder
import datetime, math, itertools

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

    def __init__(self, **kwargs):
        self.register_event_type('on_deselect')
        super(DatePicker, self).__init__(**kwargs)

    def on_deselect(self, *args):
        self.body.deselect_all()
    
    def next_month(self, maxyear=datetime.MAXYEAR):
        self.dispatch('on_deselect')

        if self.date.month == 12:
            new_year = self.date.year + 1

            if new_year <= maxyear:
                self.date = datetime.date(new_year, 1, self.date.day)

        else:
            self.date = datetime.date(self.date.year, self.date.month + 1, self.date.day)

    def previous_month(self, today=datetime.date.today()):
        self.dispatch('on_deselect')

        if self.date.month == 1:
            new_date = datetime.date(self.date.year - 1, 12, self.date.day)
        else:
            new_date = datetime.date(self.date.year, self.date.month - 1, self.date.day)

        if ((new_date.month >= today.month) and (new_date.year >= today.year)):
            self.date = new_date

    def to_today(self):
        self.dispatch('on_deselect')
        self.date = daetime.date.today()
"""
class HourHand(FreeRotateLayout):
    color = ListProperty([])
    needle = ObjectProperty(None)
    ticks = NumericProperty(12)
    clock = ObjectProperty(None)

    def rotation(self, touch_pos, center, degrees=math.degrees, atan2=math.atan2):
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
            touch.ud['prev_angle'] = self.rotation(touch.pos, self.center)
            touch.ud['tmp'] = self.angle

        return touched

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            angle = touch.ud['tmp'] + (self.rotation(touch.pos, self.center)-touch.ud['prev_angle'])%360
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
        self.angle = angle + self.clock.minute_hand.angle/self.ticks

class MinuteHand(HourHand):
    ticks = NumericProperty(60)

    def on_change(self, angle):
        hour_hand = self.clock.hour_hand
        ticks = hour_hand.ticks
        K = 360.0/ticks
        new_angle = angle - self.angle
        inc = new_angle/ticks

        if inc < -ticks:
            inc += 30
        elif inc > ticks:
            inc -= 30

        super(MinuteHand, self).on_change(angle)
        hour_hand.angle = hour_hand.angle + inc

    def on_release(self, angle):
        self.dispatch('on_change', angle)

class ClockWidget(Widget):
    hour = NumericProperty(0)
    minute = NumericProperty(0)
"""
class Modal(FloatLayout):
    _window = ObjectProperty(Window)
    _anim_alpha = NumericProperty(0.0)

    def __init__(self, **kwargs):
        self.register_event_type('on_open')
        self.register_event_type('on_dismiss')
        super(Modal, self).__init__(**kwargs)

    def engage(self, *args):
        self._window.add_widget(self)
        #a = Animation(_anim_alpha=1.0, d=0.1)
        #a.bind(on_complete=lambda *_: self.dispatch('on_open'))
        #a.start(self)
        #return self
        self.dispatch('on_open')

    def dismiss(self, *args, **kwargs):
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return self
        if kwargs.get('animation', True):
            Animation(_anim_alpha=0.0, d=0.1).start(self)
        else:
            self._anim_alpha = 0.0
        return self

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            self.dismiss()
            return True
        else:
            return super(Modal, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        super(Modal, self).on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super(Modal, self).on_touch_up(touch)
        return True

    def on__anim_alpha(self, instance, value):
        if value == 0.0 and instance._window is not None:
            instance._window.remove_widget(instance)

    def on_open(self):
        pass

    def on_dismiss(self):
        pass

Builder.load_string("""
#:import Week listitems.Week

<DayofTheWeek@Label>:
    font_name: 'Walkway Bold.ttf'
    color: app.blue
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
""")
