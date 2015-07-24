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



class HTTPServerClientProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self.buffer = b""

    def data_received(self, data):
        print('Raw data received: {!r}'.format(data))

        self.buffer += data
        header_end_ix = self.buffer.find(b"\r\n\r\n")
        if header_end_ix == -1:
            print("Not at end of header yet")
            return

        request = HTTPRequest(self.buffer)
        host = request.headers.get("Host")
        if host is None:
            print("It's a non-hosty one")
        else:
            print("It has the host {!r}".format(host))

        reply = "You're trying to access {!r}".format(host)
        print('Send: {!r}'.format(reply))
        self.transport.write(reply.encode("utf8"))

        print('Close the client socket')
        self.transport.close()

loop = asyncio.get_event_loop()
# Each client connection will create a new protocol instance
coro = loop.create_server(HTTPServerClientProtocol, '127.0.0.1', 8888)
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