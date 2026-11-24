import socket
import ssl

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
