import socket

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, 80))
        req = "GET {} HTTP/1.0\r\n".format(self.path)
        req += "Host: {}\r\n".format(self.host)
        req += "\r\n"
        s.send(req.encode("utf8"))

        resp = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = resp.readline()
        version,stataus, explanation = statusline.split(" ", 2)

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

def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))
