from kivy.metrics import sp
from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.widget import Widget
from adapters import ListViewAdapter
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, DictProperty, ListProperty, AliasProperty, ReferenceListProperty, OptionProperty
from kivy.lang import Builder
import math

class Placeholder(Widget):
    ix = NumericProperty(-1)
    text = StringProperty('')

"""class Scroller(StencilView):
    scroll_distance = NumericProperty(sp(Config.getint('widgets', 'scroll_distance')))
    scroll_wheel_distance = NumericProperty(20)
    scroll_timeout = NumericProperty(Config.getint('widgets', 'scroll_timeout'))
    scroll_y = NumericProperty(1.)
    bar_margin = NumericProperty(0)
    bar_color = ListProperty((.7, .7, .7, .9))
    bar_alpha = NumericProperty(1.)
    bar_width = NumericProperty('2dp')
    bar_pos_x = OptionProperty('bottom', options=('top', 'bottom'))
    bar_pos_y = OptionProperty('right', options=('left', 'right'))
    effect_cls = ObjectProperty(DampedScrollEffect, allownone=True)
    effect_y = ObjectProperty(None, allownone=True)
    viewport_size = ListProperty([0, 0])
    scroll_type = OptionProperty(['content'], options=(['content'], ['bars'],
                                 ['bars', 'content'], ['content', 'bars']))
    _viewport = ObjectProperty(None, allownone=True)

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / scrollview size %
        if self._viewport is None:
            return 0, 1.
        vh = self._viewport.height
        h = self.height
        if vh < h or vh == 0:
            return 0, 1.
        ph = max(0.01, h / float(vh))
        sy = min(1.0, max(0.0, self.scroll_y))
        py = (1. - ph) * sy
        return (py, ph)

    vbar = AliasProperty(_get_vbar, None, bind=('scroll_y', '_viewport', 'viewport_size'))

    def _set_viewport_size(self, instance, value):
        self.viewport_size = value

    def on__viewport(self, instance, value):
        if value:
            value.bind(size=self._set_viewport_size)
            self.viewport_size = value.size

    def __init__(self, **kwargs):
        self._touch = None
        self._trigger_update_from_scroll = Clock.create_trigger(self.update_from_scroll, -1)"""

class DNDListView(FloatLayout, ListViewAdapter):
    scrollview = ObjectProperty(None)
    container = ObjectProperty(None)
    row_height = NumericProperty(None)
    scrolling = BooleanProperty(False)
    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _wstart = NumericProperty(0)
    _wend = NumericProperty(None, allownone=True)
    _i_offset = NumericProperty(0)
    placeholder = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type("on_scroll_complete")
        self.register_event_type("on_drag_start")
        self.register_event_type("on_drag_finish")
        self.register_event_type("on_pos_change")
        self.register_event_type("on_motion_over")
        self.register_event_type("on_motion_out")
        super(DNDListView, self).__init__(**kwargs)

        self._trigger_populate = Clock.create_trigger(self._do_layout, -1)
        self.bind(size=self._trigger_populate,
                  pos=self._trigger_populate)

    def on_data(self, instance, value):
        super(DNDListView, self).on_data(instance, value)
        instance._sizes.clear()
        instance._reset_spopulate()

    def _scroll(self, scroll_y, ceil=math.ceil, floor=math.floor):
        if self.row_height:
            self._scroll_y = scroll_y
            scroll_y = 1 - min(1, max(scroll_y, 0))
            container = self.container
            mstart = (container.height - self.height) * scroll_y
            mend = mstart + self.height

            # convert distance to index
            rh = self.row_height
            istart = int(ceil(mstart / rh))
            iend = int(floor(mend / rh))

            istart = max(0, istart - 1)
            iend = max(0, iend - 1)

            istart -= self._i_offset
            iend += self._i_offset

            if istart < self._wstart:
                rstart = max(0, istart - 10)
                self.populate(rstart, iend)
                self._wstart = rstart
                self._wend = iend
            elif iend > self._wend:
                self.populate(istart, iend + 10)
                self._wstart = istart
                self._wend = iend + 10

    def _do_layout(self, *args):
        self._sizes.clear()
        self.populate()

        self.row_height = rh = next(self._sizes.itervalues(), 0) #since they're all the same
        self.container.height = rh * self.get_count()

    def _reset_spopulate(self, *args):
        self._wend = None
        self.populate()
        # simulate the scroll again, only if we already scrolled before
        # the position might not be the same, mostly because we don't know the
        # size of the new item.
        if hasattr(self, '_scroll_y'):
            self._scroll(self._scroll_y)

    def populate(self, istart=None, iend=None):
        container = self.container
        sizes = self._sizes
        rh = self.row_height
        get_view = self.get_view

        # ensure we know what we want to show
        if istart is None:
            istart = self._wstart
            iend = self._wend

        # clear the view
        container.clear_widgets()

        # guess only ?
        if iend is not None:

            # fill with a "padding"
            fh = 0
            for x in xrange(istart):
                fh += sizes[x] if x in sizes else rh
            container.add_widget(Widget(size_hint_y=None, height=fh))

            # now fill with real item_view
            index = istart
            while index <= iend:
                item_view = get_view(index)
                index += 1

                if item_view is not None:
                    sizes[index] = item_view.height
                    container.add_widget(item_view)
        else:
            available_height = self.height
            real_height = 0
            index = self._index
            count = 0

            while available_height > 0:
                item_view = get_view(index)

                if item_view is None:
                    break

                sizes[index] = item_view.height
                index += 1
                count += 1
                container.add_widget(item_view)
                available_height -= item_view.height
                real_height += item_view.height

    def scroll_to(self, index=0):
        if not self.scrolling:
            self.scrolling = True
            self._index = index
            self.populate()
            self.dispatch('on_scroll_complete')

    def on_scroll_complete(self, *args):
        self.scrolling = False

    def on_drag_start(self, widget):
        self.deselect_all()

    def on_drag_finish(self, widget):
        pass

    def on_pos_change(self, widget):
        placeholder = self.placeholder

        if not placeholder:
            self.dispatch('on_motion_over', widget)
            return placeholder

        children = self.container.children
        p_ix = children.index(placeholder)
        _dict = {}

        for child in children:
            if (widget.collide_widget(child) and (child is not placeholder)):
                c_ix = children.index(child)

                if ((widget.center_y <= child.top) and (widget.center_y <= placeholder.y)) or ((widget.center_y >= child.y) and (widget.center_y >= placeholder.top)):
                    children.insert(c_ix, children.pop(p_ix))
                    #maybe scroll here
                    _dict = dict([(placeholder.text, child.ix)])

                    if child.text:
                        _dict[child.text] = placeholder.ix

                    child.ix, placeholder.ix = placeholder.ix, child.ix

                return _dict

    def deparent(self, widget):
        container = self.container
        placeholder = self.placeholder = Placeholder(size=widget.size,
                                                     size_hint_y=None,
                                                     index=widget.index,
                                                     text=widget.text,
                                                     ix=widget.ix,
                                                     opacity=0.0)

        container.add_widget(placeholder, container.children.index(widget))
        container.remove_widget(widget)
        widget.size_hint_x = None
        container.get_root_window().add_widget(widget)
        return

    def reparent(self, widget):
        placeholder = self.placeholder

        if placeholder:
            container = self.container

            if placeholder.collide_widget(widget):
                index = container.children.index(placeholder)
                container.remove_widget(placeholder)
                container.get_root_window().remove_widget(widget)
                container.add_widget(widget, index)
                widget.size_hint_x = 1.
                widget.ix = placeholder.ix
                self.placeholder = None

    def on_motion_over(self, *args):
        pass

    def on_motion_out(self, widget, _dict, *args):
        widget.title.state = 'normal'
        self.parent.dispatch('on_drop', _dict)

class AccordionListView(DNDListView):

    def _lcm(self, a, b):
        a, b = int(a), int(b)
        numerator = a * b

        while b:
            a, b = b, a%b

        if not a:
            return a - 1
        else:
            return numerator/a

    def on__sizes(self, instance, value):
        if value:
            #lcm = lambda a, b: ((a * b)/gcd(floor(a),floor(b)))
            sizes = set(value.itervalues()); _min = min(sizes); _max = max(sizes)
            count = instance.get_count() - 1
            instance.container.height = real_height = _max + (_min * count)
            instance.row_height = r_h = real_height / (count + 1)
            numerator = self._lcm(_min, r_h)
            instance._i_offset = int((numerator/_min) - (numerator/r_h)) + 1

    def populate(self, istart=None, iend=None):
        container = self.container
        sizes = self._sizes
        rh = self.row_height
        get_view = self.get_view

        # ensure we know what we want to show
        if istart is None:
            istart = self._wstart
            iend = self._wend

        # clear the view
        container.clear_widgets()

        # guess only ?
        if iend is not None:
            
            # fill with a "padding"
            fh = 0
            for x in xrange(istart):
                if x in sizes:
                    fh += sizes[x]
                else:
                    fh += rh
            container.add_widget(Widget(size_hint_y=None, height=fh))

            # now fill with real item_view
            index = istart
            while index <= iend:
                item_view = get_view(index)
                index += 1

                if item_view is not None:
                    item_view.listview = self
                    container.add_widget(item_view)
        else:
            available_height = self.height
            real_height = 0
            index = self._index
            count = 0

            while available_height > 0:
                item_view = get_view(index)

                if item_view is None:
                    break

                item_view.listview = self
                index += 1
                count += 1
                container.add_widget(item_view)
                available_height -= item_view.height
                real_height += item_view.height

        self._do_layout() 

    def _do_layout(self, *args):
        sizes = self._sizes
        d = {}

        for child in self.container.children:
            if type(child) is not Widget:
                d[child.index] = child.height

        self._sizes = dict(sizes, **d)

class ActionListView(AccordionListView):

    def on_motion_over(self, widget):
        children = self.container.children

        for child in children:
            if child.collide_point(*widget.center):
                child.title.state = 'down'
            elif child.title.state <> 'normal':
                child.title.state = 'normal'

    def on_motion_out(self, widget, _dict, *args):
        children = self.container.children

        for child in children:
            if child.title.state == 'down':
                child.ix, widget.ix = widget.ix, child.ix
                d = {child.text: child.ix, widget.text: widget.ix}
                _dict = dict(_dict, **d)
                self.get_root_window().remove_widget(widget)

        super(ActionListView, self).on_motion_out(widget, _dict)

Builder.load_string("""
#:import Scroller scroller.Scroller

<DNDListView>:
    spacing: 1
    container: container_id
    scrollview: scrollview_id

    Scroller:
        id: scrollview_id
        pos_hint: {'x': 0, 'y': 0}
        on_scroll_y: root._scroll(args[1])
        do_scroll_x: False

        GridLayout:
            id: container_id
            cols: 1
            spacing: root.spacing
            size_hint: 1, None

<-ActionListView>:
    container: container_id

    GridLayout:
        id: container_id
        cols: 1
        spacing: 0, 1
        size_hint: 1, None
        pos_hint: {'top': 1}

<-QuickListView@DNDListView>:
    container: container
    selection_mode: 'None'

    GridLayout:
        cols: 1
        id: container
        size_hint: 1, 1
""")
