import request


HOST = "127.0.0.1"
PORT = 9000

RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

BAD_REQUEST_RESPONSE = b"""\
HTTP/1.1 400 Bad Request
Content-type: text/plain
Content-length: 11

Bad Request""".replace(b"\n", b"\r\n")

NOT_FOUND_RESPONSE = b"""\
HTTP/1.1 404 Not Found
Content-Type: text/plain
Content-length: 9

Not Found""".replace(b"\n", b"\r\n")

METHOD_NOT_ALLOWED_RESPONSE = b"""\
HTTP/1.1 405 Method Not Allowed
Content-type: text/plain
Content-length: 17

Method Not Allowed""".replace(b"\n", b"\r\n")

SERVER_ROOT = os.path.abspath("www")

FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")




def serve_file(sock: socket.socket, path: str) -> None:
    """Given a socket and the relative path to a file (relative to
    SERVER_SOCK), send that file to the socket if it exists. If the
    file doesn't exist, send a '404 Not Found' response.
    """
    if path == "/":
        path = "/index.html"

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        response = Response(status="404 Not Found", content="Not Found")
        response.send(sock)
        return

    try:
        with open(abspath, "rb") as f:
            content_type, encoding = mimetypes.guess_type(abspath)
            if content_type is None:
                content_type = "application/octet-stream"

            if encoding is not None:
                content_type += f"; charset={encoding}"

            response = Response(status="200 OK", body=f)
            response.headers.add("content-type", content_type)
            response.send(socket)
            return
    except FileNotFoundError:
        response = Response(status="404 Not Found", content="Not Found")
        response.send(sock)
        return
            

    
# By default, socket.socket creates TCP sockets
with socket.socket() as server_sock:
    # This tells the kernel to reuse sockets that ar in 'TIME_WAIT' state
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # This tells the socket what address to bind to
    server_sock.bind((HOST, PORT))

    # 0 is the number of pending connections the socket may have before
    # new connections are refused. Since this server is going to process
    # one connection at a time, we want to refuse any additional coonnections
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"New connection from {client_addr}.")
        with client_sock:
            try:
                request = Request.from_socket(client_sock)
                if "100-continue" in request.headers.get("expect", ""):
                    response = Response(status="100 Continue")
                    response.send(client_sock)
                    
                try:
                    content_length = int(request.headers.get("content_length", 0))
                except ValueError:
                    content_length = 0

                if content_length:
                    body = request.body.read(content_length)
                    print("Request body", body)
                    
                if request.method != "GET":
                    response = Response(status="405 Method Not Allowed", content="Method Not Allowed")
                    response.send(client_sock)
                    continue
                
                serve_file(client_sock, request.path)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                response = Response(status="400 Bad Request", content="Bad Request")
                response.send(client_sock)
            



