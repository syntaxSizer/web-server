import socket

HOST = '127.0.0.1'
PORT = 9000

RESPONSE = b"""
        HTTP/1.1 200 OK
        Content-type: text/html charset=utf-8
        Content-length: 15

        <h1>Hello!</h1>""".replace(b"\n", b"\r\n")

with socket.socket() as ssock:
    ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ssock.bind((HOST, PORT ,))
    ssock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = ssock.accept()
        with client_sock:
            client_sock.sendall(RESPONSE)
            print(f"New connection from {client_addr}.")
