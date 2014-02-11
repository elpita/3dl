kv = '''
<ShaderTest>:
    canvas:
        Color:
            rgb: 0.1, 0.2, 0.3
        Rectangle:
            size: self.size
            pos: self.pos

    Button:
        text: 'foobar'
        size_hint: 0.5, 0.5
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

'''
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.graphics import RenderContext
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.app import App
from kivy.graphics import Fbo, Color, Rectangle

class FboTest(Widget):
    def __init__(self, **kwargs):
        super(FboTest, self).__init__(**kwargs)

        # first step is to create the fbo and use the fbo texture on other
        # rectangle

        with self.canvas:
            # create the fbo
            self.fbo = Fbo(size=(256, 256))

            # show our fbo on the widget in different size
            Color(1, 1, 1)
            Rectangle(size=(32, 32), texture=self.fbo.texture)
            Rectangle(pos=(32, 0), size=(64, 64), texture=self.fbo.texture)
            Rectangle(pos=(96, 0), size=(128, 128), texture=self.fbo.texture)

        # in the second step, you can draw whatever you want on the fbo
        with self.fbo:
            Color(1, 0, 0, .8)
            Rectangle(size=(256, 64))
            Color(0, 1, 0, .8)
            Rectangle(size=(64, 256))

class ShaderTest(Widget):
    #canvas = ObjectProperty(RenderContext(shader='blur.glsl'))

    def __init__(self, **kwargs):
        super(ShaderTest, self).__init__(**kwargs)
        self.canvas = RenderContext()
    #canvas = ObjectProperty(RenderContext(shader='blur.glsl'))

class ShaderTestApp(App):

    def build(self):
        return FboTest()

if __name__ == '__main__':
    #Builder.load_string(kv)
    ShaderTestApp().run()
