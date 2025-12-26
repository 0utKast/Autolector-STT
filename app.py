import os
import subprocess
import uuid
import shutil
import threading
import queue
import time
import json
from flask import Flask, request, render_template, jsonify, Response, send_from_directory
from faster_whisper import WhisperModel
import torch

# Configuración del modelo Whisper
WHISPER_MODEL_NAME = os.getenv('WHISPER_MODEL', 'base')
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

print(f"DEBUG: Loading Whisper model '{WHISPER_MODEL_NAME}' on {device} ({compute_type})...")
model = WhisperModel(WHISPER_MODEL_NAME, device=device, compute_type=compute_type)
print("DEBUG: Whisper model loaded successfully.")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Almacenamiento global para estados y streams
task_statuses = {}
task_queues = {}
task_audio_paths = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/audio/<task_id>')
def serve_audio(task_id):
    path = task_audio_paths.get(task_id)
    if path and os.path.exists(path):
        return send_from_directory(os.path.dirname(path), os.path.basename(path))
    return "Audio not found", 404

@app.route('/stream/<task_id>')
def stream_transcription(task_id):
    print(f"DEBUG: New SSE connection request for task {task_id}")
    def generate():
        q = task_queues.get(task_id)
        if not q:
            print(f"DEBUG: SSE Task {task_id} not found")
            yield "data: {\"error\": \"Task not found\"}\n\n"
            return
        
        # Send initial connection event
        yield "data: {\"status\": \"connected\"}\n\n"
        print(f"DEBUG: SSE connection established for task {task_id}")
        
        while True:
            try:
                segment = q.get(timeout=30)
                if segment == "DONE":
                    print(f"DEBUG: SSE Task {task_id} completed")
                    yield "data: {\"status\": \"completed\"}\n\n"
                    break
                if isinstance(segment, dict) and "error" in segment:
                    print(f"DEBUG: SSE Task {task_id} error: {segment['error']}")
                    yield f"data: {json.dumps(segment)}\n\n"
                    break
                
                print(f"DEBUG: SSE Sending segment for {task_id}: {segment.get('text')[:20]}...")
                yield f"data: {json.dumps(segment)}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
            except Exception as e:
                print(f"DEBUG: SSE Exception for {task_id}: {e}")
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/status/<task_id>')
def get_status(task_id):
    status = task_statuses.get(task_id, {'status': 'unknown', 'transcription': None, 'error': None})
    return jsonify(status)

@app.route('/upload', methods=['POST'])
def upload_file():
    task_id = str(uuid.uuid4())
    task_statuses[task_id] = {'status': 'received', 'transcription': None, 'error': None}

    if 'file' not in request.files:
        task_statuses[task_id]['status'] = 'error'
        task_statuses[task_id]['error'] = "No file part"
        return jsonify({'task_id': task_id, 'status': 'error', 'message': "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        task_statuses[task_id]['status'] = 'error'
        task_statuses[task_id]['error'] = "No selected file"
        return jsonify({'task_id': task_id, 'status': 'error', 'message': "No selected file"}), 400

    if file:
        if shutil.which('ffmpeg') is None:
            task_statuses[task_id]['status'] = 'error'
            task_statuses[task_id]['error'] = "ffmpeg no instalado"
            return jsonify({'task_id': task_id, 'status': 'error', 'message': "ffmpeg no instalado"}), 500

        unique_filename = str(uuid.uuid4())
        original_filename, file_extension = os.path.splitext(file.filename)
        temp_input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename + file_extension)
        file.save(temp_input_file_path)

        task_queues[task_id] = queue.Queue()
        threading.Thread(target=process_file_for_transcription, args=(temp_input_file_path, file_extension, task_id, original_filename)).start()

        return jsonify({'task_id': task_id, 'status': 'processing_started'}), 202

def process_file_for_transcription(input_file_path, file_extension, task_id, original_filename):
    sanitized_name = "".join([c for c in original_filename if c.isalnum() or c in (' ', '_', '-')]).strip() or "transcription"
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    wav_path = os.path.join(app.config['UPLOAD_FOLDER'], base_filename + '.wav')
    txt_path_final = os.path.join(app.config['UPLOAD_FOLDER'], f"{sanitized_name}_{str(uuid.uuid4())[:8]}.txt")

    audio_input_path = input_file_path

    try:
        task_statuses[task_id]['status'] = 'file_saved'

        if file_extension.lower() == '.mp4':
            task_statuses[task_id]['status'] = 'extracting_audio'
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', input_file_path, '-vn', wav_path], check=True, timeout=600)
            audio_input_path = wav_path
            task_statuses[task_id]['status'] = 'audio_extracted'
            task_audio_paths[task_id] = wav_path
        else:
            task_statuses[task_id]['status'] = 'ready_for_transcription'
            task_audio_paths[task_id] = input_file_path

        task_statuses[task_id]['status'] = 'transcribing'
        segments, info = model.transcribe(audio_input_path, beam_size=5)
        
        full_text = []
        q = task_queues.get(task_id)

        for segment in segments:
            seg_data = {"start": segment.start, "end": segment.end, "text": segment.text}
            full_text.append(segment.text)
            if q: q.put(seg_data)

        with open(txt_path_final, 'w', encoding='utf-8') as f:
            f.write("".join(full_text))

        task_statuses[task_id]['status'] = 'completed'
        task_statuses[task_id]['transcription'] = "".join(full_text)
        if q: q.put("DONE")

    except Exception as e:
        print(f"ERROR task {task_id}: {e}")
        task_statuses[task_id]['status'] = 'error'
        task_statuses[task_id]['error'] = str(e)
        q = task_queues.get(task_id)
        if q: q.put({"error": str(e)})
    finally:
        # Cleanup code could go here, but for 'Autolector' we might want to keep the audio 
        # for a while. We'll leave the file management for now.
        pass

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
