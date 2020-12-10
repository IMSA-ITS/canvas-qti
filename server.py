from flask import jsonify, make_response, request, send_file, Flask
from flask_cors import CORS
import io
import logging
import text2qti
import time

qti_config = text2qti.config.Config()
qti_config.load()

app = Flask(__name__)
CORS(app)

app.logger.setLevel(logging.DEBUG)


@app.route("/")
def root():
    return "Hello, World!"


@app.route("/validate", methods=["POST"])
def validate():
    return doit()

@app.route("/generate", methods=["POST"])
def generate():
    return doit(generate=True)

def doit(generate=False):
    app.logger.info(f"validate: {request.args}")

    body = request.get_data().decode("utf-8")
    app.logger.debug(f"body = {body}")

    responseBody = {"error": ""}

    # time.sleep(2)               # for testing with lag
    try:
        quiz = text2qti.quiz.Quiz(body, config=qti_config, source_name="input")
        responseBody["quizinfo"] = quizinfo(quiz)

        app.logger.debug(f"{len(quiz.questions_and_delims)} questions")
    except text2qti.err.Text2qtiError as e:
        app.logger.error(f"text parse failed ({body}): {e}")
        responseBody["error"] = f"{e}\n"
        return jsonify(responseBody)

    app.logger.debug(f"locals = {locals()}")

    if not generate:
        return jsonify(responseBody)

    qti = text2qti.qti.QTI(quiz)

    fp = io.BytesIO()
    qti.write(fp)
    fp.seek(0)
    app.logger.debug(f"about to send generated file")

    return send_file(
        fp,
        mimetype="application/zip",
        as_attachment=True,
        attachment_filename="qti.zip",
    )


def quizinfo(quiz):
    info = { "questions": 0, "groups": 0 }

    for x in quiz.questions_and_delims:
        if isinstance(x, text2qti.quiz.Question):
            info["questions"] += 1
        elif isinstance(x, text2qti.quiz.GroupStart):
            info["groups"] += 1
            info["questions"] += len(x.group.questions)

    return info

            
