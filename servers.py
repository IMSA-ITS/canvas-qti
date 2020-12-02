from http.server import BaseHTTPRequestHandler
from urllib import parse
import functools
import json
import text2qti
import text2qti.config
import logging
import logging.config
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
    def __init__(self, config, logger, *args, **kwargs):
        self.config = config
        self.logger = logger
        super().__init__(*args, **kwargs)

    def do_POST(self):
        parsed_path = parse.urlparse(self.path)
        if parsed_path.path == "/validate":
            self.validate()
        elif parsed_path.path == "/generate":
            self.validate(generate=True)
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("")


    def validate(self, generate=False):
        self.logger.debug("validate")
        content_len = int(self.headers.get("Content-Length"))
        body = self.rfile.read(content_len).decode("utf-8", "strict")

        try:
            quiz = text2qti.quiz.Quiz(body, config=self.config)
        except text2qti.err.Text2qtiError as e:
            self.logger.error(f"text parse failed ({body}): {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            body = json.dumps({"error": f"QTI parse failed: {e}"})
            self.wfile.write(body.encode("utf-8"))
            return

        self.logger.debug(f"locals = {locals()}")

        if not generate:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response_body = json.dumps({})
            self.wfile.write(response_body.encode("utf-8"))

        qti = text2qti.qti.QTI(quiz)


if __name__ == "__main__":
    from http.server import HTTPServer

    logging.config.fileConfig("logging.conf")
    logger = logging.getLogger(__name__)

    def signal_handler(sig, frame):
        logger.info("interrupted")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    config = text2qti.config.Config()
    config.load()

    handler = functools.partial(QTIHandler, config, logger)
    server = HTTPServer(("localhost", 8080), handler)
    print("Starting server, use <Ctrl-C> to stop")

    server.serve_forever()
