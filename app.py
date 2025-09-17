import os
import logging
import threading
import time
import requests
from flask import Flask, request, render_template, redirect, send_file, jsonify
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

tasks = {}
tasks_lock = threading.Lock()

class DownloadTask:
    def __init__(self, url):
        self.url = url
        self.status = "queued"
        self.thread = None
        self.filename = ""
        self.output_dir = "downloads"
        self.progress = 0
        self.speed = "0 KB/s"
        self.downloaded_size = 0
        self.total_size = 0
        self.last_update = time.time()
        self.last_size = 0
        self.stop_requested = False
        self.pause_requested = False
        os.makedirs(self.output_dir, exist_ok=True)

    def start_download(self):
        try:
            self.status = "downloading"
            self.progress = 0
            self.speed = "0 KB/s"
            self.downloaded_size = 0
            self.total_size = 0
            self.last_size = 0
            self.last_update = time.time()
            self.stop_requested = False
            self.pause_requested = False
            
            # Получаем имя файла из URL
            parsed_url = urlparse(self.url)
            filename_from_url = os.path.basename(parsed_url.path)
            
            if not filename_from_url or '.' not in filename_from_url:
                filename_from_url = f"download_{int(time.time())}_{id(self)}"
            
            self.filename = os.path.join(self.output_dir, filename_from_url)
            
            # Запускаем поток для скачивания
            self.thread = threading.Thread(target=self.download_file, daemon=True)
            self.thread.start()
            
        except Exception as e:
            self.status = f"error: {str(e)}"
            logging.error(f"Error starting download: {e}")

    def download_file(self):
        try:
            # Получаем информацию о файле
            with requests.get(self.url, stream=True, timeout=10) as response:
                response.raise_for_status()
                
                # Получаем общий размер файла
                self.total_size = int(response.headers.get('content-length', 0))
                
                # Открываем файл для записи
                with open(self.filename, 'wb') as file:
                    start_time = time.time()
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.stop_requested:
                            break
                            
                        if self.pause_requested:
                            while self.pause_requested and not self.stop_requested:
                                time.sleep(0.1)
                            if self.stop_requested:
                                break
                        
                        if chunk:
                            file.write(chunk)
                            self.downloaded_size += len(chunk)
                            
                            # Обновляем скорость каждые 0.5 секунды
                            current_time = time.time()
                            time_diff = current_time - self.last_update
                            
                            if time_diff >= 0.5:
                                size_diff = self.downloaded_size - self.last_size
                                speed_bps = size_diff / time_diff
                                
                                # Форматируем скорость
                                if speed_bps > 1024*1024:
                                    self.speed = f"{speed_bps/(1024*1024):.1f} MB/s"
                                elif speed_bps > 1024:
                                    self.speed = f"{speed_bps/1024:.1f} KB/s"
                                else:
                                    self.speed = f"{speed_bps:.1f} B/s"
                                
                                # Вычисляем прогресс
                                if self.total_size > 0:
                                    self.progress = min(100, round((self.downloaded_size / self.total_size) * 100, 1))
                                
                                self.last_size = self.downloaded_size
                                self.last_update = current_time
                                
                
                # Проверяем, была ли остановка
                if self.stop_requested:
                    self.status = "paused" if self.pause_requested else "error"
                    return
                
                # Проверяем, завершена ли загрузка
                if self.downloaded_size == self.total_size or self.total_size == 0:
                    self.status = "completed"
                    self.progress = 100
                    self.speed = "Completed"
                    logging.info(f"Download completed: {self.url}")
                else:
                    self.status = "error"
                    logging.error(f"Download incomplete: {self.downloaded_size}/{self.total_size}")
                    
        except Exception as e:
            self.status = f"error: {str(e)}"
            logging.error(f"Error downloading file: {e}")

    def pause(self):
        if self.status == "downloading":
            self.pause_requested = True
            self.status = "paused"
            logging.info(f"Download paused: {self.url}")

    def resume(self):
        if self.status == "paused":
            self.pause_requested = False
            self.status = "downloading"
            logging.info(f"Download resumed: {self.url}")

    def restart(self):
        self.stop_requested = True
        time.sleep(0.1)  # Даем время остановиться
        
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except OSError as e:
                logging.error(f"Error deleting file: {e}")
        
        logging.info(f"Download restarted: {self.url}")
        self.start_download()

    def delete(self):
        self.stop_requested = True
        
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
                logging.info(f"File deleted: {self.filename}")
            except OSError as e:
                logging.error(f"Error deleting file: {e}")
        
        logging.info(f"Task deleted: {self.url}")

    def get_progress_info(self):
        return {
            'progress': self.progress,
            'speed': self.speed,
            'downloaded': self.format_size(self.downloaded_size),
            'total': self.format_size(self.total_size),
            'status': self.status
        }

    def format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        for unit in units:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

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