// Функция для установки куки
function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

// Функция для получения значения куки по имени
function getCookie(name) {
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i];
        while (cookie.charAt(0) === ' ') {
            cookie = cookie.substring(1);
        }
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length + 1, cookie.length);
        }
    }
    return null;
}

// Функция для установки языка
function setLanguage(language) {
    const elementsToTranslate = document.querySelectorAll('[data-translate]');
    elementsToTranslate.forEach(element => {
        const translationKey = element.getAttribute('data-translate');
        if (translations[translationKey] && translations[translationKey][language]) {
            element.textContent = translations[translationKey][language];
        }
    });

    // Сохраняем выбранный язык в куки
    setCookie('language', language, 30);
}

// Функция для инициализации языка при загрузке страницы
function initializeLanguage() {
    // Пытаемся получить язык из куков
    const savedLanguage = getCookie('language');

    // Если язык сохранен в куки, устанавливаем его
    if (savedLanguage) {
        setLanguage(savedLanguage);
    } else {
        // Иначе устанавливаем английский язык по умолчанию
        setLanguage('en');
    }
}

setInterval(() => document.getElementById('switchToEnglish').addEventListener('click', () => setLanguage('en')), 100);
setInterval(() => document.getElementById('switchToRussian').addEventListener('click', () => setLanguage('ru')), 100);

document.addEventListener('DOMContentLoaded', initializeLanguage);
