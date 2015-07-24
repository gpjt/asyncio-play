import asyncio

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

        header_text = self.buffer[:header_end_ix]
        print("Got total header, it's {!r}".format(header_text))
        headers = header_text.split(b"\r\n")
        host = None
        for header in headers:
            print("Processing header {!r}".format(header))
            try:
                key, _, value = header.partition(b": ")
                # value = value.strip(b"\r\n")
                print("Key is {!r}, value is {!r}".format(key, value))
                if key == b"Host":
                    host = value.decode()
            except Exception as e:
                print("No colon, skipping: {!r}".format(e))

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