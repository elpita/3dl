'''
Created on Jul 23, 2013

@author: Divine
'''
from uiux import Screen_
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.properties import ObjectProperty, ListProperty

class ConfigPanel(Widget):

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super(ConfigPanel, self).on_touch_down(touch)
        else:
            widget = self.parent
            widget._anim = Animation(x=0, y=0, duration=0.2)
            widget._anim.bind(on_complete=lambda *_: widget.remove_widget(self))
            widget._anim.start(widget)
            widget.polestar = None
            return True

class PagesScreen(Screen_):
    pages = ListProperty([])
    list_view = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_root_directory')
        self.register_event_type('on_settings')
        super(PagesScreen, self).__init__(**kwargs)

    def on_root_directory(self, *args):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       SELECT DISTINCT page_number, page
                       FROM notebook
                       ORDER BY page_number
                       """)
        self.pages = cursor.fetchall()

    def on_status_bar(self, *args):
        self.list_view.scroll_to()

    def on_leave(self, *args):
        cursor = self.root_directory.cursor()
        screen = self.manager.current_screen
        cursor.execute("""
                       UPDATE notebook
                       SET bookmark=1
                       WHERE page=?
                       """,
                       (screen.page,))

    def on_settings(self, *args):
        if not self.polestar:
            self.polestar = ConfigPanel()
            self.add_widget(self.polestar)
            self._anim = Animation(x=self.size[0]*0.75, duration=0.2)
            self._anim.start(self)

    def _args_converter(self, row_index, an_obj):
        dict = {'index': an_obj[0],
                'text': an_obj[1],
                'is_selected': False,
                'size_hint_y': None,
                'screen': self}
        return dict

    def new_page(self, instance, text):
        text = text.lstrip()

        if text:
            cursor = self.root_directory.cursor()
            num = len(self.pages)
            cursor.execute("""
                           INSERT INTO notebook(page_number, page)
                           VALUES(?, ?)
                           """,
                           (num, text))
            #cursor.execute('commit')
            self.dispatch('on_root_directory')

        instance.text = ''
        instance.focus = False

    def on_delete(self, instance):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       DELETE FROM notebook
                       WHERE page_number=? AND page=?
                       """,
                       (instance.index, instance.text))
        self.dispatch('on_root_directory')
        self.polestar = None

Builder.load_string("""
#:import NavBar uiux
#:import Button_ uiux.Button_
#:import DNDListView listviews.DNDListView
#:import BoundedTextInput uiux.BoundedTextInput
#:import PagesScreenItem listitems.PagesScreenItem

<ConfigPanel>:
    size_hint: 0.75, 1
    pos_hint: {'right':0, 'y':0}
    canvas.before:
        Color:
            rgb: app.smoke_white
        Rectangle:
            pos: self.pos
            size: self.size

<PagesScreen>:
    name: 'Pages Screen'
    list_view: list_view_id

    NavBar:
        id: navbar_id
        size_hint: 1, .0775
        pos_hint:{'top': 0.9648}

        Label:
            text: "Lists"
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            font_size: self.height*0.8
            font_name: 'Walkway Bold.ttf'
            color: app.white
        Button_:
            font_size: self.height*0.8
            font_name: 'breezi_font-webfont.ttf'
            size_hint: 0.09375, .682
            pos_hint: {'center_x': 0.08, 'center_y': 0.5}
            text: 'E'
            on_press: root.dispatch('on_settings')
            
    DNDListView:
        id: list_view_id
        data: root.pages
        selection_mode: 'None'
        list_item: PagesScreenItem
        args_converter: root._args_converter
        size_hint: 1, .8
        top: navbar_id.y

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
                hint_text: 'Create New List...'
                multiline: False
                on_text_validate: root.new_page(self, self.text)
            Button_:
                size_hint: 0.226, 1
                text: 'Add'
                on_press: root.new_page(textinput_id, textinput_id.text)
        
            
""")


