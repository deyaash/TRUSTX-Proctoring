// ══════════════════════════════════════════════════
//  Language System
// ══════════════════════════════════════════════════
let currentLang = localStorage.getItem('quizLang') || 'ar';

const LANG = {
    ar: {
        cheatTitle:     'تحذير غش!',
        expelTitle:     'تم طردك من الامتحان!',
        expelMsg:       'وصلت للحد الأقصى من محاولات الغش.',
        expelTimer:     'سيتم تحويلك خلال 5 ثوانٍ...',
        tabSwitch:      'تم اكتشاف فتح تبويب أو نافذة جديدة!',
        winBlur:        'تم اكتشاف مغادرة نافذة الامتحان!',
        attemptOf:      'محاولة',
        of:             'من',
        timeOff:        'انتهى الوقت',
        congrats:       'أحسنت! حصلت على',
        nice:           'جيد، حصلت على',
        outOf:          'من',
        // حالة الكشف
        face_ok:       'مكتشف ✓',
        face_none:     'لا يوجد وجه ⚠',
        face_multi:    'وجوه متعددة ⚠',
        face_wait:     'جارٍ الكشف...',
        gaze_center:   'مركز ✓',
        gaze_left:     'يسار ⚠',
        gaze_right:    'يمين ⚠',
        gaze_up:       'لأعلى',
        gaze_down:     'لأسفل',
        phone_no:      'لا يوجد ✓',
        phone_yes:     'مكتشف! 🚨',
        chip_face_ok:  'وجه: مكتشف',
        chip_face_no:  'وجه: غائب',
        chip_face_mul: 'وجه: متعدد',
        chip_gaze_ok:  'نظر: مركز',
        chip_gaze_l:   'نظر: يسار ⚠',
        chip_gaze_r:   'نظر: يمين ⚠',
        chip_phone_no: 'لا تلفون',
        chip_phone_yes:'تلفون! 🚨',
        log_start:     'بدأ الامتحان — بدأت المراقبة',
        score_label:   'درجتك',
    },
    en: {
        cheatTitle:     'Cheating Detected!',
        expelTitle:     'You Have Been Expelled!',
        expelMsg:       'You reached the maximum cheating attempts.',
        expelTimer:     'Redirecting in 5 seconds...',
        tabSwitch:      'New tab or window detected!',
        winBlur:        'You left the exam window!',
        attemptOf:      'Attempt',
        of:             'of',
        timeOff:        'Time Off',
        congrats:       'Congrats! You got',
        nice:           'Nice! You got',
        outOf:          'out of',
        face_ok:       'Detected ✓',
        face_none:     'No face ⚠',
        face_multi:    'Multiple faces ⚠',
        face_wait:     'Initializing...',
        gaze_center:   'Center ✓',
        gaze_left:     'Left ⚠',
        gaze_right:    'Right ⚠',
        gaze_up:       'Up',
        gaze_down:     'Down',
        phone_no:      'Clear ✓',
        phone_yes:     'Detected! 🚨',
        chip_face_ok:  'Face: OK',
        chip_face_no:  'Face: Missing',
        chip_face_mul: 'Face: Multiple',
        chip_gaze_ok:  'Gaze: Center',
        chip_gaze_l:   'Gaze: Left ⚠',
        chip_gaze_r:   'Gaze: Right ⚠',
        chip_phone_no: 'No Phone',
        chip_phone_yes:'Phone! 🚨',
        log_start:     'Exam started — Proctoring active',
        score_label:   'Your Score',
    }
};

function t(key) { return (LANG[currentLang] || LANG.ar)[key] || key; }

function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('quizLang', lang);

    const root = document.getElementById('htmlRoot');
    if (root) { root.lang = lang; root.dir = lang === 'ar' ? 'rtl' : 'ltr'; }

    // نص كل العناصر اللي عندها data-ar/data-en
    document.querySelectorAll('[data-ar][data-en]').forEach(el => {
        el.textContent = el.dataset[lang];
    });

    const lbl = document.getElementById('langLabel');
    if (lbl) lbl.textContent = lang === 'ar' ? 'EN' : 'عر';

    // أعد رسم حالة الكشف بالنصوص الصحيحة
    if (_lastStatus) updateDetUI(_lastStatus);
}

function toggleLang() { applyLanguage(currentLang === 'ar' ? 'en' : 'ar'); }


// ══════════════════════════════════════════════════
//  Helpers
// ══════════════════════════════════════════════════
function toArabicNum(n) {
    return currentLang === 'ar'
        ? n.toString().replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d])
        : n.toString();
}

function nowTimeStr() {
    return new Date().toLocaleTimeString('ar-SA', { hour12: true });
}

function addLogEntry(text, cls = '') {
    const list = document.getElementById('liveLog');
    if (!list) return;
    const row = document.createElement('div');
    row.className = 'log-entry';
    row.innerHTML =
        '<span class="log-time">' + nowTimeStr() + '</span>' +
        '<span class="log-text ' + cls + '">' + text + '</span>';
    list.insertBefore(row, list.firstChild);
    while (list.children.length > 20) list.removeChild(list.lastChild);
}


// ══════════════════════════════════════════════════
//  Exit Confirmation
// ══════════════════════════════════════════════════
function confirmExit() {
    const msg = currentLang === 'ar'
        ? 'هل أنت متأكد من الخروج؟ سيتم إلغاء الامتحان.'
        : 'Are you sure you want to exit? The exam will be cancelled.';
    if (confirm(msg)) {
        clearInterval(examTimerInterval);
        clearInterval(proctoringInterval);
        window.location.href = '/dashboard';
    }
}

// ══════════════════════════════════════════════════
//  Questions (loaded from server)
// ══════════════════════════════════════════════════
let questions = [];

async function loadExamData() {
    console.log('[Quiz] EXAM_ID =', typeof EXAM_ID !== 'undefined' ? EXAM_ID : 'UNDEFINED');
    if (typeof EXAM_ID === 'undefined' || EXAM_ID === null || EXAM_ID === '') {
        console.warn('[Quiz] No EXAM_ID — questions will not load');
        return;
    }
    try {
        const url = '/exam_data/' + EXAM_ID;
        console.log('[Quiz] Fetching', url);
        const res  = await fetch(url);
        console.log('[Quiz] Response status:', res.status);
        if (!res.ok) { console.error('[Quiz] Server returned error:', res.status); return; }
        const data = await res.json();
        console.log('[Quiz] Exam data received:', data);
        questions = Array.isArray(data.questions) ? data.questions : [];
        console.log('[Quiz] Questions count:', questions.length);

        const titleEl = document.getElementById('examTitle');
        if (titleEl && data.title) {
            titleEl.textContent = data.title;
            titleEl.dataset.ar  = data.title;
            titleEl.dataset.en  = data.title;
        }
        if (data.duration && data.duration > 0) {
            examTimeLeft = data.duration * 60;
            renderTimer();
        }
        renderAllQuestions();
    } catch (e) {
        console.error('[Quiz] Failed to load exam:', e);
    }
}

// ══════════════════════════════════════════════════
//  Render All Questions
// ══════════════════════════════════════════════════
function renderAllQuestions() {
    const container = document.getElementById('questionsContainer');
    if (!container || !questions.length) return;

    container.innerHTML = '';

    questions.forEach((q, i) => {
        const card = document.createElement('div');
        card.className = 'q-card';
        card.id = 'qcard' + i;

        const numLabel = toArabicNum(i + 1) + '.';

        const optionsHTML = q.options.map((opt, j) =>
            '<label class="q-option" id="opt_' + i + '_' + j + '">' +
            '<input type="radio" name="q' + i + '" value="' + escHtml(opt) + '" ' +
            'onchange="onOptionChange(' + i + ',this)">' +
            '<span>' + escHtml(opt) + '</span>' +
            '</label>'
        ).join('');

        card.innerHTML =
            '<div class="q-header">' +
            '<span class="q-num">' + numLabel + '</span>' +
            '<span class="q-text">' + escHtml(q.question) + '</span>' +
            '</div>' +
            '<div class="q-options">' + optionsHTML + '</div>';

        container.appendChild(card);
    });
}

function escHtml(str) {
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function onOptionChange(qIndex, input) {
    const card = document.getElementById('qcard' + qIndex);
    if (card) card.classList.add('answered');
}

window.addEventListener('load', async () => {
    applyLanguage(currentLang);
    startExamTimer();
    await loadExamData();
    startProctoringPoll();
    addLogEntry(t('log_start'), 'log-start');
});


// ══════════════════════════════════════════════════
//  Submit Exam
// ══════════════════════════════════════════════════
function submitExam() {
    if (expelled) return;
    clearInterval(examTimerInterval);
    clearInterval(proctoringInterval);

    let score = 0;
    questions.forEach((q, i) => {
        const sel = document.querySelector('input[name="q' + i + '"]:checked');
        if (sel && sel.value === q.answer) {
            score++;
            // لوّن الخيار الصح
            document.querySelectorAll('input[name="q' + i + '"]').forEach(r => {
                r.closest('.q-option').classList.toggle('opt-correct', r.value === q.answer && r.checked);
                r.closest('.q-option').classList.toggle('opt-incorrect', r.value !== q.answer && r.checked);
            });
        } else {
            // لوّن الإجابة الصح + الغلط
            document.querySelectorAll('input[name="q' + i + '"]').forEach(r => {
                if (r.value === q.answer) r.closest('.q-option').classList.add('opt-correct');
                if (r.checked && r.value !== q.answer) r.closest('.q-option').classList.add('opt-incorrect');
            });
        }
        // أوقف التفاعل
        document.querySelectorAll('input[name="q' + i + '"]').forEach(r => r.disabled = true);
    });

    showResult(score);
}

function sendResult(score) {
    if (!EXAM_ID) return;
    fetch('/submit_result', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            exam_id:      EXAM_ID,
            student_name: (typeof STUDENT_NAME !== 'undefined' && STUDENT_NAME) ? STUDENT_NAME : 'غير معروف',
            score:        score,
            total:        questions.length,
            violations:   violations,
            cheat_events: cheatLog
        })
    }).catch(e => console.warn('Could not send result:', e));
}

function showResult(score) {
    sendResult(score);

    const overlay  = document.getElementById('resultOverlay');
    const scoreEl  = document.getElementById('resultScore');
    const titleEl  = document.getElementById('resultTitle');
    if (!overlay) return;

    const prefix = score > Math.floor(questions.length / 2) ? t('congrats') : t('nice');
    scoreEl.innerHTML =
        prefix + ' <strong>' + score + '</strong> ' + t('outOf') + ' ' + questions.length;
    if (titleEl) titleEl.textContent = titleEl.dataset[currentLang] || titleEl.textContent;

    overlay.style.display = 'flex';
    setTimeout(() => { window.location.href = '/dashboard'; }, 10000);
}


// ══════════════════════════════════════════════════
//  Exam Timer  (15 minutes total)
// ══════════════════════════════════════════════════
const EXAM_MINUTES  = 15;
const EXAM_SECS     = EXAM_MINUTES * 60;
let examTimeLeft    = EXAM_SECS;
let examTimerInterval = null;

function startExamTimer() {
    examTimeLeft = EXAM_SECS;
    renderTimer();
    examTimerInterval = setInterval(() => {
        if (expelled) return;
        examTimeLeft--;
        renderTimer();
        if (examTimeLeft <= 0) {
            clearInterval(examTimerInterval);
            submitExam();
        }
    }, 1000);
}

function renderTimer() {
    const el = document.getElementById('hdrTimer');
    if (!el) return;
    const m = Math.floor(examTimeLeft / 60);
    const s = examTimeLeft % 60;
    el.textContent = String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    el.className = 'hdr-timer';
    if (examTimeLeft <= 120) el.classList.add('warn');
    if (examTimeLeft <= 60)  el.classList.replace('warn', 'danger');
}


// ══════════════════════════════════════════════════
//  Cheat Detection
// ══════════════════════════════════════════════════
const MAX_VIOLATIONS = 5;
let violations       = 0;
let lastCheatTime    = 0;
let expelled         = false;
let proctoringInterval = null;
const cheatLog       = [];   // سجل كامل لأحداث الغش

function recordCheat(reason) {
    if (expelled) return;
    const now = Date.now();
    if (now - lastCheatTime < 2000) return;
    lastCheatTime = now;

    violations++;
    cheatLog.push({ time: new Date().toLocaleTimeString('ar-SA'), reason });
    document.getElementById('violBadgeHdr').textContent = violations;
    addLogEntry(reason, 'log-cheat');

    if (violations >= MAX_VIOLATIONS) {
        expelStudent();
    } else {
        showCheatWarn(reason, violations);
    }
}

function showCheatWarn(reason, n) {
    const overlay = document.getElementById('cheatOverlay');
    if (!overlay) return;
    overlay.classList.remove('expelled');
    document.getElementById('cheatIcon').textContent    = '⚠️';
    document.getElementById('cheatTitle').textContent   = t('cheatTitle');
    document.getElementById('cheatMsg').textContent     = reason;
    document.getElementById('cheatCounter').textContent =
        t('attemptOf') + ' ' + n + ' ' + t('of') + ' ' + MAX_VIOLATIONS;
    overlay.classList.add('active');
    setTimeout(() => overlay.classList.remove('active'), 4000);
}

function expelStudent() {
    expelled = true;
    clearInterval(examTimerInterval);
    clearInterval(proctoringInterval);

    const overlay = document.getElementById('cheatOverlay');
    if (!overlay) return;
    overlay.classList.add('active', 'expelled');
    document.getElementById('cheatIcon').textContent    = '🚫';
    document.getElementById('cheatTitle').textContent   = t('expelTitle');
    document.getElementById('cheatMsg').textContent     = t('expelMsg');
    document.getElementById('cheatCounter').textContent = t('expelTimer');

    setTimeout(() => { window.location.href = '/dashboard'; }, 5000);
}

// كشف تبديل التبويب
document.addEventListener('visibilitychange', () => {
    if (document.hidden) recordCheat(t('tabSwitch'));
});
window.addEventListener('blur', () => {
    if (!document.hidden) recordCheat(t('winBlur'));
});

// حالة الكاميرا في الـ chip
function setCamChip(active) {
    const chip = document.getElementById('chipCam');
    if (!chip) return;
    const dot = chip.querySelector('.chip-dot');
    chip.className = 'chip chip-cam ' + (active ? 'st-ok' : 'st-danger');
    if (dot) dot.className = 'chip-dot ' + (active ? 'chip-ok' : 'chip-danger');
}

// راقب حالة الكاميرا (MJPEG stream — polling أكثر موثوقية من حدث load)
window.addEventListener('load', () => {
    const vid = document.getElementById('videoElement');
    if (!vid) return;

    // اكتشاف خطأ فوري (منفذ مغلق / كاميرا غير متاحة)
    vid.addEventListener('error', () => {
        setCamChip(false);
    }, { once: true });

    // تحقق مرة كل ثانية حتى نحصل على فريم أو نصل للحد
    let tries = 0;
    const camPoll = setInterval(() => {
        tries++;
        if (vid.naturalWidth > 0) {
            setCamChip(true);
            clearInterval(camPoll);
        } else if (tries >= 8) {
            // بعد 8 ثوانٍ بدون فريم → كاميرا غير متاحة
            setCamChip(false);
            clearInterval(camPoll);
        }
    }, 1000);
});

// حالة النافذة في الـ chip
function setWindowChip(active) {
    const chip = document.getElementById('chipWindow');
    if (!chip) return;
    const dot = chip.querySelector('.chip-dot');
    chip.className = 'chip ' + (active ? 'st-ok' : 'st-warn');
    if (dot) { dot.className = 'chip-dot ' + (active ? 'chip-ok' : 'chip-warn'); }
}
document.addEventListener('visibilitychange', () => setWindowChip(!document.hidden));
window.addEventListener('focus', () => setWindowChip(true));
window.addEventListener('blur',  () => setWindowChip(false));


// ══════════════════════════════════════════════════
//  Detection Status UI
// ══════════════════════════════════════════════════
let _lastStatus = null;

function updateDetUI(s) {
    _lastStatus = s;

    // ── تفاصيل الـ sidebar ─────────────────────────
    const faceRow  = document.getElementById('detFaceRow');
    const gazeRow  = document.getElementById('detGazeRow');
    const headRow  = document.getElementById('detHeadRow');
    const phoneRow = document.getElementById('detPhoneRow');

    if (faceRow) {
        const map = { ok:'face_ok', none:'face_none', multiple:'face_multi', searching:'face_wait' };
        faceRow.textContent = t(map[s.face] || 'face_wait');
        faceRow.className   = 'det-val ' + (s.face === 'ok' ? 'det-ok' : s.face === 'searching' ? '' : 'det-danger');
    }
    if (gazeRow) {
        const map = { center:'gaze_center', left:'gaze_left', right:'gaze_right', up:'gaze_up', down:'gaze_down' };
        gazeRow.textContent = t(map[s.gaze] || 'gaze_center');
        gazeRow.className   = 'det-val ' + (s.gaze === 'center' ? 'det-ok' : 'det-warn');
    }
    if (headRow) {
        const map = { center:'gaze_center', left:'gaze_left', right:'gaze_right', up:'gaze_up', down:'gaze_down' };
        headRow.textContent = t(map[s.head] || 'gaze_center');
        headRow.className   = 'det-val ' + (s.head === 'center' ? 'det-ok' : 'det-warn');
    }
    if (phoneRow) {
        phoneRow.textContent = t(s.phone ? 'phone_yes' : 'phone_no');
        phoneRow.className   = 'det-val ' + (s.phone ? 'det-danger' : 'det-ok');
    }
    const audioRow = document.getElementById('detAudioRow');
    if (audioRow) {
        const loud = s.audio === 'loud';
        audioRow.textContent = loud
            ? (currentLang === 'ar' ? 'صوت مكتشف ⚠' : 'Audio Detected ⚠')
            : (currentLang === 'ar' ? 'هادئ ✓' : 'Quiet ✓');
        audioRow.className = 'det-val ' + (loud ? 'det-danger' : 'det-ok');
    }

    // ── chips الهيدر ───────────────────────────────
    const chipFace  = document.getElementById('chipFace');
    const chipFaceT = document.getElementById('chipFaceTxt');
    const chipGaze  = document.getElementById('chipGaze');
    const chipGazeT = document.getElementById('chipGazeTxt');
    const chipPhone = document.getElementById('chipPhone');
    const chipPhoneT= document.getElementById('chipPhoneTxt');

    if (chipFace && chipFaceT) {
        const ok = s.face === 'ok';
        const mul = s.face === 'multiple';
        chipFace.className = 'chip ' + (ok ? 'st-ok' : mul ? 'st-danger' : 'st-warn');
        const dot = chipFace.querySelector('.chip-dot');
        if (dot) dot.className = 'chip-dot ' + (ok ? 'chip-ok' : mul ? 'chip-danger' : 'chip-warn');
        chipFaceT.textContent = t(ok ? 'chip_face_ok' : mul ? 'chip_face_mul' : 'chip_face_no');
    }
    if (chipGaze && chipGazeT) {
        const ok = s.gaze === 'center';
        chipGaze.className = 'chip ' + (ok ? 'st-ok' : 'st-warn');
        const dot = chipGaze.querySelector('.chip-dot');
        if (dot) dot.className = 'chip-dot ' + (ok ? 'chip-ok' : 'chip-warn');
        const map = { center:'chip_gaze_ok', left:'chip_gaze_l', right:'chip_gaze_r' };
        chipGazeT.textContent = t(map[s.gaze] || 'chip_gaze_ok');
    }
    if (chipPhone && chipPhoneT) {
        chipPhone.className = 'chip ' + (s.phone ? 'st-danger' : 'st-ok');
        const dot = chipPhone.querySelector('.chip-dot');
        if (dot) dot.className = 'chip-dot ' + (s.phone ? 'chip-danger' : 'chip-ok');
        chipPhoneT.textContent = t(s.phone ? 'chip_phone_yes' : 'chip_phone_no');
    }
}


// ══════════════════════════════════════════════════
//  Proctoring Poll  (2.5s interval)
// ══════════════════════════════════════════════════
function startProctoringPoll() {
    proctoringInterval = setInterval(async () => {
        if (expelled) return;
        try {
            const res  = await fetch('/proctoring_data');
            const data = await res.json();

            for (const evt of (data.events || [])) {
                const reason = (evt.reason || {})[currentLang] || (evt.reason || {}).ar || '';
                if (reason) recordCheat(reason);
            }

            if (data.status) updateDetUI(data.status);
        } catch (_) {}
    }, 2500);
}
