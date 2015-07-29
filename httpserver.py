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
def handle_request(downstream_reader, downstream_writer):
    print("New connection")
    data = b""

    try:
        while True:
            try:
                data += yield from asyncio.wait_for(downstream_reader.read(100), timeout=10)
            except asyncio.TimeoutError:
                print("TimeoutError!")
                downstream_writer.write(b"Timeout!")
                downstream_writer.close()
                return

            header_end_ix = data.find(b"\r\n\r\n")
            if header_end_ix != -1:
                print("Detected end of header")
                break
            print("Not at end of header yet")

        request = HTTPRequest(data[:header_end_ix])
        if request.error_code is not None:
            downstream_writer.write("HTTP/1.0 {} error\n\n".format(request.error_code).encode("utf8"))
            return

        host = request.headers.get("Host")
        if host is None:
            print("It's a non-hosty one")
        else:
            print("It has the host {!r}".format(host))

        print("Connecting upstream")
        upstream_reader, upstream_writer = yield from asyncio.open_connection(
            'www.resolversystems.com', 80, loop=loop
        )
        print("Got reader and writer for upstream, about to write {!r}".format(data))
        upstream_writer.write(data)
        print("Written buffer")
        upstream_reader_task = asyncio.Task(upstream_reader.read(100))
        downstream_reader_task = asyncio.Task(downstream_reader.read(100))
        while True:
            print("Waiting on both up- and down-stream readers")
            done, pending = yield from asyncio.wait(
                [upstream_reader_task, downstream_reader_task],
                loop=loop,
                return_when=asyncio.FIRST_COMPLETED
            )
            print("Got some data")
            breakout = False
            for future in done:
                if future == upstream_reader_task:
                    print("It's the upstream reader.  Replacing it.")
                    upstream_reader_task = asyncio.Task(upstream_reader.read(100))
                    print("Result is {!r}".format(future.result()))
                    if future.result() is b"":
                        breakout = True
                    else:
                        print("Writing to downstream")
                        downstream_writer.write(future.result())
                elif future == downstream_reader_task:
                    print("It's the downstream reader.  Replacing it.")
                    downstream_reader_task = asyncio.Task(downstream_reader.read(100))
                    print("Result is {!r}".format(future.result()))
                    if future.result() is b"":
                        breakout = True
                    else:
                        print("Writing to upstream")
                        upstream_writer.write(future.result())
                else:
                    raise Exception("WTF?")

            if breakout:
                print("Breakout!")
                break

        print("Out of loop")


    finally:
        print('Close the client socket')
        downstream_writer.close()


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
