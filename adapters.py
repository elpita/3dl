from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, NumericProperty, ListProperty, OptionProperty, DictProperty, BooleanProperty

class ListViewAdapter(object):
    data = ListProperty([])
    list_item = ObjectProperty(None)
    args_converter = ObjectProperty(None)
    selection = ListProperty([])
    selection_mode = OptionProperty('single', options=('None', 'single'))
    cached_views = DictProperty({})

    def __init__(self, **kwargs):
        self.register_event_type('on_selection_change')
        super(ListViewAdapter, self).__init__(**kwargs)

    def on_data(self, instance, value):
        instance.delete_cache()
        selection = instance.selection

        if len(selection) > 0:
            selection[:] = []

    def on_selection(self, instance, value):
        instance.dispatch('on_selection_change')

    def delete_cache(self, **args):
        self.cached_views.clear()

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        data = self.data

        if (0 <= index < self.get_count()):
            return data[index]

    def get_view(self, index):
        cached_views = self.cached_views

        if index in cached_views:
            return cached_views[index]
        else:
            item_view = self.create_view(index)

            if item_view:
                cached_views[index] = item_view

            return item_view

    def create_view(self, index):
        item = self.get_data_item(index)

        if item is not None:
            item_args = self.args_converter(index, item)
            item_args['index'] = index
            view_instance = self.list_item(**item_args)

            if self.selection_mode <> 'None':
                view_instance.bind(on_release=self.handle_selection)

            return view_instance

    def deselect_all(self, *args):
        selection = self.selection[:]

        for each_view in xrange(len(selection)):
            selection.pop().is_selected = False

    def handle_selection(self, view, hold_dispatch=False, *args):
        if view not in self.selection:
            
            if self.selection_mode == 'single':
                self.deselect_all()
                self.select_item_view(view)

        else:
            self.deselect_item_view(view)

        if not hold_dispatch:
            self.dispatch('on_selection_change')

    def select_item_view(self, view):
        view.is_selected = True
        self.selection.append(view)

    def deselect_item_view(self, view):
        view.is_selected = False
        self.selection.remove(view)

    def on_selection_change(self, *args):
        pass
        
