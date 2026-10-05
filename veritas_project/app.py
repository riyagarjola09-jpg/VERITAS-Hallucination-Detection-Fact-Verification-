"""
VERITAS Web Application
------------------------
Flask server exposing the VERITAS hallucination-detection pipeline
through a small REST API and a browser-based demo UI.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

from flask import Flask, jsonify, render_template, request

from veritas.pipeline import VeritasPipeline

app = Flask(__name__)
pipeline = VeritasPipeline()

SAMPLE_RESPONSE = """The capital of Australia is Sydney, which is also its largest city.
Water boils at 100 degrees Celsius at standard atmospheric pressure.
The Great Wall of China can be seen from space with the naked eye, which is a well known fact.
Python was created by Guido van Rossum and first released in 1991.
The first iPhone was released by Apple in 2005.
Studies show that listening to jazz music increases IQ by 15 points permanently.
Mount Everest stands at 8,849 meters above sea level."""


@app.route("/")
def index():
    return render_template("index.html", sample_response=SAMPLE_RESPONSE)


@app.route("/api/verify", methods=["POST"])
def verify():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Please provide a non-empty 'text' field."}), 400
    report = pipeline.run(text)
    return jsonify(report)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
