from pathlib import Path
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import os
import json

load_dotenv()

from .case_loader import load_case_docs_in_chunks, load_example_case_docs, load_case_docs
from .local_llm import exec_llm, exec_llm_refine, exec_llm_revision, exec_llm_user_revision

os.environ["FLASK_ENV"] = "development"
os.environ["FLASK_DEBUG"] = "False"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logs_dir = Path(os.getcwd()).parent / "narrative_logs"
os.makedirs(logs_dir, exist_ok=True)

@app.route("/", methods=['GET'])
def ping():
    return jsonify({"ping": "pong"})


@app.route("/generate_narrative", methods=['POST'])
def generate_narrative():
    data = request.get_json()

    if not data or 'case' not in data:
        return jsonify({"error": "Missing case field"}), 400
    
    if 'files' not in data or not data['files']:
        return jsonify({"error": "No files provided"}), 400
    
    if 'folderName' not in data or not data['folderName']:
        return jsonify({"error": "Missing folderName field"}), 400

    # Process the files sent from frontend
    case = int(data['case'])
    files_data = data['files']
    folder_name = data['folderName']
    user_marker = data['marker']
    
    # docs = load_example_case_docs(case_id=case)
    docs = load_case_docs(case_id=case, files_data=files_data, folder_name=folder_name, use_marker=user_marker)
    if not docs:
        return jsonify({"error": f"Case {case} not found"}), 404

    response = exec_llm(docs)

    return jsonify({"narrative": response})

@app.route("/generate_narrative_revision", methods=['POST'])
def generate_narrative_revision():
    data = request.get_json()

    if not data or 'case' not in data:
        return jsonify({"error": "Missing case field"}), 400
    
    if 'files' not in data or not data['files']:
        return jsonify({"error": "No files provided"}), 400
    
    if 'folderName' not in data or not data['folderName']:
        return jsonify({"error": "Missing folderName field"}), 400

    if not data or 'narrative' not in data:
        return jsonify({"error": "Missing narrative field"}), 400

    if not data or 'feedback' not in data:
        return jsonify({"error": "Missing feedback field"}), 400
    
    # Process the files sent from frontend
    case = int(data['case'])
    files_data = data['files']
    folder_name = data['folderName']
    narrative = data['narrative']
    feedback = data['feedback']
    user_marker = data['marker']

    # print(case, files_data, folder_name, narrative, feedback)s

    docs = load_case_docs(case_id=case, files_data=files_data, folder_name=folder_name, max_tokens=3000, use_marker=user_marker)
    response = exec_llm_revision(narrative, feedback, docs)

    return jsonify({"narrative": response})

@app.route("/generate_narrative_refined", methods=['POST'])
def generate_narrative_refined():
    data = request.get_json()

    if not data or 'case' not in data:
        return jsonify({"error": "Missing case field"}), 400
    
    if 'files' not in data or not data['files']:
        return jsonify({"error": "No files provided"}), 400
    
    if 'folderName' not in data or not data['folderName']:
        return jsonify({"error": "Missing folderName field"}), 400

    # Process the files sent from frontend
    case = int(data['case'])
    files_data = data['files']
    folder_name = data['folderName']
    user_marker = data.get('marker', False)

    chunks = load_case_docs_in_chunks(files_data, folder_name, case_id=case, max_tokens=3000, use_marker=user_marker)
    
    # Use the refine approach
    response = exec_llm_refine(chunks)

    return jsonify({"narrative": response})


@app.route("/generate_narrative_revision_refined", methods=['POST'])
def generate_narrative_revision_refined():
    data = request.get_json()

    if not data or 'case' not in data:
        return jsonify({"error": "Missing case field"}), 400
    
    if 'files' not in data or not data['files']:
        return jsonify({"error": "No files provided"}), 400
    
    if 'folderName' not in data or not data['folderName']:
        return jsonify({"error": "Missing folderName field"}), 400

    if not data or 'narrative' not in data:
        return jsonify({"error": "Missing narrative field"}), 400

    if not data or 'feedback' not in data:
        return jsonify({"error": "Missing feedback field"}), 400
    
    # Process the files sent from frontend
    case = int(data['case'])
    files_data = data['files']
    folder_name = data['folderName']
    narrative = data['narrative']
    feedback = data['feedback']
    user_marker = data.get('marker', False)

    chunks = load_case_docs_in_chunks(files_data, folder_name, case_id=case, max_tokens=3000, use_marker=user_marker)

    # Use the refined revision approach
    response = exec_llm_user_revision(
        narrative=narrative,
        user_feedback=feedback,
        chunks=chunks
    )

    return jsonify({"narrative": response})

@app.route("/save_history", methods=['POST'])
def save_history():
    data = request.get_json()

    # Required fields: narrativeId, timestamp, user, narrative.
    required_fields = ['narrativeId', 'timestamp', 'user', 'narrative', 'folderName']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing {field} field"}), 400

    # Load existing history if available
    history_file = logs_dir / f'{data["narrativeId"].split(": ")[1]}_{data["user"]}.json'
    print(f"History file: {history_file}")
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            try:
                history = json.load(f)
            except Exception as e:
                history = []
    else:
        history = []

    # Append new entry
    history.append(data)
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    return jsonify({"message": "History saved successfully"}), 200


@app.route("/get_history", methods=['GET'])
def get_history():
    
    # Optionally filter by narrativeId and testerName (user)
    narrative_id = request.args.get('narrativeId')
    tester_name = request.args.get('testerName')

    history_file = logs_dir / f'{narrative_id.split(": ")[1]}_{tester_name}.json'

    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            try:
                history = json.load(f)
            except Exception as e:
                history = []
    else:
        history = []

    return jsonify(history), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)