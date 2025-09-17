// Глобальная переменная для хранения таймеров обновления
const progressTimers = {};

// Функция для обновления прогресса конкретной задачи
function updateProgress(taskId) {
    fetch(`/progress/${taskId}`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    clearInterval(progressTimers[taskId]);
                    delete progressTimers[taskId];
                }
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const taskElement = document.getElementById(`task-${taskId}`);
            if (!taskElement) return;

            const progressBar = document.getElementById(`progress-${taskId}`);
            const sizeInfo = document.getElementById(`size-${taskId}`);
            const speedInfo = document.getElementById(`speed-${taskId}`);
            const statusBadge = taskElement.querySelector('.status-badge');

            if (progressBar && data.progress !== undefined) {
                progressBar.style.width = `${data.progress}%`;
                progressBar.textContent = `${data.progress}%`;
            }

            if (sizeInfo && data.downloaded !== undefined && data.total !== undefined) {
                sizeInfo.textContent = `${data.downloaded} / ${data.total}`;
            }

            if (speedInfo && data.speed !== undefined) {
                speedInfo.textContent = data.speed;
            }

            if (data.status) {
                taskElement.className = taskElement.className.replace(
                    /\b(queued|downloading|paused|completed|error)\b/g, ''
                ).trim();
                taskElement.className += ' task ' + data.status;

                if (statusBadge) {
                    statusBadge.textContent = data.status;
                    statusBadge.className = statusBadge.className.replace(
                        /\bstatus-(queued|downloading|paused|completed|error)\b/g, ''
                    ).trim();
                    statusBadge.className += ' status-badge status-' + data.status;
                }
            }

            // динамически создаём кнопку Download, если задача завершена
            if (data.status === 'completed') {
                let downloadBtn = taskElement.querySelector('.btn-download');
                if (downloadBtn) {
                    downloadBtn.href = `/download/${taskId}`;
                    downloadBtn.style.display = 'inline-block';
                }
                let pauseBtn = taskElement.querySelector('.btn-pause');
                if (pauseBtn) {
                    pauseBtn.style.display = 'none';
                }
                clearInterval(progressTimers[taskId]);
                delete progressTimers[taskId];
            }

            if (data.status === 'error') {
                clearInterval(progressTimers[taskId]);
                delete progressTimers[taskId];
            }
        })
        .catch(error => {
            console.error('Error updating progress for task', taskId, ':', error);
        });
}


function startProgressUpdate(taskId) {
    if (progressTimers[taskId]) {
        clearInterval(progressTimers[taskId]);
    }
    updateProgress(taskId);
    progressTimers[taskId] = setInterval(() => updateProgress(taskId), 500);
}

function startAllProgressUpdates() {
    const tasks = document.querySelectorAll('.task.downloading, .task.paused');
    tasks.forEach(task => {
        const taskId = task.id.replace('task-', '');
        startProgressUpdate(taskId);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(startAllProgressUpdates, 100);
});