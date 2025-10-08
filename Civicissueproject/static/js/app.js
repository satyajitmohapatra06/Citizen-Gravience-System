document.addEventListener('DOMContentLoaded', () => {
    const languageSwitcher = document.getElementById('language-switcher'); // You will need to add this ID to your language <select> dropdown in the HTML

    const setLanguage = (language) => {
        // --- 1. Translate all elements with 'data-translate' ---
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            const translation = translations[language]?.[key];
            if (translation) {
                element.textContent = translation;
            }
        });

        // --- 2. Translate all placeholders with 'data-translate-placeholder' ---
        document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
            const key = element.getAttribute('data-translate-placeholder');
            const translation = translations[language]?.[key];
            if (translation) {
                element.setAttribute('placeholder', translation);
            }
        });
        
        // --- 3. Set the HTML lang attribute for accessibility ---
        document.documentElement.lang = language;
        
        // --- 4. Save the user's preference in localStorage ---
        localStorage.setItem('language', language);
    };

    // --- Listen for changes on the language switcher dropdown ---
    if (languageSwitcher) {
        languageSwitcher.addEventListener('change', (event) => {
            setLanguage(event.target.value);
        });
    }

    // --- Load the saved language or default to English ('en') ---
    const savedLanguage = localStorage.getItem('language') || 'en';
    if (languageSwitcher) {
        languageSwitcher.value = savedLanguage;
    }
    setLanguage(savedLanguage);
});