import socket
from typing import Generator

HOST = '127.0.0.1'
PORT = 3000

RESPONSE = b"""
        HTTP/1.1 200 OK
        Content-type: text/html; charset=utf-8
        Content-length: 15

        <h1>Hello!</h1>""".replace(b"\n", b"\r\n")

def iterate_lines(sock: socket.socket, bufsize: int = 16_384) ->\
        Generator[bytes, None, bytes]:
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




with socket.socket() as ssock:
    ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ssock.bind((HOST, PORT ,))
    ssock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = ssock.accept()
        with client_sock:
            for request_line in iterate_lines(client_sock):
                print(request_line)

            client_sock.sendall(RESPONSE)
            print(f"New connection from {client_addr}.")
