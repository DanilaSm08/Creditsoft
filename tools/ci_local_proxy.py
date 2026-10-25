"""Map the public loopback Gitea artifact URL inside its isolated CI container."""

import select
import socket
import socketserver


class Forward(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection(("gitea", 3000), timeout=60) as upstream:
            streams = [self.request, upstream]
            while True:
                readable, _, _ = select.select(streams, [], [], 60)
                if not readable:
                    return
                for stream in readable:
                    data = stream.recv(65536)
                    if not data:
                        return
                    (upstream if stream is self.request else self.request).sendall(data)


if __name__ == "__main__":
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", 3030), Forward) as server:
        server.serve_forever()
