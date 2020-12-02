from http.server import BaseHTTPRequestHandler
from urllib import parse
import functools
import json
import text2qti
import text2qti.config
import logging
import signal
import sys


class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = parse.urlparse(self.path)
        message_parts = [
            "CLIENT VALUES:",
            "client_address={} ({})".format(self.client_address, self.address_string()),
            "command={}".format(self.command),
            "path={}".format(self.path),
            "real path={}".format(parsed_path.path),
            "query={}".format(parsed_path.query),
            "request_version={}".format(self.request_version),
            "",
            "SERVER VALUES:",
            "server_version={}".format(self.server_version),
            "sys_version={}".format(self.sys_version),
            "protocol_version={}".format(self.protocol_version),
            "",
            "HEADERS RECEIVED:",
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append("{}={}".format(name, value.rstrip()))
        message_parts.append("")
        message = "\r\n".join(message_parts)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def do_POST(self):
        parsed_path = parse.urlparse(self.path)
        message_parts = [
            "POST CLIENT VALUES:",
            "client_address={} ({})".format(self.client_address, self.address_string()),
            "command={}".format(self.command),
            "path={}".format(self.path),
            "real path={}".format(parsed_path.path),
            "query={}".format(parsed_path.query),
            "request_version={}".format(self.request_version),
            "",
            "SERVER VALUES:",
            "server_version={}".format(self.server_version),
            "sys_version={}".format(self.sys_version),
            "protocol_version={}".format(self.protocol_version),
            "",
            "HEADERS RECEIVED:",
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append("{}={}".format(name, value.rstrip()))
        message_parts.append("")

        content_len = int(self.headers.get("Content-Length"))
        post_body = self.rfile.read(content_len)

        message_parts.append("BODY")
        # message_parts.append('content_len={}'.format(content_len))
        message_parts.append(post_body.decode("utf-8", "strict"))
        message_parts.append("")

        message = "\r\n".join(message_parts)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))


class QTIHandler(BaseHTTPRequestHandler):
    def __init__(self, config, *args, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)

    def do_POST(self):
        parsed_path = parse.urlparse(self.path)
        #logging.debug(f"POST: {locals()}")
        if parsed_path.path == "/validate":
            self.validate()

    def validate(self):
        logging.debug("validate")
        content_len = int(self.headers.get("Content-Length"))
        post_body = self.rfile.read(content_len)
        try:
            body = json.loads(post_body.decode("utf-8", "strict"))
        except json.decoder.JSONDecodeError as e:
            logging.error(f"failed to decode post body ({post_body}): {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            body = json.dumps({
                "error": f"failed to decode post body: {e}"
            })
            self.wfile.write(body.encode("utf-8"))
            return

        quiz = text2qti.quiz.Quiz(body, config=self.config)

        logging.debug(f"locals = {locals()}")

def signal_handler(sig, frame):
    logging.info("interrupted")
    sys.exit(0)


if __name__ == "__main__":
    from http.server import HTTPServer

    logging.basicConfig(level=logging.DEBUG)

    signal.signal(signal.SIGINT, signal_handler)

    config = text2qti.config.Config()
    config.load()

    handler = functools.partial(QTIHandler, config)
    server = HTTPServer(("localhost", 8080), handler)
    print("Starting server, use <Ctrl-C> to stop")

    server.serve_forever()
