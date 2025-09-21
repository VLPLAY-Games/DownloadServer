function showHelp() {
    const dialog = document.getElementById('help-dialog');
    const currentLang = localStorage.getItem('language') || 'ru';
    
    // Показываем соответствующий язык
    document.querySelectorAll('[data-language]').forEach(el => {
        el.style.display = el.getAttribute('data-language') === currentLang ? 'block' : 'none';
    });
    
    // Показываем диалог с анимацией
    dialog.showModal();
    setTimeout(() => {
        dialog.classList.remove('hide');
        dialog.classList.add('show');
    }, 10);
}

function hideHelp() {
    const dialog = document.getElementById('help-dialog');
    
    // Запускаем анимацию закрытия
    dialog.classList.remove('show');
    dialog.classList.add('hide');
    
    // Закрываем диалог после завершения анимации
    setTimeout(() => {
        dialog.close();
        dialog.classList.remove('hide');
    }, 300);
}

// Ждем загрузки DOM перед добавлением обработчиков
document.addEventListener('DOMContentLoaded', function() {
    const dialog = document.getElementById('help-dialog');
    const closeButton = document.querySelector('.help-dialog-close');
    
    if (dialog) {
        // Отключаем стандартное поведение ESC для этого диалога
        dialog.addEventListener('cancel', function(event) {
            event.preventDefault();
            hideHelp();
        });
        
        // Закрытие по клику вне диалога
        dialog.addEventListener('click', function(event) {
            if (event.target === this) {
                hideHelp();
            }
        });
    }
    
    if (closeButton) {
        closeButton.addEventListener('click', hideHelp);
    }
});