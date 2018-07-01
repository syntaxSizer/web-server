import socket
import typing

HOST = '127.0.0.1'
PORT = 3000

RESPONSE = b"""
        HTTP/1.1 200 OK
        Content-type: text/html; charset=utf-8
        Content-length: 15

        <h1>Hello!</h1>""".replace(b"\n", b"\r\n")

def read_lines(sock: socket.socket, bufsize: int = 16_384) ->\
        typing.Generator[bytes, None, bytes]:
    """
        Given a socket, read all the individual CRLF-separated lines
        and yield each one until an empty one is found.  Returns the
        remainder after the empty line.
    """
    buff = b""
    while True:
        data = sock.recv(bufsize)
        if not data:
            return b""

        buff += data
        while True:
            try:
                i = buff.index(b"\r\n")
                line, buff = buff[:i], buff[i+2:]
                if not line:
                    return buff
                yield line
            except IndexError:
                break


class Request(typing.NamedTuple):
    method: str
    path: str
    headers: typing.Mapping[str, str]

    @classmethod
    def parse(cls, sock: socket.socket) -> "Request":
        """
            Read and parse the request from a socket object.
            Raises: ValueError When the request cannot be parsed.
        """
        lines = read_lines(sock)
        try:
            request_line = next(lines).decode("ascii")
        except StopIteration:
            raise ValueError("Request line missing.")

        try:
            method, path, _ = request_line.split(" ")
        except ValueError:
            raise ValueError(f"Malformed request line {request_line!r}.")
        headers = {}
        for line in lines:
            try:
                name, _, value = line.decode("ascii").partition(":")
                headers[name.lower()] = value.lstrip()
            except ValueError:
                raise ValueError(f"Malformed header line {line!r}.")
            return cls(method=method.upper(), path=path, headers=headers)


with socket.socket() as ssock:
    ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ssock.bind((HOST, PORT ,))
    ssock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = ssock.accept()
        with client_sock:
            request = Request.parse(sock=client_sock)
            client_sock.sendall(RESPONSE)
            print(f"New connection from {client_addr}.")
