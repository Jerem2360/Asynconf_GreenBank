import pyglet

from . import vehicle

class Colors:
    BLACK = (0, 0, 0, 255)
    DARK_GRAY = (30, 30, 30, 255)
    GRAY = (100, 100, 100, 255)
    ALT_GRAY = (120, 120, 120, 255)
    WHITE = (255, 255, 255, 255)
    LIGHT_GRAY = (200, 200, 200, 255)
    RED = (255, 0, 0, 255)


class Widget:
    def collision_test(self, x, y): ...

    def on_mouse_motion(self, x, y, dx, dy): ...

    def on_mouse_press(self, x, y, button, modifiers): ...

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers): ...

    def on_text(self, text): ...

    def on_text_motion(self, motion): ...

    def on_text_motion_select(self, motion): ...

    def begin_focus(self, x, y): ...

    def end_focus(self, x, y): ...

    def write_char(self, char): ...

    def erase_char(self): ...

    def arrow_right(self): ...

    def arrow_left(self): ...

    def arrow_up(self): ...

    def arrow_down(self): ...

    @property
    def x(self): return 0

    @x.setter
    def x(self, value): ...

    @property
    def y(self): return 0

    @y.setter
    def y(self, value): ...

    @property
    def width(self): return 0

    @property
    def height(self): return 0

    @property
    def value(self): return ""


class TextInput(Widget):

    def __init__(self, root, x, y, width, font_name="Times New Roman", font_size=12, base_text=""):
        font = pyglet.font.load(font_name, font_size)
        height = font.ascent - font.descent

        self.bg = pyglet.graphics.Group(0)
        self.fg = pyglet.graphics.Group(1)
        self.root = root

        self._padding = 2
        self.rect = pyglet.shapes.Rectangle(x, y, width, height + 2 * self._padding, Colors.GRAY, self.root.fields_batch, self.bg)

        self.doc = pyglet.text.document.UnformattedDocument(base_text)
        self.doc.set_style(0, len(self.doc.text),
                           dict(
                               color=Colors.BLACK,
                               font_name=font_name,
                               font_size=font_size,
                           ))
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.doc, width - 2 * self._padding, height, False, batch=self.root.fields_batch, group=self.fg
        )
        self.layout.x = x + self._padding
        self.layout.y = y - font.descent + self._padding
        self.caret = pyglet.text.caret.Caret(self.layout, self.root.fields_batch, Colors.BLACK)
        self.caret.visible = False
        self.text_cursor = root.get_system_mouse_cursor('text')

    def collision_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.collision_test(x, y):
            self.root.set_mouse_cursor(self.text_cursor)
            return True
        self.root.set_mouse_cursor(None)
        return False

    def begin_focus(self, x, y):
        self.caret.visible = True

    def end_focus(self, x, y):
        self.caret.visible = False

    def arrow_left(self):
        if self.caret.position > 0:
            self.caret.position -= 1

    def arrow_right(self):
        if self.caret.position < (len(self.doc.text) - 1):
            self.caret.position += 1

    def write_char(self, char):
        self.layout.begin_update()
        if self.caret.position == len(self.doc.text):
            self.doc.text += char
        else:
            self.doc.insert_text(self.caret.position, char)
        self.caret.position += 1
        self.layout.end_update()

    def erase_char(self):
        if self.caret.position == 0:
            return
        self.layout.begin_update()
        self.doc.delete_text(self.caret.position - 1, self.caret.position)
        self.caret.position -= 1
        self.layout.end_update()

    @property
    def value(self):
        return self.doc.text

    @property
    def font(self):
        return self.doc.get_font()

    @property
    def x(self):
        assert self.layout.x == self.rect.x + self._padding
        return self.rect.x

    @x.setter
    def x(self, value):
        self.rect.x = value
        self.layout.x = value + self._padding

    @property
    def y(self):
        assert self.layout.y == self.rect.y + self._padding - self.font.descent
        return self.rect.y

    @y.setter
    def y(self, value):
        self.rect.y = value
        self.layout.y = value + self._padding - self.font.descent

    @property
    def width(self):
        return self.rect.width

    @property
    def height(self):
        return self.rect.height

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, value):
        self._padding = value
        self.layout.x = self.rect.x + value
        self.layout.y = self.rect.y + value - self.font.descent

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_text(self, text):
        self.caret.on_text(text)

    def on_text_motion(self, motion):
        self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        self.caret.on_text_motion_select(motion)


class DropDownList(Widget):
    def __init__(self, root, possibilities, x, y, width, font_name="Times New Roman", font_size=12):
        self.root = root
        self.labels = []
        self.rects = []
        self.focused = False
        self.padding = 2
        self.selected = -1
        self.owner = None

        self.bg = pyglet.graphics.Group(0)
        self.fg = pyglet.graphics.Group(1)

        font = pyglet.font.load(font_name, font_size)
        height = font.ascent - font.descent

        self.initial_label = pyglet.text.Label(
            "<Pas de selection>", font_name,
            font_size, color=Colors.BLACK,
            x=x + self.padding, y=y + self.padding,
            width=width - (2 * self.padding),
            height=height - (2 * self.padding),
            batch=root.fields_batch,
            group=self.fg
        )
        self.initial_label.visible = True
        self.initial_rect = pyglet.shapes.Rectangle(
            x, y, width, height, Colors.ALT_GRAY, root.fields_batch, self.bg
        )
        self.initial_rect.visible = True
        y += height + 2 * self.padding

        color = Colors.GRAY

        self.dropdown_bg = pyglet.graphics.Group(2)
        self.dropdown_fg = pyglet.graphics.Group(3)

        for possibility in possibilities:
            lab = pyglet.text.Label(
                possibility, font_name,
                font_size, color=Colors.BLACK,
                width=width - (2 * self.padding),
                height=height,
                batch=root.fields_batch, group=self.dropdown_fg
            )
            lab.x = x + self.padding
            lab.y = y + self.padding
            lab.visible = False
            self.labels.append(lab)
            rect = pyglet.shapes.Rectangle(
                x, y, width, height + (2 * self.padding), color, root.fields_batch, self.dropdown_bg
            )
            rect.visible = False
            self.rects.append(rect)
            y += height + 2 * self.padding
            if color == Colors.GRAY:
                color = Colors.ALT_GRAY
            else:
                color = Colors.GRAY

    def begin_focus(self, x, y):
        for rect in self.rects:
            rect.visible = True
        for lab in self.labels:
            lab.visible = True
        self.owner._title_label.visible = False
        self.focused = True

    def end_focus(self, x, y):
        for rect in self.rects:
            rect.visible = False
        for lab in self.labels:
            lab.visible = False
        for i in range(len(self.rects)):
            rect = self.rects[i]
            if (x, y) in rect:
                self.selected = i
                self.initial_label.begin_update()
                self.initial_label.text = self.labels[i].text
                self.initial_label.end_update()
                break

        self.focused = False
        self.owner._title_label.visible = True

    def collision_test(self, x, y):
        return self.x < x < self.x + self.initial_rect.width and \
            self.y < y < self.y + self.initial_rect.height

    @property
    def width(self):
        return self.initial_rect.width

    @property
    def height(self):
        if self.focused:
            return self.initial_rect.height * (len(self.rects) + 1)
        return self.initial_rect.height

    @property
    def x(self):
        return self.initial_rect.x

    @x.setter
    def x(self, value):
        self.initial_rect.x = value
        self.initial_label.x = value + self.padding
        for rect in self.rects:
            rect.x = value
        for lab in self.labels:
            lab.x = value + self.padding

    @property
    def y(self):
        return self.initial_rect.y

    @y.setter
    def y(self, value):
        self.initial_rect.y = value
        self.initial_label.y = value + self.padding
        for i in range(len(self.rects)):
            rect = self.rects[i]
            rect.y = self.initial_rect.y - (self.initial_rect.height * i)
        for i in range(len(self.labels)):
            lab = self.labels[i]
            lab.y = self.initial_rect.y - (self.initial_rect.height * i) + self.padding

    @property
    def value(self):
        if self.selected < 0:
            return None
        return self.labels[self.selected].text


class Button(Widget):
    def __init__(self, root, x, y, width, height, text, font_name="Times New Roman", font_size=12):
        self.padding = 5
        self.root = root
        self.bbg = pyglet.gui.Group(0)
        self.bg = pyglet.gui.Group(1)
        self.fg = pyglet.gui.Group(2)
        self.back_layer = pyglet.shapes.Rectangle(x, y, width, height, Colors.ALT_GRAY, root.fields_batch, self.bbg)
        self.front_layer = pyglet.shapes.Rectangle(
            x + self.padding, y + self.padding, width - 2 * self.padding,
            height - 2 * self.padding, Colors.GRAY, root.fields_batch, self.bg
        )

        lb_x = x + int(self.back_layer.width / 2)
        lb_y = y + int(self.back_layer.height / 2)

        self.label = pyglet.text.Label(
            text, font_name, font_size, color=Colors.BLACK, x=lb_x, y=lb_y,
            anchor_x='center', anchor_y='center', batch=root.fields_batch, group=self.fg
        )

    def collision_test(self, x, y):
        return ((self.back_layer.x < x < self.back_layer.x + self.back_layer.width) and
                (self.back_layer.y < y < self.back_layer.y + self.back_layer.height))

    def on_mouse_motion(self, x, y, dx, dy):
        if self.collision_test(x, y):
            self.back_layer.color = Colors.GRAY
            self.front_layer.color = Colors.ALT_GRAY
        else:
            self.back_layer.color = Colors.ALT_GRAY
            self.front_layer.color = Colors.GRAY

    def on_mouse_press(self, x, y, button, modifiers):
        if button in (pyglet.window.mouse.LEFT, pyglet.window.mouse.RIGHT) and self.collision_test(x, y):
            self.root.calculate_result()



class ParameterSelector:
    def __init__(self, widget: Widget, root, fsize):

        self._widget = widget
        root.widgets.append(self._widget)
        self._error_msg = pyglet.text.Label(
            "", font_size=int(fsize * 2 / 3), color=Colors.RED, x=self._widget.x, y=self._widget.y - self._widget.height * 0.65, width=self._widget.width,
            batch=root.fields_batch
        )
        self._title_label = None

    def set_error(self, msg):
        self._error_msg.text = msg

    def clear_error(self):
        self.set_error("")

    @property
    def error_message(self):
        if not self._error_msg.text:
            return None
        return self._error_msg.text

    @classmethod
    def make_text_input(cls, root, title, x, y, width, font_name="Times New Roman", font_size=12, base_text=""):
        fnt = pyglet.font.load(font_name, font_size)
        height = fnt.ascent - (2 * fnt.descent)
        title_lb = pyglet.text.Label(
            title, font_name, int(font_size * 2 / 3), color=Colors.WHITE, x=x, y=y + height / 2, width=width, multiline=True,
            batch=root.fields_batch
        )
        res = cls(
            TextInput(root, x, y - height * 1.3, width, font_name, font_size, base_text), root, font_size
        )
        res._title_label = title_lb
        return res

    @classmethod
    def make_dropdown_list(cls, root, title, possibilities, x, y, width, font_name="Times New Roman", font_size=12):
        fnt = pyglet.font.load(font_name, font_size)
        height = fnt.ascent - (2 * fnt.descent)
        title_lb = pyglet.text.Label(
            title, font_name, int(font_size * 2 / 3), color=Colors.WHITE, x=x, y=y, width=width, batch=root.fields_batch
        )
        res = cls(
            DropDownList(root, possibilities, x, y - height * 1.3, width, font_name, font_size), root, font_size
        )
        res._widget.owner = res
        res._title_label = title_lb
        return res

    @property
    def x(self):
        return self._widget.x

    @x.setter
    def x(self, value):
        self._widget.x = value

    @property
    def y(self):
        return self._widget.y

    @y.setter
    def y(self, value):
        self._widget.y = value

    @property
    def value(self):
        return self._widget.value

    @property
    def width(self):
        return self._widget.width

    @property
    def height(self):
        return self._widget.height


class Root(pyglet.window.Window):
    def __init__(self):
        super().__init__(1024, 510, caption="Calculateur d'emprunte écologique pour voitures")
        self.widgets: list[Widget] = []
        self._focused = -1
        self.fields_batch = pyglet.graphics.Batch()
        self.result_batch = pyglet.graphics.Batch()
        self.current_batch = self.fields_batch
        x = 75
        y = 350
        self.calc_button = Button(self, 452, 50, 120, 50, "Calculer", font_size=20)

        res_lb_x = int(self.width / 2)
        res_lb_y = int(self.height / 2)

        self.result_label = pyglet.text.Label(
            "", font_name="Times New Roman", font_size=20, color=Colors.WHITE, x=res_lb_x, y=res_lb_y,
            anchor_x='center', anchor_y='center', batch=self.result_batch
        )

        self._selectors = {
            'energy': ParameterSelector.make_dropdown_list(
                self, "Quel est le type d'énergie utilisé par le véhicule ?", [
                    'Essence',
                    'Electrique',
                    'Gaz',
                    'Diesel',
                    'Hybride'
                ], x, y, 400, font_size=20
            ),
            'kilometers': ParameterSelector.make_text_input(
                self, "Combien de kilomètres comptez-vous rouler en moyenne chaque année ?", x, y - 100, 400, font_size=20
            ),
            'car_type': ParameterSelector.make_dropdown_list(
                self, "Quel est le type de voiture ?", [
                    'Citadine',
                    'Cabriolet',
                    'Berline',
                    'SUV / 4x4',
                ], x, y - 200, 400, font_size=20
            ),
            'year': ParameterSelector.make_text_input(
                self, "De quand date votre voiture ?", x + 500, y, 400, font_size=20
            ),
            'passenger_count': ParameterSelector.make_text_input(
                self, "Combien de personnes vivent dans votre foyer ?", x + 500, y - 100, 400, font_size=20
            )
        }

    def validate_energy(self, energy):
        if not energy:
            self.error('energy', "Veuillez sélectionner une valeur")
            return False
        return True

    def validate_kilometers(self, kilometers):
        if not kilometers:
            self.error('kilometers', "Veuillez entrer un nombre entre 5 000 et 30 000")
            return False
        if not kilometers.isnumeric():
            self.error('kilometers', "Veuillez entrer un nombre entre 5 000 et 30 000")
            return False
        num = int(kilometers)
        if num < 5000 or num > 30000:
            self.error('kilometers', "Veuillez entrer un nombre entre 5 000 et 30 000")
            return False
        return True

    def validate_car_type(self, car_type):
        if not car_type:
            self.error('car_type', "Veuiller sélectionner une valeur")
            return False
        return True

    def validate_year(self, year):
        if not year:
            self.error('year', "Veuillez entrer une année supérieure à 1960")
            return False
        if not year.isnumeric():
            self.error('year', "Veuillez entrer une année supérieure à 1960")
            return False
        num = int(year)
        if num < 1960:
            self.error('year', "Veuillez entrer une année supérieure à 1960")
            return False
        return True

    def validate_passengers(self, npassengers):
        if not npassengers:
            self.error('passenger_count', "Veuillez entrer un nombre entre 1 et 4")
            return False
        if not npassengers.isnumeric():
            self.error('passenger_count', "Veuillez entrer un nombre entre 1 et 4")
            return False
        num = int(npassengers)
        if num < 1 or num > 4:
            self.error('passenger_count', "Veuillez entrer un nombre entre 1 et 4")
            return False
        return True

    def calculate_result(self):
        for s in self._selectors.values():
            s.clear_error()

        ok = True
        in_energy = self._selectors['energy'].value
        ok &= self.validate_energy(in_energy)

        in_kilometers = self._selectors['kilometers'].value.replace(' ', '')
        ok &= self.validate_kilometers(in_kilometers)

        in_car_type = self._selectors['car_type'].value
        ok &= self.validate_car_type(in_car_type)

        in_year = self._selectors['year'].value.replace(' ', '')
        ok &= self.validate_year(in_year)

        in_passengers = self._selectors['passenger_count'].value.replace(' ', '')
        ok &= self.validate_passengers(in_passengers)

        if not ok:
            return

        v = vehicle.Vehicle(in_energy, int(in_kilometers), in_car_type, int(in_year), int(in_passengers))
        result = v.calculate_borrowing_rate()

        self.result_label.begin_update()
        self.result_label.text = f"Votre taux d'emprunt est de {result}%."
        self.result_label.end_update()

        self.current_batch = self.result_batch

    def error(self, selector, message):
        self._selectors[selector].set_error(message)

    def on_draw(self):
        self.clear()
        rect = pyglet.shapes.Rectangle(self.screen.x, self.screen.y, self.width, self.height, Colors.DARK_GRAY)
        rect.draw()
        self.current_batch.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self.calc_button.on_mouse_motion(x, y, dx, dy)
        for w in self.widgets:
            if w.on_mouse_motion(x, y, dx, dy):
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button not in (pyglet.window.mouse.LEFT, pyglet.window.mouse.RIGHT):
            return
        for i in range(len(self.widgets)):
            w = self.widgets[i]
            if w.collision_test(x, y):
                w.begin_focus(x, y)
                self._focused = i
                break
            if self._focused >= 0:
                self.widgets[self._focused].end_focus(x, y)
                self._focused = -1
        self.calc_button.on_mouse_press(x, y, button, modifiers)

    def on_key_press(self, symbol, modifiers):
        if self._focused < 0:
            return
        w = self.widgets[self._focused]
        if symbol == pyglet.window.key.BACKSPACE:
            w.erase_char()
            return
        if symbol == pyglet.window.key.LEFT:
            w.arrow_left()
            return
        if symbol == pyglet.window.key.RIGHT:
            w.arrow_right()
            return
        if symbol == pyglet.window.key.UP:
            w.arrow_up()
            return
        if symbol == pyglet.window.key.DOWN:
            w.arrow_down()
            return

        if not modifiers:
            w.write_char(symbol)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._focused < 0:
            return
        self.widgets[self._focused].on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_text(self, text):
        if self._focused < 0:
            return
        self.widgets[self._focused].on_text(text)

    def on_text_motion(self, motion):
        if self._focused < 0:
            return
        self.widgets[self._focused].on_text_motion(motion)

    def on_text_motion_select(self, motion):
        if self._focused < 0:
            return
        self.widgets[self._focused].on_text_motion_select(motion)


def run():
    pyglet.app.run()

