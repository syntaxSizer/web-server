import socket

HOST = '127.0.0.1'
PORT = 3000

RESPONSE = b"""
        HTTP/1.1 200 OK
        Content-type: text/html
        Content-length: 15
        <h1>Hello!</h1>""".replace(b"\n", b"\r\n")

with socket.socket() as ssock:
    ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ssock.bind((HOST, PORT ,))
    ssock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = ssock.accept()
        print(f"New connection from {client_addr}.")
        with client_sock:
            client_sock.sendall(RESPONSE)
            client_sock, client_addr = ssock.accept()
            print(f"New connection from {client_addr}.")
            print(f" the response {RESPONSE}")
