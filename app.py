import os
import logging
import threading
import time
import subprocess
import re
from flask import Flask, request, render_template, redirect, send_file, jsonify

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

tasks = {}
tasks_lock = threading.Lock()

class DownloadTask:
    def __init__(self, url):
        self.url = url
        self.status = "queued"
        self.process = None
        self.filename = ""
        self.output_dir = "downloads"
        self.progress = 0
        self.speed = "0 KB/s"
        self.downloaded_size = 0
        self.total_size = 0
        self.last_update = time.time()
        self.last_size = 0
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
            
            filename_from_url = os.path.basename(self.url)
            if not filename_from_url or '.' not in filename_from_url:
                filename_from_url = f"download_{int(time.time())}_{id(self)}"
            
            self.filename = os.path.join(self.output_dir, filename_from_url)
            
            # Запускаем wget с выводом прогресса
            self.process = subprocess.Popen(
                ["wget", "-c", "--progress=dot", "-O", self.filename, self.url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            threading.Thread(target=self.monitor_wget_output, daemon=True).start()
            threading.Thread(target=self.monitor_file_size, daemon=True).start()
            threading.Thread(target=self.monitor_download_completion, daemon=True).start()
        except Exception as e:
            self.status = f"error: {str(e)}"
            logging.error(f"Error starting download: {e}")


    def monitor_wget_output(self):
        """Мониторим вывод wget для получения информации о размере и прогрессе"""
        try:
            if self.process and self.process.stderr:
                while self.process.poll() is None and self.status == "downloading":
                    line = self.process.stderr.readline()
                    if not line:
                        time.sleep(0.1)  # Небольшая пауза если нет данных
                        continue
                    
                    line = line.strip()
                    logging.debug(f"wget: {line}")
                    
                    # Ищем информацию о размере
                    size_match = re.search(r'Length:\s*(\d+)', line)
                    if size_match:
                        self.total_size = int(size_match.group(1))
                        logging.info(f"Total size: {self.total_size} bytes")
                    
                    # Ищем информацию о прогрессе
                    progress_match = re.search(r'(\d+)%', line)
                    if progress_match:
                        self.progress = int(progress_match.group(1))
                        # Обновляем размер скачанного (если есть общий размер)
                        if self.total_size > 0:
                            self.downloaded_size = int(self.total_size * self.progress / 100)
                    
                    # Ищем информацию о скорости
                    speed_match = re.search(r'(\d+\.?\d*[KM]?B/s)', line)
                    if speed_match:
                        self.speed = speed_match.group(1)
                    
        except Exception as e:
            logging.error(f"Error monitoring wget output: {e}")

    def monitor_file_size(self):
        """Резервный метод: мониторим размер файла на диске каждые 0.5 секунды"""
        while self.process and self.process.poll() is None and self.status == "downloading":
            try:
                if os.path.exists(self.filename):
                    current_size = os.path.getsize(self.filename)
                    self.downloaded_size = current_size
                    
                    # Вычисляем скорость на основе изменения размера
                    current_time = time.time()
                    time_diff = current_time - self.last_update
                    
                    if time_diff >= 0.5:  # Обновляем каждые 0.5 секунды
                        size_diff = current_size - self.last_size
                        speed_bps = size_diff / time_diff if time_diff > 0 else 0
                        
                        # Форматируем скорость
                        if speed_bps > 1024*1024:
                            self.speed = f"{speed_bps/(1024*1024):.1f} MB/s"
                        elif speed_bps > 1024:
                            self.speed = f"{speed_bps/1024:.1f} KB/s"
                        else:
                            self.speed = f"{speed_bps:.1f} B/s"
                        
                        # Если знаем общий размер, вычисляем прогресс
                        if self.total_size > 0:
                            self.progress = min(100, int((current_size / self.total_size) * 100))
                        
                        self.last_size = current_size
                        self.last_update = current_time
                
                time.sleep(0.1)  # Частая проверка для быстрого обновления
                
            except Exception as e:
                logging.error(f"Error monitoring file size: {e}")
                time.sleep(0.5)

    def monitor_download_completion(self):
        """Отдельный поток для ожидания завершения загрузки"""
        if self.process:
            returncode = self.process.wait()
            if returncode == 0:
                self.status = "completed"
                self.progress = 100
                self.speed = "Completed"
                if os.path.exists(self.filename):
                    self.downloaded_size = os.path.getsize(self.filename)
                logging.info(f"Download completed: {self.url}")
            else:
                self.status = "error"
                logging.error(f"Download failed: {self.url}")
                self.retry_download()


    def retry_download(self):
        time.sleep(5)
        if self.status != "paused":
            logging.info(f"Retrying download: {self.url}")
            self.start_download()

    def pause(self):
        if self.status == "downloading":
            self.status = "paused"
            if self.process:
                self.process.terminate()
            logging.info(f"Download paused: {self.url}")

    def resume(self):
        if self.status == "paused":
            logging.info(f"Download resumed: {self.url}")
            self.start_download()

    def restart(self):
        if self.process:
            self.process.terminate()
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except OSError as e:
                logging.error(f"Error deleting file: {e}")
        
        logging.info(f"Download restarted: {self.url}")
        self.start_download()

    def delete(self):
        # Останавливаем процесс если он запущен
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logging.error(f"Error stopping process: {e}")
        
        # Удаляем файл если он существует
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
                logging.info(f"File deleted: {self.filename}")
            except OSError as e:
                logging.error(f"Error deleting file: {e}")
        
        logging.info(f"Task deleted: {self.url}")

    def get_progress_info(self):
        # Обновляем информацию о размере файла перед возвратом данных
        if self.status == "downloading" and os.path.exists(self.filename):
            try:
                current_size = os.path.getsize(self.filename)
                current_time = time.time()
                
                # Обновляем размер и скорость, если прошло достаточно времени
                if current_time - self.last_update > 0.1:  # Не чаще чем 10 раз в секунду
                    size_diff = current_size - self.last_size
                    time_diff = current_time - self.last_update
                    
                    if time_diff > 0:
                        speed_bps = size_diff / time_diff
                        
                        # Форматируем скорость
                        if speed_bps > 1024*1024:
                            self.speed = f"{speed_bps/(1024*1024):.1f} MB/s"
                        elif speed_bps > 1024:
                            self.speed = f"{speed_bps/1024:.1f} KB/s"
                        else:
                            self.speed = f"{speed_bps:.1f} B/s"
                        
                        self.downloaded_size = current_size
                        self.last_size = current_size
                        self.last_update = current_time
                        
                        # Если знаем общий размер, вычисляем прогресс
                        if self.total_size > 0:
                            self.progress = min(100, int((current_size / self.total_size) * 100))
            except Exception as e:
                logging.error(f"Error updating file info: {e}")
        
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
    os.makedirs('downloads', exist_ok=True)
    app.run(host='0.0.0.0', port=8100, debug=True)