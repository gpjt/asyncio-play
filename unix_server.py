"""
just listens to a file socket using start_unix_server
"""
import asyncio

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
    writer.write('hi, received your request')


loop = asyncio.get_event_loop()
coro = asyncio.start_unix_server(handle_request, path='/tmp/hi', loop=loop)
server = loop.run_until_complete(coro)

try:
    loop.run_forever()
except:
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
