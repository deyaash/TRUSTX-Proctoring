// ── Shared Language Toggle ──────────────────────────────────
(function () {
    let currentLang = localStorage.getItem('quizLang') || 'ar';

    function applyLanguage(lang) {
        currentLang = lang;
        localStorage.setItem('quizLang', lang);
        const root = document.documentElement;
        root.lang = lang;
        root.dir  = lang === 'ar' ? 'rtl' : 'ltr';

        document.querySelectorAll('[data-ar][data-en]').forEach(el => {
            el.textContent = el.dataset[lang];
        });
        document.querySelectorAll('[data-placeholder-ar]').forEach(el => {
            el.placeholder = lang === 'ar' ? el.dataset.placeholderAr : el.dataset.placeholderEn;
        });

        const lbl = document.getElementById('langLabel');
        if (lbl) lbl.textContent = lang === 'ar' ? 'EN' : 'عر';

        // نُطلق حدث مخصص لتمكين الصفحات من التفاعل
        document.dispatchEvent(new CustomEvent('langchange', { detail: lang }));
    }

    window.toggleLang   = function () { applyLanguage(currentLang === 'ar' ? 'en' : 'ar'); };
    window.getCurrentLang = function () { return currentLang; };
    window.applyLanguage  = applyLanguage;

    document.addEventListener('DOMContentLoaded', () => applyLanguage(currentLang));
})();
