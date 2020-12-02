from flask import make_response, request, send_file, Flask
import io
import logging
import text2qti

qti_config = text2qti.config.Config()
qti_config.load()

app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)


@app.route("/")
def root():
    return "Hello, World!"


@app.route("/validate", methods=["POST"])
def validate():
    app.logger.info(f"validate: {request.args}")

    body = request.get_data().decode("utf-8")
    app.logger.debug(f"body = {body}")

    try:
        quiz = text2qti.quiz.Quiz(body, config=qti_config)
    except text2qti.err.Text2qtiError as e:
        app.logger.error(f"text parse failed ({body}): {e}")
        return f"parse for QTI failed: {e}\n", 400

    app.logger.debug(f"locals = {locals()}")

    if not ("generate" in request.args):
        return "ok"

    qti = text2qti.qti.QTI(quiz)

    fp = io.BytesIO()
    qti.write(fp)
    fp.seek(0)
    return send_file(
        fp,
        mimetype="application/zip",
        as_attachment=True,
        attachment_filename="qti.zip",
    )
