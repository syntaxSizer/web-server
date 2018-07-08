import mimetypes
import os
import socket
import typing

SERVER_ROOT = os.path.abspath('')
HOST = '127.0.0.1'
PORT = 3000

RESPONSES = {
        '200' : b'''
            HTTP/1.1 200 OK
            Content-type: text/html; charset=utf-8
            Content-length: 15
            <h1>Hello!</h1>'''.replace(b'\n', b'\r\n'),
        '400' : b'''\
            HTTP/1.1 400 Bad Request
            Content-type: text/plain; charset=utf-8
            Content-length: 11
            Bad Request'''.replace(b'\n', b'\r\n'),
        '404' : b'''\
                HTTP/1.1 404 Not Found
                Content-type: text/plain
                Content-length: 9
                Not Found'''.replace(b'\n', b'\r\n'),
        '405' : b'''\
                HTTP/1.1 405 Method Not Allowed
                Content-type: text/plain
                Content-length: 17
                Method Not Allowed'''.replace(b'\n', b'\r\n'),
        'FILE_RESPONSE_TEMPLATE': '''\
                HTTP/1.1 200 OK
                Content-type: {content_type}
                Content-length: {content_length}
                '''.replace('\n', '\r\n')
        }

def serve_file(sock: socket.socket, path: str) -> None:
    '''
        Given a socket and the relative path to a file
        (relative to SERVER_SOCK), send that file to the socket if it exists.
        If the file doesn't exist, send a '404 Not Found' response.
    '''
    if path == '/':
        path = '/index.html'
    abspath = os.path.normpath(os.path.join(SERVER_ROOT,
        path.lstrip('/')))

    if not abspath.startswith(SERVER_ROOT):
        sock.sendall(RESPONSES['404'])
        return
    try:
        with open(abspath, 'rb') as f:
            stat = os.fstat(f.fileno())
            content_type, encoding = mimetypes.guess_type(abspath)
            if content_type is None:
                content_type = 'application/octet-stream'
            if encoding is not None:
                content_type += f'; charset={encoding}'
            response_headers = RESPONSES['FILE_RESPONSE_TEMPLATE'].format(
                content_type=content_type,
                content_length=stat.st_size,
            ).encode('utf-8')
            sock.sendall(response_headers)
            sock.sendfile(f)
    except FileNotFoundError:
        sock.sendall(RESPONSES['404'])
        return

def read_lines(sock: socket.socket, bufsize: int = 16_384) ->\
        typing.Generator[bytes, None, bytes]:
    '''
        Given a socket, read all the individual CRLF-separated lines
        and yield each one until an empty one is found.  Returns the
        remainder after the empty line.
    '''
    buff = b''
    while True:
        data = sock.recv(bufsize)
        if not data:
            return b''

        buff += data
        while True:
            try:
                i = buff.index(b'\r\n')
                line, buff = buff[:i], buff[i + 2:]
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
    def parse(cls, sock: socket.socket) -> 'Request':
        '''
            Read and parse the request from a socket object.
            Raises: ValueError When the request cannot be parsed.
        '''
        lines = read_lines(sock)
        try:
            request_line = next(lines).decode('utf-8')
        except StopIteration:
            raise ValueError('Request line missing.')

        try:
            method, path, _ = request_line.split(' ')
        except ValueError:
            raise ValueError(f'Malformed request line {request_line!r}.')
        headers = {}
        for line in lines:
            try:
                name, _, value = line.decode('utf-8').partition(':')
                headers[name.lower()] = value.lstrip()
            except ValueError:
                raise ValueError(f'Malformed header line {line!r}.')
            return cls(method=method.upper(), path=path, headers=headers)


with socket.socket() as ssock:
    ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ssock.bind((HOST, PORT ,))
    ssock.listen(0)
    print(f'Listening on {HOST}:{PORT}...')

    while True:
        client_sock, client_addr = ssock.accept()
        with client_sock:
            try:
                request = Request.parse(client_sock)
                print('method type ', request.method)
                if request.method != 'GET':
                    client_sock.sendall(RESPONSES['405'])
                    continue
                serve_file(client_sock, request.path)
                print(f'{request}')
            except Exception as e:
                client_sock.sendall(RESPONSES['400'])
                client_sock.close()
            print(f'New connection from {client_addr}.')
