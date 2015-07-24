import asyncio
from http.server import BaseHTTPRequestHandler
from io import BytesIO


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_bytes):
        self.rfile = BytesIO(request_bytes)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


@asyncio.coroutine
def handle_request(reader, writer):
    data = b""

    while True:
        try:
            data += yield from asyncio.wait_for(reader.read(100), timeout=10)
        except asyncio.TimeoutError:
            print("TimeoutError!")
            writer.write(b"Timeout!")
            writer.close()
            return

        header_end_ix = data.find(b"\r\n\r\n")
        if header_end_ix != -1:
            print("Detected end of header")
            break
        print("Not at end of header yet")

    request = HTTPRequest(data[:header_end_ix])
    if request.error_code is not None:
        reply = "Error {}".format(request.error_code)
    else:
        host = request.headers.get("Host")
        if host is None:
            print("It's a non-hosty one")
        else:
            print("It has the host {!r}".format(host))

        reply = "You're trying to access {!r}".format(host)

    print('Send: {!r}'.format(reply))
    writer.write(reply.encode("utf8"))

    print('Close the client socket')
    writer.close()

loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_request, '127.0.0.1', 8888, loop=loop)
server = loop.run_until_complete(coro)

# Serve requests until CTRL+c is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()

