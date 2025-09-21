function showHelp() {
    const dialog = document.getElementById('help-dialog');
    const currentLang = localStorage.getItem('language') || 'ru';
    
    // Показываем соответствующий язык
    document.querySelectorAll('[data-language]').forEach(el => {
        el.style.display = el.getAttribute('data-language') === currentLang ? 'block' : 'none';
    });
    
    dialog.showModal();
}