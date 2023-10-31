import pyglet

from . import vehicle

class Colors:
    """
    List of colors we will need, in the (R, G, B, A) format.
    """
    BLACK = (0, 0, 0, 255)
    DARK_GRAY = (30, 30, 30, 255)
    GRAY = (100, 100, 100, 255)
    ALT_GRAY = (120, 120, 120, 255)
    WHITE = (255, 255, 255, 255)
    LIGHT_GRAY = (200, 200, 200, 255)
    RED = (255, 0, 0, 255)


class Widget:
    """
    Base class describing a simple gui element with which the user can interact.
    """
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
    """
    This class describes fields in which the user can write some text.
    """

    def __init__(self, root, x, y, width, font_name="Times New Roman", font_size=12, base_text=""):
        font = pyglet.font.load(font_name, font_size)
        height = font.ascent - font.descent

        self.bg = pyglet.graphics.Group(0)
        self.fg = pyglet.graphics.Group(1)
        self.root = root

        self._padding = 2
        # this is the background of our text input:
        self.rect = pyglet.shapes.Rectangle(x, y, width, height + 2 * self._padding, Colors.GRAY, self.root.fields_batch, self.bg)

        # the following initializes the elements required to accept input text from the user:
        # the document stores the actual text:
        self.doc = pyglet.text.document.UnformattedDocument(base_text)
        self.doc.set_style(0, len(self.doc.text),
                           dict(
                               color=Colors.BLACK,
                               font_name=font_name,
                               font_size=font_size,
                           ))
        # the layout handles everything about interacting with the user, except the caret:
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.doc, width - 2 * self._padding, height, False, batch=self.root.fields_batch, group=self.fg
        )
        self.layout.x = x + self._padding
        self.layout.y = y - font.descent + self._padding

        # the caret shows where the user is located in the text:
        self.caret = pyglet.text.caret.Caret(self.layout, self.root.fields_batch, Colors.BLACK)
        self.caret.visible = False
        self.text_cursor = root.get_system_mouse_cursor('text')

    def collision_test(self, x, y):
        """
        Test if the specified coordinates are contained within this widget's rectangle.
        """
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)

    def on_mouse_motion(self, x, y, dx, dy):
        """
        dispatched each time the mouse moves.
        """
        # if the mouse is inside our text box, set the cursor to a text cursor, otherwise put it to default:
        if self.collision_test(x, y):
            self.root.set_mouse_cursor(self.text_cursor)
            return True
        self.root.set_mouse_cursor(None)
        return False

    def begin_focus(self, x, y):
        """
        Called when our widget acquires the focus
        """
        # we show the caret only when we have the focus:
        self.caret.visible = True

    def end_focus(self, x, y):
        """
        Called when our widget loses the focus
        """
        # same as above:
        self.caret.visible = False

    @property
    def value(self):
        """
        What the user entered in the text input.
        :return:
        """
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

    # the following events are dispatched to our cursor so that the user can
    # interact with our text input.

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """
        Called each time the mouse drags something.
        """
        # simply dispatch the event to our cursor:
        self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_text(self, text):
        # simply dispatch the event to our cursor:
        self.caret.on_text(text)

    def on_text_motion(self, motion):
        # simply dispatch the event to our cursor:
        self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        # simply dispatch the event to our cursor:
        self.caret.on_text_motion_select(motion)


class DropDownList(Widget):
    """
    This class describes a widget that allows the user to select a value
    from a list of fixed possible values.
    """
    def __init__(self, root, possibilities, x, y, width, font_name="Times New Roman", font_size=12):
        # This widget is composed of one base component and one
        # more for each one of its possible values.
        # Each 'component' is composed of a name displayed with
        # a label on the foreground, and a rectangle on the
        # background.
        # The base component is always displayed on the screen,
        # and shows which choice is currently selected.
        # The rest of the components only show when the widget
        # has the focus.
        # When the user clicks the base component the first time,
        # the widget acquires the focus.
        # Then, if the user clicks outside the base component,
        # the widget loses the focus. If the mouse happened to
        # be on one of the choice components, the corresponding
        # choice is selected.

        self.root = root
        self.labels = []  # list of all our labels: one per possible value
        self.rects = []  # list of all our rectangles: one per possible value
        self.focused = False
        self.padding = 2
        self.selected = -1
        self.owner = None

        self.bg = pyglet.graphics.Group(0)
        self.fg = pyglet.graphics.Group(1)

        font = pyglet.font.load(font_name, font_size)
        height = font.ascent - font.descent

        # the 'base component''s label:
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
        # the 'base component''s background rectangle:
        self.initial_rect = pyglet.shapes.Rectangle(
            x, y, width, height, Colors.ALT_GRAY, root.fields_batch, self.bg
        )
        self.initial_rect.visible = True
        y += height + 2 * self.padding

        color = Colors.GRAY

        # initialization of a label and a background rectangle for every choice element.
        # these are invisible by default, but are made visible when the widget has the focus:
        self.dropdown_bg = pyglet.graphics.Group(2)
        self.dropdown_fg = pyglet.graphics.Group(3)

        for possibility in possibilities:

            # label:
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
            # background rectangle:
            rect = pyglet.shapes.Rectangle(
                x, y, width, height + (2 * self.padding), color, root.fields_batch, self.dropdown_bg
            )
            rect.visible = False
            self.rects.append(rect)
            y += height + 2 * self.padding
            # neighbor choice elements have a slightly different color to help differentiate them:
            if color == Colors.GRAY:
                color = Colors.ALT_GRAY
            else:
                color = Colors.GRAY

    def begin_focus(self, x, y):
        # make the choice elements visible when we acquire the focus:
        for rect in self.rects:
            rect.visible = True
        for lab in self.labels:
            lab.visible = True
        self.focused = True

    def end_focus(self, x, y):
        # make the choice elements invisible when we lose the focus:
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
        """
        The choice that is currently selected as a string
        """
        if self.selected < 0:
            return None
        return self.labels[self.selected].text


class Button(Widget):
    """
    Describes a button that can be clicked by the user. This class is specifically designed to
    initiate the calculation process when the button is clicked.
    A button is composed of one large rectangle at the back and one smaller rectangle at the front,
    as well as a text label.
    The usage of the two rectangles creates a small perspective effect.
    """
    def __init__(self, root, x, y, width, height, text, font_name="Times New Roman", font_size=12):
        self.padding = 5
        self.root = root
        # group for the larger rectangle:
        self.bbg = pyglet.gui.Group(0)
        # group for the smaller rectangle:
        self.bg = pyglet.gui.Group(1)
        # group for the label text:
        self.fg = pyglet.gui.Group(2)

        # larger rectangle is at the back:
        self.back_layer = pyglet.shapes.Rectangle(x, y, width, height, Colors.ALT_GRAY, root.fields_batch, self.bbg)
        # smaller rectangle is at the front, centered on the larger one:
        self.front_layer = pyglet.shapes.Rectangle(
            x + self.padding, y + self.padding, width - 2 * self.padding,
            height - 2 * self.padding, Colors.GRAY, root.fields_batch, self.bg
        )

        lb_x = x + int(self.back_layer.width / 2)
        lb_y = y + int(self.back_layer.height / 2)

        # label text is in front of all our rectangles, centered on them.
        self.label = pyglet.text.Label(
            text, font_name, font_size, color=Colors.BLACK, x=lb_x, y=lb_y,
            anchor_x='center', anchor_y='center', batch=root.fields_batch, group=self.fg
        )

    def collision_test(self, x, y):
        return ((self.back_layer.x < x < self.back_layer.x + self.back_layer.width) and
                (self.back_layer.y < y < self.back_layer.y + self.back_layer.height))

    def on_mouse_motion(self, x, y, dx, dy):
        # we invert the colors of our two rectangles when hovered be the
        # mouse to create a nice visual effect:
        if self.collision_test(x, y):
            self.back_layer.color = Colors.GRAY
            self.front_layer.color = Colors.ALT_GRAY
        else:
            self.back_layer.color = Colors.ALT_GRAY
            self.front_layer.color = Colors.GRAY

    def on_mouse_press(self, x, y, button, modifiers):
        """
        This event is called each time the user clicks on the mouse.
        """
        if button in (pyglet.window.mouse.LEFT, pyglet.window.mouse.RIGHT) and self.collision_test(x, y):
            self.root.calculate_result()



class ParameterSelector:
    """
    Generic class for a widget that requires the user to give a value as input
    to the calculation process. Can either contain a drop-down list or a text input.
    """
    def __init__(self, widget: Widget, root, fsize):

        self._widget = widget
        root.widgets.append(self._widget)
        self._error_msg = pyglet.text.Label(
            "", font_size=int(fsize * 2 / 3), color=Colors.RED, x=self._widget.x, y=self._widget.y - self._widget.height * 0.65, width=self._widget.width,
            batch=root.fields_batch
        )
        self._title_label = None

    def set_error(self, msg):
        """
        Set the error message for this parameter selector.
        """
        self._error_msg.text = msg

    def clear_error(self):
        """
        Clear the error message for this parameter selector.
        """
        self.set_error("")

    @property
    def error_message(self):
        """
        The error message contained by this parameter selector.
        :return:
        """
        if not self._error_msg.text:
            return None
        return self._error_msg.text

    @classmethod
    def make_text_input(cls, root, title, x, y, width, font_name="Times New Roman", font_size=12, base_text=""):
        """
        Create and return a new parameter selector that uses a TextInput.
        """
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
        """
        Create and return a new parameter selector that uses a DropDownList.
        """
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
        """
        The value entered by the user as a string.
        """
        return self._widget.value

    @property
    def width(self):
        return self._widget.width

    @property
    def height(self):
        return self._widget.height


class Root(pyglet.window.Window):
    """
    The root window of our application.

    This contains one ParameterSelector per option to provide to the calculation process,
    as well as a 'Calculate' button to actually start the calculation.
    """
    def __init__(self):
        super().__init__(1024, 510, caption="Calculateur d'emprunte écologique pour voitures")
        self.widgets: list[Widget] = []
        self._focused = -1
        self.fields_batch = pyglet.graphics.Batch()
        self.result_batch = pyglet.graphics.Batch()
        self.current_batch = self.fields_batch
        x = 75
        y = 350
        # the 'calculate' button:
        self.calc_button = Button(self, 452, 50, 120, 50, "Calculer", font_size=20)

        # the label that will display the result once the calculation is done:
        res_lb_x = int(self.width / 2)
        res_lb_y = int(self.height / 2)

        self.result_label = pyglet.text.Label(
            "", font_name="Times New Roman", font_size=20, color=Colors.WHITE, x=res_lb_x, y=res_lb_y,
            anchor_x='center', anchor_y='center', batch=self.result_batch
        )

        self._selectors = {
            # our selector for the energy type parameter:
            'energy': ParameterSelector.make_dropdown_list(
                self, "Quel est le type d'énergie utilisé par le véhicule ?", [
                    'Essence',
                    'Electrique',
                    'Gaz',
                    'Diesel',
                    'Hybride'
                ], x, y, 400, font_size=20
            ),
            # selector for the number of kilometers:
            'kilometers': ParameterSelector.make_text_input(
                self, "Combien de kilomètres comptez-vous rouler en moyenne chaque année ?", x, y - 120, 400, font_size=20
            ),
            # selector for the car type:
            'car_type': ParameterSelector.make_dropdown_list(
                self, "Quel est le type de voiture ?", [
                    'Citadine',
                    'Cabriolet',
                    'Berline',
                    'SUV / 4x4',
                ], x, y - 240, 400, font_size=20
            ),
            # selector for the year of the car:
            'year': ParameterSelector.make_text_input(
                self, "De quand date votre voiture ?", x + 500, y, 400, font_size=20
            ),
            # selector for the number of passengers:
            'passenger_count': ParameterSelector.make_text_input(
                self, "Combien de personnes seront dans le véhicule à la fois en moyenne ?", x + 500, y - 120, 400, font_size=20
            )
        }

    # the next few methods (validate_*) return whether the corresponding
    # parameter is valid. If not, they set the selector's error message
    # appropriately.

    def validate_energy(self, energy):
        """
        Check if the energy parameter is valid
        """
        if not energy:
            self.error('energy', "Veuillez sélectionner une valeur")
            return False
        return True

    def validate_kilometers(self, kilometers):
        """
        Check if the kilometers parameter is valid
        """
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
        """
        Check if the car type parameter is valid
        """
        if not car_type:
            self.error('car_type', "Veuiller sélectionner une valeur")
            return False
        return True

    def validate_year(self, year):
        """
        Check if the year is valid
        """
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
        """
        Check if the number of passengers is valid
        """
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
        """
        Calculates the borrowing rate if all the parameters are valid.
        If so, empties the screen and displays a label showing the
        result of the calculation.
        """
        # clear the errors of all the selectors so the ones
        # that no longer have en error no longer show an error
        for s in self._selectors.values():
            s.clear_error()

        # successively check all the parameters.
        # we check all parameters even if one was already
        # found incorrect so all the errors can be
        # displayed at once.
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

        # at least one parameter is wrong ? OK, then don't do the calculation.
        if not ok:
            return

        # query the actual calculation:
        v = vehicle.Vehicle(in_energy, int(in_kilometers), in_car_type, int(in_year), int(in_passengers))
        result = v.calculate_borrowing_rate()

        # put the result inside our label:
        self.result_label.begin_update()
        self.result_label.text = f"Votre taux d'emprunt est de {result}%."
        self.result_label.end_update()

        # switch to the appropriate batch:
        self.current_batch = self.result_batch

    def error(self, selector, message):
        """
        Shows the provided error in the provided selector.
        """
        self._selectors[selector].set_error(message)

    def on_draw(self):
        """
        Draw the current batch to our window.
        """
        # first, clear the window.
        self.clear()
        # then, draw its background color as a rectangle:
        rect = pyglet.shapes.Rectangle(self.screen.x, self.screen.y, self.width, self.height, Colors.DARK_GRAY)
        rect.draw()
        self.current_batch.draw()  # draw the current batch.

    def on_mouse_motion(self, x, y, dx, dy):
        # dispatch the event to all our child widgets:
        self.calc_button.on_mouse_motion(x, y, dx, dy)
        for w in self.widgets:
            if w.on_mouse_motion(x, y, dx, dy):
                break

    def on_mouse_press(self, x, y, button, modifiers):
        # don't dispatch if the mouse button is not left of right:
        if button not in (pyglet.window.mouse.LEFT, pyglet.window.mouse.RIGHT):
            return
        # Widgets acquire the focus when they are clicked, and
        # they don't already have the focus. They lose the focus
        # if they have the focus and the user clicks somewhere else.
        for i in range(len(self.widgets)):
            w = self.widgets[i]
            if w.collision_test(x, y) and self._focused != i:
                w.begin_focus(x, y)
                self._focused = i
                break
            if self._focused >= 0:
                self.widgets[self._focused].end_focus(x, y)
                self._focused = -1

        # dispatch the event to our 'calculate' button:
        self.calc_button.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        # dispatch the event to the widget that has the focus, if any:
        if self._focused < 0:
            return
        self.widgets[self._focused].on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_text(self, text):
        # dispatch the event to the widget that has the focus, if any:
        if self._focused < 0:
            return
        self.widgets[self._focused].on_text(text)

    def on_text_motion(self, motion):
        # dispatch the event to the widget that has the focus, if any:
        if self._focused < 0:
            return
        self.widgets[self._focused].on_text_motion(motion)

    def on_text_motion_select(self, motion):
        # dispatch the event to the widget that has the focus, if any:
        if self._focused < 0:
            return
        self.widgets[self._focused].on_text_motion_select(motion)


def run():
    pyglet.app.run()

