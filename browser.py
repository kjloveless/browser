import socket
import ssl
import tkinter
import tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
FONTS = {}

def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)

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

    def __init__(self, tag, parent):
        self.tag = tag
        self.children = []
        self.parent = parent

class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished  = []

    def add_text(self, text):
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, parent)
            self.unfinished.append(node)

    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        for tok in tokens:
            self.token(tok)
        self.flush()

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
        elif tok == "i":
            self.style = "italic"
        elif tok == "/i":
            self.style = "roman"
        elif tok == "b":
            self.weight = "bold"
        elif tok == "/b":
            self.weight = "normal"
        elif tok == "small":
            self.size -= 2
        elif tok == "/small":
            self.size += 2
        elif tok == "big":
            self.size += 4
        elif tok == "/big":
            self.size -= 4
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

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.draw()

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, f in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=f, anchor='nw')

    def load(self, url):
        body = url.request()
        tokens = HTMLParser(body).parse()
        self.display_list = Layout(tokens).display_list
        self.draw()

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        if self.scheme == "file":
            file = open(self.host, "r")
            content = file.read()
            file.close()
            return content

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        req = "GET {} HTTP/1.1\r\n".format(self.path)
        req += "Host: {}\r\n".format(self.host)
        req += "Connection: close\r\n"
        req += "User-Agent: aurora\r\n"
        req += "\r\n"
        s.send(req.encode("utf8"))

        resp = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = resp.readline()
        version, status, explanation = statusline.split(" ", 2)

        resp_headers = {}
        while True:
            line = resp.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            resp_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in resp_headers
        assert "content-encoding" not in resp_headers

        content = resp.read()
        s.close()
        return content

def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight,
            slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

if __name__ == "__main__":
    import sys
    path = "file://suspense.txt"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    Browser().load(URL(path))
    tkinter.mainloop()
