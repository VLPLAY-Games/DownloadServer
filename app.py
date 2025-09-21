import os
import logging
import threading
from flask import Flask, request, render_template, redirect, send_file, jsonify
from backend.download import DownloadTask
from backend.account_manager import AccountManager, login_required
from flask import Flask, request, render_template, redirect, send_file, jsonify, session, flash

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = os.urandom(24)
account_manager = AccountManager()

tasks = {}
tasks_lock = threading.Lock()

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    username = session['username']
    user_tasks = account_manager.get_user_tasks(username)

    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if url:
            try:
                with tasks_lock:
                    task = DownloadTask(url)
                    task_id = id(task)
                    tasks[task_id] = task

                    # сохраняем задачу
                    task_data = {
                        'id': task_id,
                        'url': url,
                        'status': 'started',
                        'filename': task.filename
                    }
                    account_manager.add_user_task(username, task_data)

                    task.start_download()
                logging.info(f"New download task added: {url}")
            except Exception as e:
                logging.error(f"Error creating task: {e}")
                flash(f"Error creating task: {e}", "error")
        return redirect('/')

    return render_template('index.html', tasks=tasks, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        success, message = account_manager.login(username, password)
        if success:
            session['username'] = username
            flash(message, "success")
            return redirect('/')
        else:
            flash(message, "error")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
        else:
            success, message = account_manager.register(username, password)
            if success:
                flash(message, "success")
                return redirect('/login')
            else:
                flash(message, "error")
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out", "info")
    return redirect('/login')

@app.route('/control', methods=['POST'])
@login_required
def control():
    try:
        task_id = int(request.form['id'])
        action = request.form['action']
        username = session['username']
        
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
                    # Удаляем задачу из профиля пользователя
                    account_manager.delete_user_task(username, task_id)
                    
    except (KeyError, ValueError) as e:
        logging.error(f"Error processing control action: {e}")
        flash(f"Error processing action: {e}", "error")
    
    return redirect('/')

@app.route('/progress/<int:task_id>')
@login_required
def get_progress(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
        if task:
            return jsonify(task.get_progress_info())
    return jsonify({'error': 'Task not found'}), 404

@app.route('/download/<int:task_id>')
@login_required
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