'''
Created on Jul 27, 2013

@author: Divine
'''
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from datepickerminiscreen import DatePickerMiniScreen
from kivy.lang import Builder
from uiux import Screen_

class ListScreen(Screen_):
    action_view = ObjectProperty(None)
    accordion_view = ObjectProperty(None)
    action_items = ListProperty([])
    list_items = ListProperty([])
    page = StringProperty('')
    page_number = NumericProperty(None)
    selection = ListProperty([])
    
    def __init__(self, **kwargs):
        self.register_event_type('on_drop')
        self.register_event_type('on_due_date')
        self.register_event_type('on_importance')
        super(ListScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        if self.page:
            cursor = self.root_directory.cursor()
            action_items = [(i, u"", u"", 0, u"") for i in xrange(3)]
            list_items = []

            for i in cursor.execute("""
                                    SELECT ix, what, when_, why, how
                                    FROM notebook
                                    WHERE page=? AND ix>=0
                                    ORDER BY ix
                                    """,
                                    (self.page,)):
                ix = i[0]#; print ix, i

                if ix < 3:
                    action_items[ix] = i
                else:
                    list_items.append(i)

            self.action_items = action_items
            self.list_items = list_items

    def _args_converter(self, row_index, an_obj):
        dict = {'droppable_zone_objects': [self.action_view,],
                'screen': self}
        dict['ix'], dict['text'], dict['when'], dict['why'], dict['how'] = an_obj
        dict['why'] = bool(dict['why'])

        if dict['ix'] < 3:
            dict['title_height_hint'] = (153./1136.)
            dict['content_height_hint'] = (322./1136.)
            dict['listview'] = self.action_view
            dict['aleft'] = True
            dict['font_name'] = 'Oswald-Bold.otf'
        else:
            dict['title_height_hint'] = 0.088
            dict['content_height_hint'] = (190./1136.)
            dict['droppable_zone_objects'].append(self.accordion_view)
            dict['listview'] = self.accordion_view
            dict['aleft'] = False
            dict['font_name'] = 'Walkway Bold.ttf'

        return dict

    def new_task(self, instance, text):
        text = text.lstrip()

        if text:
            cursor = self.root_directory.cursor()
            num = len(self.list_items) + 3
            cursor.execute("""
                           INSERT INTO notebook(bookmark, page_number, page, ix, what)
                           VALUES(?, ?, ?, ?, ?)
                           """,
                           (1, self.page_number, self.page, num, text))
            #cursor.execute('commit')
            self.dispatch('on_pre_enter')#, self, self.page)

        instance.text = ''
        instance.focus = False

    def on_delete(self, instance):
        #ix = instance.index if (instance.accordion is ActionListView) else (instance.index + 3)
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       DELETE FROM notebook
                       WHERE ix=? AND what=?
                       """,
                       (instance.ix, instance.title))
        self.dispatch('on_pre_enter')#, self, self.page)

    def on_complete(self, instance):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       INSERT INTO archive(page, what, when_, why, how)
                       SELECT page, what, when_, why, how
                       FROM notebook
                       WHERE page=? AND ix=? AND what=?
                       """,
                       (self.page, instance.ix, instance.title))
        self.dispatch('on_pre_enter')#, self, self.page)

    def on_importance(self, instance, value):
        instance.why = value
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE notebook
                       SET why=?
                       WHERE page=? AND ix=? AND what=?
                       """,
                       (int(value), self.page, instance.ix, instance.text))

    def on_due_date(self, instance, value):
        if value:
            manager = self.manager
            dpms = DatePickerMiniScreen(item=instance)
            manager.add_widget(dpms)
            manager.transition = RiseInTransition(duration=0.2)
            manager.current = 'DatePicker Mini-Screen'

    def on_drop(self, d):
        if d:
            items = ((k, v, self.page) for (v, k) in d.iteritems())
            cursor = self.root_directory.cursor()
            cursor.executemany("""
                               UPDATE notebook
                               SET ix=?
                               WHERE what=? AND page=?
                               """,
                               items)
            self.dispatch('on_pre_enter')#, self, self.page)

Builder.load_string("""
#:import NavBar uiux
#:import BoundedTextInput uiux.BoundedTextInput
#:import ActionListItem listitems.ActionListItem
#:import ListScreenItem listitems.ListScreenItem
#:import ActionListView listviews.ActionListView
#:import AccordionListView listviews.AccordionListView

<ListScreen>:
    name: 'List Screen'
    action_view: action_view_id
    accordion_view: accordion_view_id

    NavBar:
        id: navbar_id
        size_hint: 1, .0775
        pos_hint:{'top': 0.9648}

        BoxLayout:
            orientation: 'horizontal'
            size_hint: .9, .9
            pos_hint: {'center_x': .5, 'center_y': .5}

            Button_:
                font_size: 12
                size_hint: 0.2, 1
                text: '< Lists'
                on_press: root.on_lists()
            Label:
                text: root.page
                size_hint: 0.6, 1
                font_size: self.height*0.8
                font_name: 'Walkway Bold.ttf'
                color: app.white
            Button_:
                font_size: 12
                size_hint: 0.2, 1
                text: 'Archive >'

    ActionListView:
        id: action_view_id
        data: root.action_items
        args_converter: root._args_converter
        list_item: ActionListItem
        selection: root.selection
        top: navbar_id.y
        size_hint: 1, 0.401

    AccordionListView:
        id: accordion_view_id
        data: root.list_items
        args_converter: root._args_converter
        list_item: ListScreenItem
        selection: root.selection
        top: action_view_id.container.y
        size_hint: 1, 0.401

    FloatLayout:
        size_hint: 1, .086
        pos_hint: {'y': 0}
        canvas.before:
            Color:
                rgba: app.dark_blue
            Rectangle:
                size: self.size
                pos: self.pos

        BoxLayout:
            orientation: 'horizontal'
            spacing: 14
            size_hint: 0.9781, 0.7561
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}

            BoundedTextInput:
                id: textinput_id
                size_hint: 0.774, 1
                hint_text: 'Create New Task...'
                multiline: False
                on_text_validate: root.new_task(self, self.text)
            Button_:
                size_hint: 0.226, 1
                text: 'Add'
                on_press: root.new_task(textinput_id, textinput_id.text)

""")
