import tkinter
import tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
FONTS = {}

def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)

def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight,
            slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

class Text:
    def __repr__(self):
        return repr(self.text)

    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent

class Element:
    def __repr__(self):
        return "<" + self.tag + ">"

    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

class Layout:
    def __init__(self, tree):
        self.display_list = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.recurse(tree)
        print_tree(tree)
        self.flush()

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4

    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def flush(self):
        if not self.line: return

        max_ascent = max([font.metrics("ascent")
            for x, word, font in self.line])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        max_descent = max([font.metrics("descent")
            for x, word, font in self.line])

        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok == "br":
            self.flush()
        elif tok == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def word(self, word):
        font = get_font(
            self.size,
            self.weight,
            self.style)

        w = font.measure(word)
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()
            self.cursor_x = HSTEP
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
