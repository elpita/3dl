from kivy.properties import ObjectProperty, ListProperty, NumericProperty, StringProperty, BooleanProperty, OptionProperty, AliasProperty
from uiux import Selectable, Clickable, Editable, Completable, Deletable, TouchDownAndHoldable
from kivy.uix.screenmanager import RiseInTransition, SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.utils import escape_markup
from kivy.uix.widget import Widget
from kivy.lang import Builder
from functools import partial
from kivy.clock import Clock

class AccordionListItem(Selectable, GridLayout):
    title = ObjectProperty(None)
    content = ObjectProperty(None)
    drag_opacity = NumericProperty(0.75)
    listview = ObjectProperty(None)
    shadow_color = ListProperty([])
    ix = NumericProperty(None)
    text = StringProperty('')
    why = BooleanProperty(False)
    collapse_alpha = NumericProperty(1.0)
    title_height_hint = NumericProperty(0.0)
    content_height_hint = NumericProperty(0.0)

    def __init__(self, **kwargs):
        self._anim_collapse = None
        self.register_event_type('on_release')
        super(AccordionListItem, self).__init__(**kwargs)

    def select(self, *args):
        if self._anim_collapse:
            self._anim_collapse.stop()
            self._anim_collapse = None

        self._anim_collapse = Animation(collapse_alpha=0.0,
                                        t='out_expo',
                                        d=0.25).start(self)

    def deselect(self, *args):
        if self._anim_collapse:
            self._anim_collapse.stop()
            self._anim_collapse = None

        self._anim_collapse = Animation(collapse_alpha=1.0,
                                        t='out_expo',
                                        d=0.25).start(self)

    def on_collapse_alpha(self, instance, value):
        instance.listview._do_layout()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        else:
            return super(AccordionListItem, self).on_touch_down(touch)

class PagesScreenItem(Editable, Completable, Deletable, Clickable):
    index = NumericProperty(-1)
    screen = ObjectProperty(None)
    state = OptionProperty('normal', options=('complete', 'delete', 'down', 'edit', 'normal'))

    def on_release(self):
        screen = self.screen
        cursor = screen.root_directory.cursor()
        screen.manager.transition = SlideTransition(direction="left", duration=0.2)
        #config[whatever] = instance.text
        cursor.execute("""
                       SELECT COUNT(what)
                       FROM notebook
                       WHERE page=? AND ix<3
                       """,
                       (self.text,))
        i = cursor.fetchall()[0][0]
        cursor.close()

        if i < 3:
            list_screen = screen.manager.get_screen('List Screen')
            list_screen.page = self.text
            list_screen.page_number = self.index
            screen.manager.current = 'List Screen'
        else:
            list_screen = screen.manager.get_screen('QuickView Screen')
            list_screen.page = self.text
            list_screen.page_number = self.index
            screen.manager.current = 'QuickView Screen'  

    def on_text_validate(self, instance):
        if super(PagesScreenItem, self).on_text_validate(instance):
            cursor = self.screen.root_directory.cursor()
            cursor.execute("""
                           UPDATE notebook
                           SET page=?
                           WHERE page_number=?
                           """,
                           (instance.text, self.index))
            #cursor.execute("commit")
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):

            if self.state == 'normal':
                return False
            else:
                self.state = 'normal'
                return True

        else:
            return super(PagesScreenItem, self).on_touch_down(touch)

class ListScreenItemTitle(Editable, Completable, Deletable, Clickable, TouchDownAndHoldable):
    state = OptionProperty('normal', options=('complete', 'delete', 'down', 'dragged', 'edit', 'normal'))
    screen = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):# and self.text):
            return False

        else:
            return super(ListScreenItemTitle, self).on_touch_down(touch)

class ListScreenItem(AccordionListItem):
    screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_importance')
        super(ListScreenItem, self).__init__(**kwargs)

        self.title.droppable_zone_objects = kwargs['droppable_zone_objects']
        self.title.aleft = kwargs['aleft']
        self.title.font_name = kwargs['font_name']
        self.title.screen = kwargs['screen']

    def on_importance(self, instance, value):
        if self.why <> value:
            _l = lambda *_: self.screen.dispatch('on_importance', self, value)
            Clock.schedule_once(_l, 0.25)

class ActionListItem(ListScreenItem):
    pass
    '''def on_state(self, instance, value):
        if value in ('normal', 'down'):
            if not instance.is_selected:
                instance.label.text = "[font='heydings_icons.ttf'][color=ffffff]- [/color][/font]" + escape_markup(instance.text)
                instance.markup = True
        else:
            instance.label.text = instance.text'''

class QuickViewScreenItemTitle(Completable, Deletable):
    state = OptionProperty('normal', options=('complete', 'delete', 'dragged', 'edit', 'normal'))

class QuickViewScreenItem(BoxLayout):
    ix = NumericProperty(None)
    text = StringProperty('')
    when = StringProperty('', allownone=True)
    why = BooleanProperty(False)
    how = StringProperty('', allownone=True)
    markup = BooleanProperty(False)
    screen = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):

            if self.state == 'normal':
                return False
            else:
                self.state = 'normal'
                return True

        else:
            return super(QuickViewScreenItem, self).on_touch_down(touch)

class ArchiveScreenItemTitle(Deletable, Clickable):
    state = OptionProperty('normal', options=('delete', 'down', 'normal'))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        else:
            return super(ArchiveScreenItemTitle, self).on_touch_down(touch)

class ArchiveScreenItem(AccordionListItem):
    pass

class Week(AccordionListItem):
    title_height = NumericProperty(0.0)
    content_height = NumericProperty(0.0)

Builder.load_string("""
#:import DoubleClickButton uiux.DoubleClickButton

<-AccordionListItem>:
    cols: 1
    size_hint: 1, None
    #height: self.title.height + (self.content.height*(1-self.collapse_alpha))
    shadow_color: app.shadow_gray
    canvas.before:
        StencilPush
        Rectangle:
            pos: self.pos
            size: self.size
        StencilUse
    canvas.after:
        StencilUnUse:
            Rectangle:
                pos: self.pos
                size: self.size
        StencilPop
        #Color:
            #rgba: root.shadow_color
        #Line:
            #points: self.x, self.y, self.right, self.y
            #width: 1.0

<PagesScreenItem>:
    aleft: True
    shorten: True
    height: self.screen.height*0.088
    state_color: app.light_gray if self.state == 'down' else app.white
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.y, self.right, self.y
            width: 1.0

<-DoubleClickButton>:
    size_hint: 0.5, 1
    pos_hint: {'center_x': 0.5}
    font_size: self.height*0.421875
    font_color: app.white
    opacity: 1.0 if self.double_click_switch else 0.5

    BoxLayout:
        size: root.size
        pos: root.pos

        Label:
            id: icon_id
            text: root.icon_text
            size_hint: None, 1
            width: self.height
            color: root.font_color
            font_name: root.icon_font_name
            font_size: root.font_size
        Label:
            text: root.text
            size_hint: None, 1
            width: root.width - icon_id.width
            color: root.font_color
            font_name: 'Walkway Bold.ttf'
            font_size: root.font_size
            text_size: self.size[0], None

<ListScreenItem>:
    title: title_id
    content: content_id
    state_color: app.white
    text_color: app.blue
    size_hint: 1, None
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))

    ListScreenItemTitle:
        id: title_id
        text: root.text
        screen: root.screen
        size_hint: 1, None
        height: root.screen.height*root.title_height_hint
        on_release: root.listview.handle_selection(root)
        state_color: root.state_color
        text_color: root.text_color
    BoxLayout:
        id: content_id
        orientation: 'vertical'
        size_hint: 1, None
        top: title_id.y
        height: root.screen.height*root.content_height_hint
        canvas.before:
            Color:
                rgba: title_id.state_color
            Rectangle:
                size: self.size
                pos: self.pos

        DoubleClickButton:
            icon_text: '!'
            text: 'IMPORTANT'
            double_click_switch: root.why
            on_double_click_switch: root.dispatch('on_importance', *args)
        DoubleClickButton:
            icon_text: 'T'
            #text: root.when
            on_double_click_switch: root.screen.dispatch('on_due_date', root, args[1])
        Label:
            text: 'foobar'
            font_size: self.height*0.421875

<ActionListItem>:
    state_color: app.blue if root.collapse_alpha==0.0 else (app.light_blue if self.title.state=='down' else app.gray)
    text_color: app.white if root.collapse_alpha==0.0 else app.dark_gray
    shadow_color: app.smoke_white

<ArchiveScreenItem>:
    aleft: True
    shorten: True
    height: self.screen.height*0.088
    state_color: app.smoke_white if self.state == 'down' else app.light_gray
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.y, self.right, self.y
            width: 1.0

<QuickViewScreenItemTitle>:
    label: self.label
    layout: layout_id
    label: label_id
    font_size: (self.height*0.421875)
    state_color: app.smoke_white
    canvas.before:
        Color:
            rgba: self.state_color
        Rectangle:
            size: self.size
            pos: self.pos
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.layout.x, self.label.y, self.label.right, self.label.y

    FloatLayout:
        size: root.size
        pos: root.pos

        CustomBoxLayout:
            id: layout_id
            orientation: 'horizontal'
            spacing: 5
            pos_hint: {'center_x': .5, 'center_y': .5}
            size_hint: 0.9, .75

            Label:
                id: label_id
                text: root.text
                font_size: root.font_size
                font_name: root.font_name
                shorten: root.shorten
                color: root.text_color
                markup: root.markup
                text_size: (self.size[0], None) if root.aleft else (None, None)

<QuickViewScreenItem>:
    orientation: 'vertical'
    padding: 10
    spacing: 5
    state: title_id.state

    QuickViewScreenItemTitle:
        id: title_id
        text: root.text
        screen: root.screen
        size_hint: 1, .4
        aleft: True
        markup: root.markup

    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, 0.9
        spacing: 10

        Label:
            size_hint: 0.8, 1
            text: root.how
            valign: 'top'
        BoxLayout:
            orientation: 'vertical'
            size_hint: 0.2, .6
            pos_hint: {'top' : 0.9}

            Label:
                size_hint: 1, .75
                text: '2 Days'
                font_size: (self.height*0.421875)
                canvas.before:
                    Color:
                        rgba: app.blue
                    Rectangle:
                        size: self.size
                        pos: self.pos
            Label:
                text: '11.06.2013'
                size_hint: 0.75, 0.25
                pos_hint: {'center_x' : .5}
                color: app.dark_gray

<Week>:
    title: title_id
    content: content_id
    shadow_color: app.no_color
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))

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
""")
