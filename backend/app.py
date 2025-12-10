import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from rag_pipeline import build_vectorstore_from_pdf, answer_question

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path="",
)

CORS(app)

# Global state for current PDF + vector DB
CURRENT_DB = None
CURRENT_PDF_NAME = None


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    Upload a PDF, build its vector store, and set it as the current document.
    """
    global CURRENT_DB, CURRENT_PDF_NAME

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)

    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    try:
        db = build_vectorstore_from_pdf(save_path, source_name=filename)
    except Exception as e:
        return jsonify({"error": f"Failed to process PDF: {e}"}), 500

    CURRENT_DB = db
    CURRENT_PDF_NAME = filename

    return jsonify(
        {
            "message": "PDF uploaded and indexed successfully",
            "file_name": filename,
        }
    )


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """
    Ask a question against the currently uploaded PDF.
    """
    global CURRENT_DB, CURRENT_PDF_NAME

    data = request.get_json(force=True)
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    if CURRENT_DB is None:
        return jsonify({"error": "No PDF uploaded yet. Please upload a PDF first."}), 400

    try:
        result = answer_question(CURRENT_DB, question)
        # Add file name info but no sources
        result["file_name"] = CURRENT_PDF_NAME
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def api_status():
    """
    Return info about currently loaded PDF.
    """
    return jsonify(
        {
            "file_name": CURRENT_PDF_NAME,
            "has_pdf": CURRENT_DB is not None,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
