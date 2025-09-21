import os
import logging
import threading
from flask import Flask, request, render_template, redirect, send_file, jsonify
from download import DownloadTask

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

tasks = {}
tasks_lock = threading.Lock()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if url:
            try:
                with tasks_lock:
                    task = DownloadTask(url)
                    task_id = id(task)
                    tasks[task_id] = task
                    task.start_download()
                logging.info(f"New download task added: {url}")
            except Exception as e:
                logging.error(f"Error creating task: {e}")
        return redirect('/')
    
    return render_template('index.html', tasks=tasks)

@app.route('/control', methods=['POST'])
def control():
    try:
        task_id = int(request.form['id'])
        action = request.form['action']
        
        with tasks_lock:
            task = tasks.get(task_id)
            if task:
                if action == "pause":
                    task.pause()
                elif action == "resume":
                    task.resume()
                elif action == "restart":
                    task.restart()
                elif action == "delete":
                    task.delete()
                    del tasks[task_id]
                    
    except (KeyError, ValueError) as e:
        logging.error(f"Error processing control action: {e}")
    
    return redirect('/')

@app.route('/progress/<int:task_id>')
def get_progress(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
        if task:
            return jsonify(task.get_progress_info())
    return jsonify({'error': 'Task not found'}), 404

@app.route('/download/<int:task_id>')
def download_file(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
        if task and task.status == "completed" and os.path.exists(task.filename):
            try:
                return send_file(
                    task.filename, 
                    as_attachment=True,
                    download_name=os.path.basename(task.filename)
                )
            except Exception as e:
                logging.error(f"Error downloading file: {e}")
                return f"Error downloading file: {e}", 500
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8100, debug=True)