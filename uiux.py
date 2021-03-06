from kivy.properties import ObjectProperty, NumericProperty, ListProperty, OptionProperty, StringProperty, BooleanProperty, DictProperty, AliasProperty
from kivy.uix.screenmanager import SlideTransition, Screen
from kivy.graphics.transformation import Matrix
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.vector import Vector
from kivy.lang import Builder
from kivy.clock import Clock

from functools import partial
import math

class StatusBar(Widget):

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.dispatch('on_status_bar')
            return True

class BoundedTextInput(TextInput):
    max_chars = NumericProperty(31)
    active_color = ListProperty([])
    inactive_color = ListProperty([])

    def insert_text(self, substring, from_undo=False):
        if not from_undo and (len(self.text) + len(substring) > self.max_chars):
            return
        super(BoundedTextInput, self).insert_text(substring, from_undo)

    def on_touch_down(self, touch):
        super(BoundedTextInput, self).on_touch_down(touch)
        return self.collide_point(*touch.pos)

class Screen_(Screen):
    root_directory = ObjectProperty(None)
    polestar = ObjectProperty(None, allownone=True)
    _anim = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type('on_status_bar')
        super(Screen_, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        polestar = self.polestar

        if polestar:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            ret = polestar.dispatch('on_touch_down', touch)
            touch.pop()

            if not ret:
                self.polestar = None

            return ret

        else:
            return super(Screen_, self).on_touch_down(touch)

    def on_lists(self):
        self.manager.transition = SlideTransition(direction="right", duration=0.2)
        self.manager.current = 'Pages Screen'

        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE notebook
                       SET bookmark=0
                       WHERE page=? AND bookmark=1;
                       """,
                       (self.page,))

    def on_delete(self, *args):
        pass

    def on_complete(self, *args):
        pass

    def on_status_bar(self, *args):
        pass

class Selectable(object):
    index = NumericProperty(-1)
    is_selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Selectable, self).__init__(**kwargs)

    def on_is_selected(self, instance, value):
        if value:
            instance.select()
        else:
            instance.deselect()

    def select(self, *args):
        pass

    def deselect(self, *args):
        pass

    def on_release(self):
        pass

class Base(Widget):
    text = StringProperty('')
    aleft = BooleanProperty(False)
    text_color = ListProperty([0, 0.824, 1, 1])
    state_color = ListProperty([])
    font_size = NumericProperty(0)
    font_name = StringProperty('Walkway Bold.ttf')
    shorten = BooleanProperty(False)
    markup = BooleanProperty(False)

    def on_state(self, *args):
        pass

    def on_touch_down(self, touch):
        if not self.disabled:
            touch.grab(self)
            touch.ud[self] = True

        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        else:
            return False

class Clickable(Base):

    def _press_(self, dt):
        if ((self.state == 'normal') and not self.disabled):
            self._do_press()
            self.dispatch('on_press')
        else:
            return False

    def _release_(self, dt):
        if self.state == 'normal':
            self.dispatch('on_release')
        else:
            return False
    
    state = OptionProperty('normal', options=('normal', 'down'))
    trigger_press = ObjectProperty(Clock.create_trigger(_press_, 0.0625))
    trigger_release = ObjectProperty(Clock.create_trigger(_release_, .15))

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        super(Clickable, self).__init__(**kwargs)

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            return False

        if self.state == 'normal':
            sup = super(Base, self).on_touch_down(touch)

            if sup:
                return sup
            else:
                self.trigger_press()

        return super(Clickable, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'down':
                sup = super(Base, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    self._do_release()
                    self.trigger_release()

        return super(Clickable, self).on_touch_up(touch)

    def on_press(self):
        pass

    def on_release(self):
        pass

class DelayedClickable(Clickable):

    def _release_(self, dt):
        if self.state == 'down':
            self.dispatch('on_release')
            self._do_release()
        else:
            return False
    
    trigger_release = ObjectProperty(Clock.create_trigger(_release_, .15))

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'down':
                sup = super(Base, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    self.trigger_release()

        return super(Clickable, self).on_touch_up(touch)

class Deletable(Base):    
    state = OptionProperty('normal', options=('normal', 'delete'))
    delete_button = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type('on_delete_out')
        super(Deletable, self).__init__(**kwargs)

    def on_state(self, instance, value):
        if ((value <> 'delete') and instance.delete_button):
            if instance.layout.right <> instance.right:
                instance.dispatch('on_delete_out', instance.layout)

            instance.remove_widget(instance.delete_button)
            instance.delete_button = None
            instance.screen.polestar = None

        elif value == 'delete':
            instance.delete_button = deletebutton = DeleteButton(size=(0.2*instance.size[0], instance.size[1]),
                                                                 pos=((instance.right-(0.2*instance.size[0])), instance.pos[1]),
                                                                 button=instance)
            instance.add_widget(deletebutton, 1)
            instance.screen.polestar = instance

        return super(Deletable, self).on_state(instance, value)

    def on_touch_down(self, touch):
        if self.state == 'delete':
            sup = super(Base, self).on_touch_down(touch)

            if not sup:
                self.dispatch('on_delete_out', self.layout)

            return True

        else:
            return super(Deletable, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'down':#in ('down', 'normal'):
                sup = super(Base, self).on_touch_move(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                elif ((touch.dx < -10) and not self.delete_button):
                    self.state = 'delete'

            if self.state == 'delete':
                new_pos = max(self.delete_button.x, min((self.layout.right+touch.dx), self.right))
                self.layout.right = new_pos
                return True

        return super(Deletable, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'delete':
                sup = super(Base, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    touch.ungrab(self)
                    layout = self.layout

                    if (layout.right < 0.9*self.right):
                        self._anim = Animation(right=self.delete_button.x, t='out_quad', d=0.2).start(layout)
                    else:
                         self.dispatch('on_delete_out', layout)

                    return True

        return super(Deletable, self).on_touch_up(touch)

    def on_delete_out(self, layout, *args):
        _anim = Animation(right=self.right, t='out_quad', d=0.2)

        if self.state == 'delete':
            def _do_release():
                self.state = 'normal'

            _anim.bind(on_complete=lambda *_: _do_release())

        self._anim = _anim.start(layout)

class Completable(Base):
    state = OptionProperty('normal', options=('normal', 'complete'))
    complete_button = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type('on_complete_out')
        super(Completable, self).__init__(**kwargs)

    def on_state(self, instance, value):
        if ((value <> 'complete') and instance.complete_button):
            if instance.layout.x <> instance.x:
                instance.dispatch('on_complete_out', instance.layout)

            instance.remove_widget(instance.complete_button)
            instance.complete_button = instance.screen.polestar = None

        elif value == 'complete':
            instance.complete_button = completebutton = CompleteButton(size=(instance.size[1], instance.size[1]), pos=instance.pos, button=self)
            instance.add_widget(completebutton, 1)
            instance.screen.polestar = instance

        return super(Completable, self).on_state(instance, value)

    def on_touch_down(self, touch):
        if self.state == 'complete':
            sup = super(Base, self).on_touch_down(touch)

            if not sup:
                self.dispatch('on_complete_out', self.layout)

            return True

        else:
            return super(Completable, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'down':#in ('down', 'normal'):
                sup = super(Base, self).on_touch_move(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                elif ((touch.dx > 10) and not self.complete_button):
                    self.state = 'complete'

            if self.state == 'complete':
                new_pos = max(self.x, min((self.layout.x+touch.dx), self.complete_button.right))
                self.layout.x = new_pos
                return True

        return super(Completable, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'complete':
                sup = super(Base, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    touch.ungrab(self)
                    layout = self.layout

                    if (layout.x > 0.078125*self.width):
                        self._anim = Animation(x=self.complete_button.right, t='out_quad', d=0.2).start(layout)
                    else:
                         self.dispatch('on_complete_out', layout)

                    return True

        return super(Completable, self).on_touch_up(touch)

    def on_complete_out(self, layout, *args):
        _anim = Animation(x=self.x, t='out_quad', d=0.2)

        if self.state == 'complete':
            def _do_release():
                self.state = 'normal'

            _anim.bind(on_complete=lambda *_: _do_release())

        self._anim = _anim.start(layout)

class DoubleClickable(Base):
    double_click_switch = BooleanProperty(False)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if (touch.is_double_tap and (touch.double_tap_time < 0.250)):
                touch.ungrab(self)
                self.double_click_switch = not self.double_click_switch
                return True
                
            else:
                #return super(DoubleClickable, self).on_touch_up(touch)
                return False

class Editable(DoubleClickable):
    state = OptionProperty('normal', options=('normal', 'edit'))
    textinput = ObjectProperty(None, allownone=True)

    def on_text_validate(self, instance):
        if not instance.text: #if instance.text == ""
            instance.focus = False
            return False
        else:
            self.text = instance.text.lstrip()
            instance.focus = False
            return True

    def on_text_focus(self, instance, focus):
        if focus is False:
            self.screen.polestar = None
            self.state = 'normal'

    def on_touch_down(self, touch):
        if self.state == 'edit':
            sup = super(Base, self).on_touch_down(touch)

            if not sup:
                self.state = 'normal'
            return True

        else:
            return super(Editable, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'edit':
                touched_children = super(Base, self).on_touch_up(touch)

                if touched_children:
                    touch.ungrab(self)
                    return touched_children
                    
            elif self.state == 'normal':
                return super(Editable, self).on_touch_up(touch)

        #return super(Editable, self).on_touch_up(touch)
        print self.__mro__
        return super(DoubleClickable, self).on_touch_up(touch)

    def on_double_click_switch(self, instance, value):
        if value:
            instance.state = 'edit'

    def on_state(self, instance, value):
        if ((value <> 'edit') and instance.textinput):
            instance.remove_widget(instance.textinput)
            instance.textinput = None
            instance.screen.polestar = None
            instance.double_click_switch = False

        elif value == 'edit':
            instance.textinput = t = BoundedTextInput(text=instance.text,
                                                      size_hint=(None, None),
                                                      font_size=instance.label.font_size,
                                                      font_name=instance.label.font_name,
                                                      pos=instance.pos,
                                                      size=instance.size,
                                                      multiline=False)
            instance.add_widget(instance.textinput)
            t.bind(on_text_validate=instance.on_text_validate, focus=instance.on_text_focus)
            t.focus = True
            instance.screen.polestar = instance

        return super(Editable, self).on_state(instance, value)

class TouchDownAndHoldable(Base):
    state = OptionProperty('normal', options=('normal', 'down', 'dragged'))
    hold_time = NumericProperty(0.0)
    droppable_zone_objects = ListProperty([])

    def on_hold_down(self, dt):
        if ((self.state == 'down') and not self.disabled):
            self.hold_time += dt
        else:
            self.hold_time = 0.0
            return False

    def on_state(self, instance, value):
        widget = instance.parent
        listview = widget.listview

        if ((value <> 'dragged') and listview.placeholder):
            dzo = instance.droppable_zone_objects
            widget.opacity = 1.

            for viewer in dzo:
                if viewer.collide_point(*widget.center):
                    viewer.reparent(widget)
                    break

        elif value == 'dragged':
            listview.dispatch('on_drag_start', widget)
            listview.deparent(widget)

        return super(TouchDownAndHoldable, self).on_state(instance, value)

    def on_touch_down(self, touch):
        if self.state == 'normal':
            sup = super(Base, self).on_touch_down(touch)

            if not sup:
                Clock.schedule_interval(self.on_hold_down, 0.1)
            else:
                return sup

        return super(TouchDownAndHoldable, self).on_touch_down(touch)

    def on_touch_move(self, touch):  
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'down':
                sup = super(Base, self).on_touch_move(touch)

                if sup:
                    return sup
                elif (self.hold_time > 0.2):
                    self.state = 'dragged'
                    touch.ud['indices'] = {}
                    return True
            
            elif self.state == 'dragged':
                widget = self.parent
                widget.center_y = touch.y
                dzo = self.droppable_zone_objects

                for viewer in dzo:
                    if viewer.collide_point(*widget.center):
                        d = viewer.dispatch('on_pos_change', widget)

                        if d:
                            touch.ud['indices'] = dict(touch.ud['indices'], **d)
                        return True

        return super(TouchDownAndHoldable, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        #super(Base, self).on_touch_up(touch)

        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'dragged':
                touch.ungrab(self)
                dzo = self.droppable_zone_objects
                widget = self.parent

                for viewer in dzo:
                    if viewer.collide_point(*widget.center):
                        Clock.schedule_once(viewer.dispatch('on_motion_out', widget, touch.ud['indices']), 0.15)
                        return True

        return super(TouchDownAndHoldable, self).on_touch_up(touch)

    def on_hold_in(self):
        pass

    def on_hold_out(self):
        pass

"""class DragNDroppable(_OnStateClass):
    droppable_zone_objects = ListProperty([])
    bound_zone_objects = ListProperty([])
    drag_opacity = NumericProperty(0.75)
    listview = ObjectProperty(None)

    def on_state(self, instance, value):
        container = instance.parent
        placeholder = instance.listview.placeholder
        
        if ((value <> 'dragged') and placeholder):
            instance.opacity = 1.
            for viewer in instance.droppable_zone_objects:
                if viewer.collide_point(*instance.center):
                    viewer.reparent(instance)
                    return

        elif ((value == 'dragged') and not placeholder):
            instance.opacity = self.drag_opacity
            #instance.dispatch('on_drag_start', instance)
            #instance.set_bound_axis_positions()
            #instance._old_drag_pos = self.pos
            #instance._old_parent = self.parent
            #instance._old_index = self.parent.children.index(self)
            
            instance.listview.deparent(instance)

        return super(DragNDroppable, self).on_state(instance, value)

    def on_touch_move(self, touch):
        if touch.grab_current is self.title:
            #assert(self in touch.ud)
            print 'it worked!'

            if self.state == 'dragged':
                self.center_y = touch.y

                for viewer in self.droppable_zone_objects:
                    if viewer.collide_point(*self.center):
                        d = viewer.dispatch('on_pos_change', self)

                        if d:
                            touch.ud['indices'] = dict(touch.ud['indices'], **d)
                        return True

        return super(DragNDroppable, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)
            touch.ungrab(self)

            if self.state == 'dragged':
                self.listview._ix_update = touch.ud['indices']

        return super(DragNDroppable, self).on_touch_up(touch)"""

'''class Date(Editable):
    pass

class Notes(Editable):
    pass'''

class Button_(Clickable):
    state = OptionProperty('normal', options=('down', 'normal'))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        else:
            return super(Button_, self).on_touch_down(touch)

class DeleteButton(Button_):
    button = ObjectProperty(None, allownone=True)
    rectangle_size_x = NumericProperty(100)
    rectangle_pos = ListProperty([0, 0])
    _anim = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(DeleteButton, self).__init__(**kwargs)
        self.trigger_action = Clock.create_trigger(self.trigger_release, 0)

    def on_press(self):
        if self.button:
            return self.button.screen.on_delete(self.button)
            

class CompleteButton(DeleteButton):
    rectangle_size_x = NumericProperty(-100)

    def on_press(self):
        if self.button:
            return self.button.screen.on_complete(self.button)

class DoubleClickButton(DoubleClickable):
    icon_text = StringProperty('')
    icon_font_name = StringProperty('heydings_icons.ttf')
    text = StringProperty('')

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        else:
            return super(DoubleClickButton, self).on_touch_down(touch)

class FreeRotateLayout(Widget):
    content = ObjectProperty(None)
    transform = ObjectProperty(Matrix())
    transform_inv = ObjectProperty(Matrix())

    def __init__(self, **kwargs):
        self.register_event_type('on_change')
        self.register_event_type('on_release')
        super(FreeRotateLayout, self).__init__(**kwargs)

    def to_parent(self, x, y, **k):
        p = self.transform.transform_point(x, y, 0)
        return (p[0], p[1])

    def to_local(self, x, y, **k):
        p = self.transform_inv.transform_point(x, y, 0)
        return (p[0], p[1])

    def apply_transform(self, trans, post_multiply=False, anchor=(0, 0), matrix=Matrix):
        t = matrix().translate(anchor[0], anchor[1], 0)
        t = t.multiply(trans)
        t = t.multiply(matrix().translate(-anchor[0], -anchor[1], 0))

        if post_multiply:
            self.transform = self.transform.multiply(t)
        else:
            self.transform = t.multiply(self.transform)

    def _get_bbox(self):
        xmin, ymin = xmax, ymax = self.to_parent(0, 0)

        for point in [(self.width, 0), (0, self.height), self.size]:
            x, y = self.to_parent(*point)

            if x < xmin:
                xmin = x
            if y < ymin:
                ymin = y
            if x > xmax:
                xmax = x
            if y > ymax:
                ymax = y

        return (xmin, ymin), (xmax - xmin, ymax - ymin)

    bbox = AliasProperty(_get_bbox, None, bind=('width', 'height'))

    def _get_angle(self, vector=Vector):
        v1 = vector(0, 10)
        tp = self.to_parent
        v2 = vector(*tp(*self.pos)) - tp(self.x, self.y + 10)
        ret = -1.0 * (v1.angle(v2) + 180) % 360
        return ret

    def _set_angle(self, angle, matrix=Matrix, radians=math.radians, ceil=math.ceil):
        angle_change = self.angle - angle
        r = matrix().rotate(-radians(angle_change), 0, 0, 1)
        self.apply_transform(r, post_multiply=True, anchor=self.to_local(*self.center))

    angle = AliasProperty(_get_angle, _set_angle, bind=('x', 'y'))

    def _get_center(self):
        bbox = self.bbox
        return (bbox[0][0] + bbox[1][0] / 2.0,
                bbox[0][1] + bbox[1][1] / 2.0)

    def _set_center(self, center, vector=Vector, matrix=Matrix):
        if center <> self.center:
            t = vector(*center) - self.center
            trans = matrix().translate(t.x, t.y, 0)
            self.apply_transform(trans)
        else:
            return False

    center = AliasProperty(_get_center, _set_center, bind=('bbox', ))

    def _get_pos(self):
        return self.bbox[0]

    def _set_pos(self, pos, vector=Vector, matrix=Matrix):
        _pos = self.bbox[0]

        if pos <> _pos:
            t = vector(*pos) - _pos
            trans = matrix().translate(t.x, t.y, 0)
            self.apply_transform(trans)
        else:
            return False

    pos = AliasProperty(_get_pos, _set_pos, bind=('bbox', ))

    def _get_x(self):
        return self.bbox[0][0]

    def _set_x(self, x):
        if x == self.bbox[0][0]:
            return False
        self.pos = (x, self.y)
        return True

    x = AliasProperty(_get_x, _set_x, bind=('bbox', ))

    def _get_y(self):
        return self.bbox[0][1]

    def _set_y(self, y):
        if y == self.bbox[0][1]:
            return False
        self.pos = (self.x, y)
        return True

    y = AliasProperty(_get_y, _set_y, bind=('bbox', ))

    def get_right(self):
        return self.x + self.bbox[1][0]

    def set_right(self, value):
        self.x = value - self.bbox[1][0]

    right = AliasProperty(get_right, set_right, bind=('x', 'width'))

    def get_top(self):
        return self.y + self.bbox[1][1]

    def set_top(self, value):
        self.y = value - self.bbox[1][1]

    top = AliasProperty(get_top, set_top, bind=('y', 'height'))

    def get_center_x(self):
        return self.x + self.bbox[1][0] / 2.

    def set_center_x(self, value):
        self.x = value - self.bbox[1][0] / 2.

    center_x = AliasProperty(get_center_x, set_center_x, bind=('x', 'width'))

    def get_center_y(self):
        return self.y + self.bbox[1][1] / 2.

    def set_center_y(self, value):
        self.y = value - self.bbox[1][1] / 2.

    center_y = AliasProperty(get_center_y, set_center_y, bind=('y', 'height'))

    def add_widget(self, *args):
        if self.content:
            self.content.add_widget(*args)
        else:
            super(FreeRotateLayout, self).add_widget(*args)

    def remove_widget(self, *args):
        if self.content:
            self.content.remove_widget(*args)
        else:
            super(FreeRotateLayout, self).remove_widget(*args)

    def clear_widgets(self):
        self.content.clear_widgets()

    def on_transform(self, instance, value):
        instance.transform_inv = value.inverse()

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return 0 <= x <= self.width and 0 <= y <= self.height

    def on_release(self, *args):
        pass

    def on_change(self, *args):
        pass


Builder.load_string("""
<NavBar@FloatLayout>:
    canvas.before:
        Color:
            rgba: app.blue
        Rectangle:
            size: self.size
            pos: self.pos

<Base>:
    label: label_id
    layout: layout_id
    state_color: app.no_color
    text_color: app.blue
    font_size: (self.height*0.421875)

    FloatLayout:
        id: layout_id
        size: root.size
        pos: root.pos
        canvas.before:
            Color:
                rgba: root.state_color
            Rectangle:
                size: self.size
                pos: self.pos

        Label:
            id: label_id
            pos_hint: {'x': 0, 'y': 0}
            text: root.text
            font_size: root.font_size
            font_name: root.font_name
            shorten: root.shorten
            color: root.text_color
            markup: root.markup
            text_size: (self.size[0]-(0.1*self.size[0]), None) if root.aleft else (None, None)

<Button_>:
    state_color: app.blue
    text_color: app.white

<DeleteButton>:
    text: 'Delete'
    state_color: app.red
    text_color: app.purple
    canvas.before:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.top-1, self.right, self.top-1
            width: 1.0

<CompleteButton>:
    text: 'O'
    width: self.height
    font_name: 'heydings_icons.ttf'
    font_size: self.height*0.7
    rectangle_size_x: self.size[0]
    rectangle_pos: self.right-self.rectangle_size_x, self.top-self.height
    state_color: app.purple
    text_color: app.white

<-BoundedTextInput>:
    font_name: 'Walkway Bold.ttf'
    active_color: app.white
    inactive_color: app.smoke_white
    foreground_color: app.dark_blue
    disabled: self.disabled
    canvas.before:
        Color:
            rgba: self.active_color if self.focus else self.inactive_color
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: (1, 0, 0, 1 if self.focus and not self.cursor_blink else 0)
        Rectangle:
            pos: [int(x) for x in self.cursor_pos]
            size: 1, -self.line_height
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text and not self.focus else self.foreground_color)

<FreeRotateLayout>:
    content: content_id
    canvas.before:
        PushMatrix
        MatrixInstruction:
            matrix: self.transform
    canvas.after:
        PopMatrix

    FloatLayout:
        id: content_id
        size: root.size

<StatusBar>:
    canvas.before:
        Color:
            rgba: app.blue
        Rectangle:
            size: self.size
            pos: self.pos

<Screen_>:
    canvas.before:
        Color:
            rgb: app.smoke_white
        Rectangle:
            size: self.size

    StatusBar:
        size_hint: 1, 0.0352
        pos_hint: {'x': 0, 'top': 1}
""")
