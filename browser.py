import tkinter
from url import URL
from parser import HTMLParser
from layout import DocumentLayout, WIDTH, HEIGHT, VSTEP, paint_tree

SCROLL_STEP = 100

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
        max_y = max(self.document.height + 2*VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll, self.canvas)

    def load(self, url):
        body = url.request()
        self.nodes = HTMLParser(body).parse()
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()

if __name__ == "__main__":
    import sys
    path = "file://suspense.txt"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    Browser().load(URL(path))
    tkinter.mainloop()
