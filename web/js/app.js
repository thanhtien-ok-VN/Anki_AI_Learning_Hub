const App = (() => {
  const games = [
    ['fill_blank', '✍️', 'Fill in the Blank'],
    ['cloze', '📖', 'Cloze'],
    ['translation', '🌐', 'Translation'],
    ['unscramble', '🧩', 'Word Unscramble'],
    ['matching', '🔗', 'Word Matching'],
    ['story', '📚', 'Story'],
    ['sentence_transform', '🔄', 'Sentence Transform'],
    ['taboo', '🚫', 'Taboo']
  ];
  window.HubGames = games;

  // ╔══════════════════════════════════════════════════════════════╗
  // ║  SECTION 1: STATE & PREFERENCES                             ║
  // ╚══════════════════════════════════════════════════════════════╝
  const state = window.HubState || {
    route: 'home',
    decks: [],
    pairs: [],
    seen: new Set(),
    exercise: null,
    index: 0,
    answers: {},
    busy: false,
    history: {},
    userPrefs: {},
    matchingStats: null,
    supportedLanguages: [],
    uiLanguages: ['en', 'vi'],
    hintedQuestions: new Set(),
    tabooOrder: [],
    tabooCursor: 0
  };
  window.HubState = state;

  const persistence = window.HubPersistence || {};

  function loadPrefs() {
    if (persistence.loadPrefs) persistence.loadPrefs(state);
  }

  function loadMatchingStats() {
    if (persistence.loadMatchingStats) persistence.loadMatchingStats(state);
  }

  function saveMatchingStats() {
    if (persistence.saveMatchingStats) persistence.saveMatchingStats(state);
  }

  function loadHistory() {
    if (persistence.loadHistory) persistence.loadHistory(state);
  }

  function saveHistory() {
    if (persistence.saveHistory) persistence.saveHistory(state);
  }

  function savePrefs() {
    if (persistence.savePrefs) persistence.savePrefs(state);
  }

  function debouncedSavePrefs(delayMs = 300) {
    if (persistence.debouncedSavePrefs) persistence.debouncedSavePrefs(state, delayMs);
  }

  function flushSavePrefs() {
    if (persistence.flushSavePrefs) persistence.flushSavePrefs(state);
  }

  function restorePrefs() {
    if (persistence.restorePrefs) {
      persistence.restorePrefs(state, () => {
        if (window.HubSource && window.HubSource.preview) window.HubSource.preview();
      });
    }
  }

  function clearPrefs() {
    if (persistence.clearPrefs) persistence.clearPrefs(state);
  }

  let currentAbortController = new AbortController();

  function abortActiveRequests() {
    if (currentAbortController) {
      currentAbortController.abort();
    }
    currentAbortController = new AbortController();
    if (typeof Bridge !== 'undefined' && Bridge.abortAll) {
      Bridge.abortAll();
    }
  }

  function getSignal() {
    if (!currentAbortController || currentAbortController.signal.aborted) {
      currentAbortController = new AbortController();
    }
    return currentAbortController.signal;
  }

  loadPrefs();
  loadHistory();

  // ╔══════════════════════════════════════════════════════════════╗
  // ║  SECTION 2: CORE HELPERS & UTILITIES                        ║
  // ╚══════════════════════════════════════════════════════════════╝
  const t = (key, fallback, ...args) => {
    if (window.Utils && typeof window.Utils.t === 'function') {
      return window.Utils.t(key, fallback, ...args);
    }
    if (typeof window.t === 'function' && window.t !== t) {
      return window.t(key, fallback, ...args);
    }
    let text = fallback || key;
    if (args.length > 0) {
      args.forEach((val, idx) => {
        text = text.replace(new RegExp('\\{' + idx + '\\}', 'g'), val ?? '');
      });
    }
    return text;
  };
  window.t = t;

  const normalizeText = text => {
    if (!text) return "";
    return String(text)
      .trim()
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[.,!?;:]$/, '')
      .replace(/\s+/g, ' ');
  };
  const norm = normalizeText;

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  window.esc = esc;

  const renderExplanationBox = (text, title) => {
    if (window.renderExplanationBox && window.renderExplanationBox !== renderExplanationBox) {
      return window.renderExplanationBox(text, title);
    }
    if (!text || typeof text !== 'string') return '';
    const trimmed = text.trim();
    if (!trimmed || trimmed === 'null' || trimmed === 'undefined') return '';
    const displayTitle = title || t('app.explanation_title', '💡 Giải thích từ AI');
    return `<div class="explanation-card"><h4>${esc(displayTitle)}</h4><div class="explanation-content">${esc(trimmed)}</div></div>`;
  };
  window.renderExplanationBox = renderExplanationBox;

  const timers = new Set();
  const activeIntervals = new Set();

  const setSafeTimeout = (fn, delay) => {
    let id;
    id = setTimeout(() => {
      timers.delete(id);
      fn();
    }, delay);
    timers.add(id);
    return id;
  };

  const clearSafeTimeout = id => {
    if (id !== undefined && id !== null) {
      clearTimeout(id);
      timers.delete(id);
    }
  };

  const setSafeInterval = (fn, delay) => {
    const id = setInterval(fn, delay);
    activeIntervals.add(id);
    return id;
  };

  const clearSafeInterval = id => {
    if (id !== undefined && id !== null) {
      clearInterval(id);
      activeIntervals.delete(id);
    }
  };

  const disposeCurrentGame = () => {
    for (const id of timers) {
      clearTimeout(id);
    }
    timers.clear();
    for (const id of activeIntervals) {
      clearInterval(id);
    }
    activeIntervals.clear();
  };

  const shuffleArray = arr => {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = a[i];
      a[i] = a[j];
      a[j] = tmp;
    }
    return a;
  };

  let _sharedAudioCtx = null;
  const getSharedAudioContext = () => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      if (!_sharedAudioCtx || _sharedAudioCtx.state === 'closed') {
        _sharedAudioCtx = new AudioCtx();
      }
      if (_sharedAudioCtx.state === 'suspended') {
        _sharedAudioCtx.resume().catch(() => {});
      }
      return _sharedAudioCtx;
    } catch (_) {
      return null;
    }
  };

  const closeSharedAudioContext = () => {
    if (_sharedAudioCtx && _sharedAudioCtx.state !== 'closed') {
      try {
        _sharedAudioCtx.close().catch(() => {});
      } catch (_) {}
      _sharedAudioCtx = null;
    }
  };

  window.addEventListener('beforeunload', closeSharedAudioContext);
  window.addEventListener('pagehide', closeSharedAudioContext);

  const statusState = { key: '', shownAt: 0, timeoutId: null };
  const bridgeMessage = error => {
    if (error?.message && typeof error.message === 'string' && error.message.length > 0 && !error.message.includes('The AI Hub could not')) {
      return error.message;
    }
    const messages = {
      E_RATE_LIMIT: t('app.ai_rate_limited', 'AI đang bận. Vui lòng thử lại sau.'),
      E_API_ERROR: t('app.ai_unavailable', 'AI hiện tạm không khả dụng. Vui lòng thử lại sau.'),
      E_NO_KEYS: t('app.ai_no_keys', 'Chưa có API key. Hãy cấu hình trong phần cài đặt.'),
      E_TIMEOUT: t('app.ai_timeout', 'Yêu cầu AI mất quá nhiều thời gian.'),
      E_INTERNAL: t('app.ai_internal_error', 'AI Hub không thể hoàn tất yêu cầu này.'),
      E_BACKGROUND: t('app.ai_internal_error', 'AI Hub không thể hoàn tất yêu cầu này.'),
      E_BRIDGE: t('app.ai_internal_error', 'AI Hub không thể hoàn tất yêu cầu này.'),
      E_BRIDGE_NETWORK: t('app.ai_internal_error', 'AI Hub không thể hoàn tất yêu cầu này.'),
      E_BRIDGE_PARSE: t('app.ai_internal_error', 'AI Hub không thể hoàn tất yêu cầu này.'),
      E_PYCMD: t('app.ai_internal_error', 'AI Hub không thể hoàn tất yêu cầu này.'),
      E_AI_CONTENT: t('app.ai_content_invalid', 'Nội dung do AI tạo ra không hợp lệ. Vui lòng thử lại.'),
    };
    if (error?.error_code === 'E_AI_CONTENT' && error?.message) {
      console.warn('[AI Hub] Content validation failure detail:', error.message);
    }
    return messages[error?.error_code] || error?.message || t('app.operation_failed', 'Thao tác không thể hoàn tất.');
  };

  const clearStatus = () => {
    const banner = document.querySelector('#status-banner');
    if (!banner) return;
    banner.hidden = true;
    banner.className = 'status-banner';
    statusState.key = '';
    statusState.shownAt = 0;
    if (statusState.timeoutId) {
      clearTimeout(statusState.timeoutId);
      statusState.timeoutId = null;
    }
  };

  const showStatus = (error, type = 'error') => {
    const banner = document.querySelector('#status-banner');
    const msgEl = document.querySelector('#status-banner-message');
    const iconEl = document.querySelector('#status-banner-icon');
    if (!banner || !msgEl) return;

    const message = typeof error === 'string' ? error : bridgeMessage(error);
    const key = `${type}:${message}`;
    const now = Date.now();
    if (statusState.key === key && now - statusState.shownAt < 2500) return;

    statusState.key = key;
    statusState.shownAt = now;
    msgEl.textContent = message;
    banner.className = `status-banner status-banner--${type}`;
    if (iconEl) {
      iconEl.textContent = type === 'info' ? 'ℹ️' : (type === 'warn' ? '⚠️' : '⚠️');
    }
    banner.hidden = false;

    if (statusState.timeoutId) clearTimeout(statusState.timeoutId);
    statusState.timeoutId = setTimeout(() => {
      clearStatus();
    }, 8000);
  };

  const showBridgeFailure = error => showStatus(error);
  document.querySelector('#status-banner-close')?.addEventListener('click', clearStatus);

  const getWeakWords = () => (persistence.getWeakWords ? persistence.getWeakWords() : []);
  const addWeakWord = word => { if (persistence.addWeakWord) persistence.addWeakWord(word); };

  // Expose utilities on window
  window.setSafeTimeout = setSafeTimeout;
  window.clearSafeTimeout = clearSafeTimeout;
  window.setSafeInterval = setSafeInterval;
  window.clearSafeInterval = clearSafeInterval;
  window.disposeCurrentGame = disposeCurrentGame;
  window.shuffleArray = shuffleArray;
  window.getSharedAudioContext = getSharedAudioContext;
  window.getSignal = getSignal;
  window.abortActiveRequests = abortActiveRequests;
  window.showStatus = showStatus;
  window.clearStatus = clearStatus;
  window.showBridgeFailure = showBridgeFailure;
  window.getWeakWords = getWeakWords;
  window.addWeakWord = addWeakWord;

  // ╔══════════════════════════════════════════════════════════════╗
  // ║  SECTION 3: ROUTING & SHELL                                 ║
  // ╚══════════════════════════════════════════════════════════════╝
  const nav = r => {
    flushSavePrefs();
    const oldRoute = state.route;
    disposeCurrentGame();
    abortActiveRequests();
    state.route = r;
    location.hash = r === 'home' ? '' : r;
    render();
    if (r !== oldRoute) {
      const eventName = r === 'home' ? 'game_exit' : 'game_enter';
      if (typeof Bridge !== 'undefined' && Bridge.send) {
        Bridge.send('log_event', { event: eventName, game: r, extra: { from: oldRoute } });
      }
    }
  };
  window.nav = nav;

  const getRoot = () => document.querySelector('#app') || document.body;
  const shell = body => {
    state.busy = false;
    const target = getRoot();
    if (target) {
      const curUiLang = (typeof Utils !== 'undefined' && Utils.currentLang) || state.userPrefs?.ui_lang || 'en';
      const uiLangLabel = curUiLang === 'vi' ? 'Tiếng Việt' : 'English';
      const nextUiLang = curUiLang === 'vi' ? 'en' : 'vi';
      const nextLangText = curUiLang === 'vi' ? '🇬🇧 English' : '🇻🇳 Tiếng Việt';

      target.innerHTML = `<div class="timer-bar"><span class="timer-label">${esc(t('app.title', 'AI Learning Hub'))}</span><span id="busy-label"></span><div class="timer-bar-right" style="display:inline-flex;align-items:center;gap:8px;"><button id="toggle-ui-lang" class="btn btn-outline" style="padding:2px 8px;font-size:12px;border-radius:4px;cursor:pointer;" title="${esc(t('app.ui_lang_label', 'Giao diện'))}: ${esc(uiLangLabel)}">${esc(nextLangText)}</button><button id="close-hub" aria-label="${esc(t('app.close_hub', 'Đóng Hub'))}">${esc(t('app.close_hub', 'Đóng Hub'))}</button></div></div>${body}<div id="loading" class="loading-overlay" hidden><div class="spinner"></div><span id="loading-text">${esc(t('app.processing', 'Đang xử lý…'))}</span><button id="loading-cancel-btn" class="btn btn-cancel-gen" style="margin-top:16px;" type="button">${esc(t('app.cancel_gen', 'Hủy tạo bài'))}</button></div>`;

      const langToggle = document.querySelector('#toggle-ui-lang');
      if (langToggle) {
        langToggle.onclick = () => {
          if (window.Utils && typeof window.Utils.switchUiLanguage === 'function') {
            window.Utils.switchUiLanguage(nextUiLang);
          }
        };
      }

      const bootEl = document.querySelector('#boot-overlay');
      if (bootEl) {
        if (typeof bootEl.remove === 'function') {
          bootEl.remove();
        } else if (bootEl.parentNode) {
          bootEl.parentNode.removeChild(bootEl);
        }
      }
    }
    const loadEl = document.querySelector('#loading');
    if (loadEl) loadEl.hidden = true;
  };
  window.shell = shell;

  function setBusy(on, text = t('app.generating', 'Đang tạo bài…')) {
    if (on) clearStatus();
    state.busy = on;
    const busyLabel = document.querySelector('#busy-label');
    if (busyLabel) busyLabel.textContent = on ? ` (${text})` : '';
    const e = document.querySelector('#loading');
    if (e) {
      e.hidden = !on;
      const tEl = document.querySelector('#loading-text');
      if (tEl) tEl.textContent = text;
      const cBtn = document.querySelector('#loading-cancel-btn');
      if (cBtn) {
        cBtn.textContent = text.includes('tạo bài') || text.includes('Generating') ? t('app.cancel_gen', 'Hủy tạo bài') : t('app.cancel_action', 'Hủy thao tác');
        cBtn.onclick = () => {
          try {
            abortActiveRequests();
            if (typeof Bridge !== 'undefined' && Bridge.send) {
              Bridge.send('cancel_gen', {});
            }
          } catch (ex) {
            console.error('Cancel request failed:', ex);
          }
          setBusy(false);
          showStatus(t('app.action_cancelled', 'Đã hủy thao tác.'), 'info');
        };
      }
    }
    document.querySelectorAll('button,input,select,textarea,.back-btn,#back').forEach(x => {
      if (x.id !== 'close-hub' && x.id !== 'loading-cancel-btn') {
        x.disabled = on;
      }
    });
  }
  window.setBusy = setBusy;

  function home() {
    if (window.HubHome && typeof window.HubHome.home === 'function') {
      window.HubHome.home();
      return;
    }
    const manifestList = (typeof window.ManifestClient !== 'undefined' && window.ManifestClient.getAllManifests)
      ? window.ManifestClient.getAllManifests()
      : games.map(g => ({ id: g[0], icon: g[1], default_title: g[2] }));
    shell('<main class="container"><div class="header pt-header"><h1>' + esc(t('app.title', 'AI Learning Hub')) + '</h1><p>' + esc(t('app.home_subtitle', 'Chọn một game để học từ bộ thẻ Anki')) + '</p><div class="api-check"><button class="btn btn-outline" id="test-keys">' + esc(t('app.test_api', 'Kiểm tra API')) + '</button><span id="api-result" aria-live="polite"></span></div></div><div class="game-grid">' + manifestList.map(g => '<button class="game-card" data-game="' + g.id + '"><div class="icon">' + g.icon + '</div><h3>' + esc(t(g.id + '.title', g.default_title || g.id)) + '</h3><p>' + esc(t('desc.' + g.id, 'Luyện tập tương tác')) + '</p></button>').join('') + '</div></main>');
    bindCommon();
    document.querySelectorAll('[data-game]').forEach(e => e.onclick = () => nav(e.dataset.game));
  }

  function controls(id) {
    if (typeof window.ManifestClient !== 'undefined' && window.ManifestClient.renderControlsHtml) {
      return window.ManifestClient.renderControlsHtml(id, {
        esc,
        t,
        buildLanguageOptionsHtml: () => (window.HubSource?.buildLanguageOptionsHtml ? window.HubSource.buildLanguageOptionsHtml() : '')
      });
    }
    let max = id === 'matching' ? 50 : 10, min = id === 'matching' ? 5 : (id === 'story' ? 3 : 1), extra = '';
    if (id === 'cloze') {
      max = 1; min = 1;
      extra = '<label>' + esc(t('controls.num_blanks', 'Số blank')) + '<select id="num_blanks">' + Array.from({ length: 6 }, (_, i) => '<option ' + (i + 5 === 5 ? 'selected' : '') + '>' + (i + 5) + '</option>').join('') + '</select></label>';
    }
    if (id === 'sentence_transform') {
      max = 1; min = 1;
      extra = '<label>' + esc(t('controls.form_type', 'Dạng')) + '<select id="focus"><option value="voice">' + esc(t('controls.voice_passive', 'Voice (Câu bị động)')) + '</option><option value="conditional">' + esc(t('controls.conditional', 'Conditional (Câu điều kiện)')) + '</option><option value="reported">' + esc(t('controls.reported', 'Reported (Câu tường thuật)')) + '</option><option value="comparative">' + esc(t('controls.comparative', 'Comparative (So sánh)')) + '</option></select></label>';
    }
    if (id === 'translation') { max = 1; min = 1; }

    const hideCount = (max === min && min === 1) || id === 'cloze' || id === 'translation' || id === 'sentence_transform';
    const countLabel = id === 'matching' ? t('controls.pair_count', 'Số cặp từ') : t('controls.question_count', 'Số câu');
    const countSelect = hideCount ? '' : '<label>' + esc(countLabel) + '<select id="count">' + Array.from({ length: max - min + 1 }, (_, i) => '<option ' + ((i + min === 10 || (max < 10 && i + min === min)) ? 'selected' : '') + '>' + (i + min) + '</option>').join('') + '</select></label>';

    if (id === 'matching') {
      return '<section class="config-panel"><div class="selector-grid">' + countSelect + '</div><div class="flex items-center flex-wrap gap-3 mt-3"><button class="btn primary" id="generate">' + esc(t('controls.generate', 'Tạo bài')) + '</button></div></section>';
    }

    const langHtml = window.HubSource?.buildLanguageOptionsHtml ? window.HubSource.buildLanguageOptionsHtml() : '';
    return '<section class="config-panel"><div class="selector-grid"><label>' + esc(t('app.language', 'Ngôn ngữ học')) + '<select id="language">' + langHtml + '</select></label><label>' + esc(t('app.level', 'Trình độ')) + '<select id="level"><option value="beginner">' + esc(t('controls.level_beginner', 'A1 - Sơ cấp (Beginner)')) + '</option><option value="elementary">' + esc(t('controls.level_elementary', 'A2 - Sơ trung cấp (Elementary)')) + '</option><option value="intermediate" selected>' + esc(t('controls.level_intermediate', 'B1 - Trung cấp (Intermediate)')) + '</option><option value="upper_intermediate">' + esc(t('controls.level_upper_intermediate', 'B2 - Trung cấp nâng cao (Upper-intermediate)')) + '</option><option value="advanced">' + esc(t('controls.level_advanced', 'C1–C2 - Nâng cao (Advanced)')) + '</option></select></label>' + countSelect + extra + '<label>' + esc(t('app.topic', 'Chủ đề')) + '<input id="topic" placeholder="' + esc(t('app.topic_placeholder', 'Nhập mô tả chủ đề (VD: daily_life)')) + '" value="daily_life"></label></div><div class="flex items-center flex-wrap gap-3 mt-3"><button class="btn primary" id="generate">' + esc(t('controls.generate', 'Tạo bài')) + '</button></div></section>';
  }

  function game() {
    const g = games.find(x => x[0] === state.route) || ['fill_blank', '✍️', 'Fill in the Blank'];
    const titleText = t(g[0] + '.title', g[2]);
    const sourceHtml = window.HubSource?.source ? window.HubSource.source() : '';

    shell(`<main class="container game-page pt-header">
      <div class="game-header">
        <button id="back" class="back-btn">${esc(t('app.back_hub', '← Hub'))}</button>
        <h2 class="game-title">${g[1]} ${esc(titleText)}</h2>
        <button id="open-history-btn" class="history-btn">${esc(t('app.history', '📜 Lịch sử'))}</button>
      </div>
      ${sourceHtml}
      ${controls(g[0])}
      <section id="play" class="play-area"></section>
      
      <div id="history-modal" class="modal-overlay" hidden>
        <div class="modal-content">
          <div class="modal-header">
            <h3 id="history-modal-title">${esc(t('app.history_title', '📜 Lịch sử làm bài'))}</h3>
            <button id="close-history-modal" class="modal-close-btn">${esc(t('app.close', '✕'))}</button>
          </div>
          <div id="history-modal-body" class="modal-body"></div>
        </div>
      </div>
    </main>`);

    bindCommon();
    if (window.HubSource && window.HubSource.bindSource) {
      window.HubSource.bindSource().then(() => {
        restorePrefs();
      });
    } else {
      restorePrefs();
    }

    const gameId = g[0];
    resetGameState(gameId);

    document.querySelector('#back').onclick = () => { savePrefs(); nav('home'); };
    document.querySelector('#generate').onclick = () => { savePrefs(); generate(g[0]); };

    const histBtn = document.querySelector('#open-history-btn');
    if (histBtn) {
      if (g[0] === 'matching') {
        histBtn.style.display = 'inline-flex';
        histBtn.textContent = t('history.stats_title', '📊 Thống kê');
        histBtn.onclick = () => openMatchingStatsModal();
      } else {
        histBtn.style.display = 'inline-flex';
        histBtn.textContent = esc(t('app.history', '📜 Lịch sử'));
        histBtn.onclick = () => openHistoryModal(g[0]);
      }
    }

    const closeBtn = document.querySelector('#close-history-modal');
    if (closeBtn) {
      closeBtn.onclick = () => {
        document.querySelector('#history-modal').hidden = true;
      };
    }

    const modalOverlay = document.querySelector('#history-modal');
    if (modalOverlay) {
      modalOverlay.onclick = (e) => {
        if (e.target === modalOverlay) modalOverlay.hidden = true;
      };
    }
  }

  function bindCommon() {
    const closeBtn = document.querySelector('#close-hub');
    if (closeBtn) {
      closeBtn.onclick = () => {
        if (typeof Bridge !== 'undefined' && Bridge.send) {
          Bridge.send('log_event', { event: 'hub_close' });
          abortActiveRequests();
          clearPrefs();
          Bridge.send('close_hub');
        }
      };
    }
    const cancelBtn = document.querySelector('#loading-cancel-btn');
    if (cancelBtn) {
      cancelBtn.onclick = () => {
        abortActiveRequests();
        setBusy(false);
        showStatus(t('app.cancelled_action', 'Đã hủy thao tác.'));
      };
    }
  }
  window.bindCommon = bindCommon;

  function resetGameState(gameId) {
    state.exercise = null;
    state.answers = {};
    state.isGraded = false;
    state.index = 0;
    state.currentHistoryItem = null;
    state.hintedQuestions = new Set();
    if (window.HintSystem && typeof window.HintSystem.reset === 'function') {
      window.HintSystem.reset();
    }
    if (gameId === 'taboo') {
      state.tabooCursor = 0;
      state.tabooOrder = [];
    }
    const d = document.querySelector('#play');
    if (d) d.innerHTML = '';
  }
  window.resetGameState = resetGameState;

  // ╔══════════════════════════════════════════════════════════════╗
  // ║  SECTION 4: GENERATE & PLAY DISPATCH                        ║
  // ╚══════════════════════════════════════════════════════════════╝
  function normalizeExercise(id, x) {
    if (!x) return x;
    if (id === 'matching' && x.items && !x.pairs) {
      const map = {};
      x.items.forEach(item => {
        if (!map[item.pair_id]) map[item.pair_id] = {};
        if (item.type === 'term') map[item.pair_id].term = item.content;
        else if (item.type === 'definition') map[item.pair_id].definition = item.content;
      });
      x.pairs = Object.keys(map).map(pid => ({
        id: pid,
        term: map[pid].term,
        definition: map[pid].definition
      }));
    }
    if (id === 'unscramble') {
      if (x.sentences && !x.questions) {
        x.questions = x.sentences;
        delete x.sentences;
      }
      if (Array.isArray(x.questions)) {
        x.questions.forEach(q => {
          if (!q.shuffled_words) {
            if (Array.isArray(q.words)) q.shuffled_words = [...q.words];
            else if (q.correct_sentence || q.original) {
              const text = q.correct_sentence || q.original || '';
              q.shuffled_words = shuffleArray(text.trim().split(/\s+/));
            } else {
              q.shuffled_words = [];
            }
          }
          if (!q.correct_sentence && q.original) q.correct_sentence = q.original;
        });
      }
    }
    if (id === 'fill_blank' && !x.questions && x.sentence) {
      x.questions = [x];
    }
    if (id === 'sentence_transform' && !x.questions && x.original) {
      x.questions = [x];
    }
    if (id === 'taboo' && !x.rounds && x.target_word) {
      x.rounds = [x];
    }
    return x;
  }

  function addHistory(id, data) {
    if (id === 'matching') return null;
    if (!state.history) state.history = {};
    if (!state.history[id]) state.history[id] = [];

    let totalQ = 0;
    if (id === 'fill_blank') totalQ = data.questions ? data.questions.length : 0;
    else if (id === 'cloze') totalQ = data.blanks ? data.blanks.length : 0;
    else if (id === 'story') totalQ = data.questions ? data.questions.length : (data.comprehension_questions ? data.comprehension_questions.length : 0);
    else if (id === 'unscramble') totalQ = data.questions ? data.questions.length : (data.sentences ? data.sentences.length : 0);
    else if (id === 'sentence_transform') totalQ = data.questions ? data.questions.length : 0;
    else if (id === 'translation') totalQ = data.sentences ? data.sentences.length : 1;
    else if (id === 'taboo') totalQ = data.rounds ? data.rounds.length : 1;

    const item = {
      time: Date.now(),
      data: JSON.parse(JSON.stringify(data)),
      answers: null,
      score: null,
      total: totalQ
    };
    state.history[id].unshift(item);
    if (state.history[id].length > 20) state.history[id].length = 20;
    state.currentHistoryItem = item;
    saveHistory();
    return item;
  }

  async function generate(id, optsOverride) {
    const signal = getSignal();
    try {
      disposeCurrentGame();
      if (!optsOverride) resetGameState(id);
      setBusy(true);

      if (!state.pairs.length && !optsOverride && window.HubSource?.sample) {
        const sampled = await window.HubSource.sample();
        if (!sampled && signal.aborted) return;
      }
      if (signal.aborted) return;

      if (id === 'matching' && state.pairs.length < 5) {
        showStatus(t('app.not_enough_vocab', 'Không đủ từ vựng để nối {0} cặp. Giảm số cặp hoặc thêm từ.', 5));
        setBusy(false);
        return;
      }

      let opts;
      if (optsOverride) {
        opts = optsOverride;
      } else {
        const lang = document.querySelector('#language');
        if (id !== 'matching' && (!lang || !lang.value)) {
          showStatus(t('app.select_lang_first', 'Hãy chọn ngôn ngữ học trước khi tạo bài.'));
          setBusy(false);
          return;
        }
        const countEl = document.querySelector('#count');
        const levelEl = document.querySelector('#level');
        const topicEl = document.querySelector('#topic');
        opts = {
          gamemode: id,
          language: lang ? lang.value : 'en',
          level: levelEl ? levelEl.value : 'intermediate',
          count: countEl ? +countEl.value : 1,
          topic: topicEl ? topicEl.value : 'daily_life',
          vocab_pairs: state.pairs
        };
        if (id === 'cloze') {
          const nb = document.querySelector('#num_blanks');
          if (nb) opts.num_blanks = +nb.value;
        }
        if (id === 'sentence_transform') {
          const fs = document.querySelector('#focus');
          if (fs) opts.focus = fs.value;
        }
      }
      state.exercise = await Bridge.sendAsync('generate', opts, { signal, timeoutMs: 180000 });
      if (signal.aborted) return;
      state.index = 0;
      state.answers = {};
      state.isGraded = false;

      const historyItem = addHistory(id, state.exercise);
      state.currentHistoryItem = historyItem;

      play(id);
    } catch(e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return;
      showBridgeFailure(e);
    } finally {
      setBusy(false);
    }
  }
  window.generate = generate;

  function play(id) {
    const d = document.querySelector('#play');
    let x = state.exercise;
    if (!x) {
      if (d) d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu bài tập.</p></div>';
      return;
    }
    x = normalizeExercise(id, x);
    if (!state.answers) state.answers = {};

    if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.has(id)) {
      const modeHandler = window.GameRegistry.get(id);
      if (modeHandler && typeof modeHandler.render === 'function') {
        modeHandler.render(x, {
          state,
          esc,
          t,
          playSound: () => {},
          addHistory,
          renderExplanationBox
        });
        return;
      }
    }

    if (id === 'fill_blank' && typeof window.renderFillBlank === 'function') window.renderFillBlank(x);
    else if (id === 'cloze' && typeof window.renderCloze === 'function') window.renderCloze(x);
    else if (id === 'matching' && typeof window.renderMatching === 'function') window.renderMatching(x);
    else if (id === 'unscramble' && typeof window.renderUnscrambleAll === 'function') window.renderUnscrambleAll(x);
    else if (id === 'story' && typeof window.renderStory === 'function') window.renderStory(x);
    else if (id === 'translation' && typeof window.renderTranslation === 'function') window.renderTranslation(x);
    else if (id === 'sentence_transform' && typeof window.renderSentenceTransform === 'function') window.renderSentenceTransform(x);
    else if (id === 'taboo' && typeof window.renderTaboo === 'function') window.renderTaboo(x);
  }
  window.play = play;

  // ╔══════════════════════════════════════════════════════════════╗
  // ║  SECTION 5: HISTORY & STATS MODALS                          ║
  // ╚══════════════════════════════════════════════════════════════╝
  function openHistoryModal(gameId) {
    const modal = document.querySelector('#history-modal');
    if (!modal) return;
    renderHistoryList(gameId);
    modal.hidden = false;
  }

  function renderHistoryList(gameId) {
    const historyList = state.history?.[gameId] || [];
    const container = document.querySelector('#history-modal-body');
    const title = document.querySelector('#history-modal-title');
    if (title) title.textContent = t('app.history_title', '📜 Lịch sử làm bài');

    if (!historyList.length) {
      if (container) container.innerHTML = '<div class="empty-state"><p>' + esc(t('app.no_history', 'Chưa có lịch sử làm bài nào.')) + '</p></div>';
      return;
    }

    const itemsHtml = historyList.map((item, idx) => {
      const timeStr = new Date(item.time).toLocaleString('vi-VN', {
        day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
      });
      const totalQ = item.total || (item.data?.questions?.length) || 0;
      const scoreStr = (item.score !== null && item.score !== undefined)
        ? `<span class="badge-score">${item.score}/${totalQ} câu đúng</span>`
        : `<span class="badge-pending">Chưa chấm điểm</span>`;

      return `
        <div class="history-card" data-history-idx="${idx}">
          <div class="history-card-header">
            <span style="font-weight:600; font-size:14px; color:var(--text);">${timeStr}</span>
            ${scoreStr}
          </div>
          <div class="history-card-sub mb-2">
            Bài tập ${totalQ} câu
          </div>
          <button class="btn btn-outline view-detail-btn" data-idx="${idx}" style="font-size:12px; padding:4px 12px;">
            Xem chi tiết →
          </button>
        </div>
      `;
    }).join('');

    if (container) {
      container.innerHTML = `<div class="history-list-grid">${itemsHtml}</div>`;
      container.querySelectorAll('.view-detail-btn').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          renderHistoryDetail(gameId, +btn.dataset.idx);
        };
      });
    }
  }

  function renderHistoryDetail(gameId, idx) {
    const item = state.history?.[gameId]?.[idx];
    if (!item) return;

    const container = document.querySelector('#history-modal-body');
    const title = document.querySelector('#history-modal-title');
    if (title) title.textContent = '🔍 Chi tiết bài làm';

    const timeStr = new Date(item.time).toLocaleString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    let detailContent = '';

    if (gameId === 'fill_blank' && item.data?.questions) {
      const questions = item.data.questions;
      const userAnswers = item.answers || {};
      const formatSentence = window.formatSentenceWithBlank;
      const buildDetails = window.buildOptionDetailsHtml;

      detailContent = questions.map((q, qIdx) => {
        const chosen = userAnswers[qIdx];
        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;
        const isCorrect = chosen === correctIdx;

        const rawSentence = q.sentence_with_blank || q.sentence || '';
        const correctOpt = q.options && q.options.find(o => typeof o === 'object' ? o.is_correct : false);
        const correctWord = q.target_word || (correctOpt ? correctOpt.word : '');
        const chosenOpt = (chosen !== undefined && q.options && q.options[chosen]);
        const chosenWord = chosenOpt ? (typeof chosenOpt === 'object' ? chosenOpt.word : chosenOpt) : '';
        const sentenceHtml = formatSentence ? formatSentence(rawSentence, chosenWord, chosen !== undefined, isCorrect, correctWord) : rawSentence;

        const trans = q.full_translation || q.sentence_translation || q.full_sentence_translation || 'Không có bản dịch';
        const explanation = q.explanation || q.explanation_short || '';

        return `
          <div class="question-card mb-4">
            <div class="q-number">Câu ${qIdx + 1}/${questions.length}</div>
            <div class="q-text" style="font-size:16px; font-weight:600;">${sentenceHtml}</div>

            <div class="feedback ${chosen !== undefined ? (isCorrect ? 'good' : 'bad') : ''} mt-3">
              ${chosen !== undefined ? `
                <div class="font-bold text-md mb-2 ${isCorrect ? 'text-success' : 'text-error'}">
                  ${isCorrect ? 'Chính xác! ✓' : 'Chưa đúng ✕'}
                </div>
              ` : '<div style="color:var(--text-secondary); margin-bottom:8px;">(Chưa làm bài)</div>'}

              <div class="mb-2">
                <b>🌐 Dịch câu hoàn chỉnh:</b> ${esc(trans)}
              </div>

              <div class="mb-2">
                <b>💡 Lý do chọn:</b> ${esc(explanation)}
              </div>

              ${q.grammar_note ? `<div class="mb-2"><b>📌 Ghi chú ngữ pháp:</b> ${esc(q.grammar_note)}</div>` : ''}

              ${buildDetails ? buildDetails(q, chosen) : ''}
            </div>
          </div>
        `;
      }).join('');
    } else if (gameId === 'cloze' && item.data?.blanks) {
      const data = item.data;
      const userAnswers = item.answers || {};

      const blanksHtml = data.blanks.map((b, bIdx) => {
        const chosen = userAnswers[bIdx];
        const isCorrect = chosen === b.correct_index;
        const correctOpt = b.options?.[b.correct_index] || b.answer || '';
        const chosenOpt = chosen !== undefined && b.options ? b.options[chosen] : 'Chưa chọn';
        const meaning = b.meaning || b.meaning_in_vietnamese || '';

        return `
          <div style="padding:10px; border:1px solid var(--border); border-radius:var(--radius-sm); margin-bottom:10px; background:var(--bg);">
            <b>Blank [${bIdx + 1}]</b>: <b style="color:var(--success);">${esc(correctOpt)}</b> ${meaning ? `(${esc(meaning)})` : ''}
            <div>Kết quả: <span class="font-semibold ${isCorrect ? 'text-success' : 'text-error'}">${isCorrect ? '✓ Đúng' : '✕ Sai'}</span> (Bạn chọn: <i>${esc(chosenOpt)}</i>)</div>
            <div style="font-size:13px; color:var(--text-secondary); margin-top:4px;">💡 ${esc(b.explanation || b.explanation_short || '')}</div>
          </div>
        `;
      }).join('');

      detailContent = `
        <div class="question-card mb-4">
          <p><b>Đoạn văn hoàn chỉnh:</b></p>
          <div style="line-height:1.6; margin-bottom:16px;">${esc(data.full_solution_text || data.paragraph || '')}</div>
          ${blanksHtml}
        </div>
      `;
    } else if (gameId === 'translation' && (item.data?.sentences || item.data?.source_sentence)) {
      const isNewTrans = !item.data.sentences;
      const srcText = isNewTrans ? item.data.source_sentence : item.data.sentences[0].source_text;
      const refText = isNewTrans ? item.data.reference_translation : item.data.sentences[0].target_text;
      const gNotes = isNewTrans ? item.data.grading_rubric : item.data.sentences[0].grammar_notes;
      detailContent = `
        <div class="question-card">
          <p><b>Câu gốc:</b> ${esc(srcText)}</p>
          <p style="color:var(--success); font-weight:600;"><b>Đáp án chuẩn:</b> ${esc(refText)}</p>
          ${gNotes ? `<p style="font-size:13px; color:var(--text-secondary);">💡 ${esc(gNotes)}</p>` : ''}
        </div>
      `;
    } else if (gameId === 'sentence_transform' && (item.data?.questions || item.data?.original)) {
      const isNewTrans = !item.data.questions;
      const original = isNewTrans ? item.data.original : item.data.questions[0].original_sentence;
      const inst = isNewTrans ? item.data.prompt : item.data.questions[0].instruction;
      const expected = isNewTrans ? item.data.expected_answer : item.data.questions[0].expected_answer;
      const gRule = isNewTrans ? item.data.grammar_rule : item.data.questions[0].grammar_rule;
      detailContent = `
        <div class="question-card">
          <p><b>Yêu cầu:</b> ${esc(inst)}</p>
          <p><b>Câu gốc:</b> ${esc(original)}</p>
          <p style="color:var(--success); font-weight:600;"><b>Đáp án:</b> ${esc(expected)}</p>
          ${gRule ? `<p style="font-size:13px; color:var(--text-secondary);">💡 ${esc(gRule)}</p>` : ''}
        </div>
      `;
    } else if (gameId === 'taboo' && (item.data?.rounds || item.data?.target_word)) {
      const target = item.data.target_word || item.data.rounds?.[0]?.target_word || '';
      const forbidden = item.data.taboo_words || item.data.rounds?.[0]?.taboo_words || [];
      const clue = item.data.clue || item.data.rounds?.[0]?.clue || '';
      detailContent = `
        <div class="question-card">
          <p><b>Từ bí mật:</b> <b style="color:var(--primary); font-size:16px;">${esc(target)}</b></p>
          <p><b>Mô tả:</b> ${esc(clue)}</p>
          <p><b>Các từ cấm:</b> ${forbidden.map(w => `<span class="badge-pending" style="margin-right:4px;">🚫 ${esc(w)}</span>`).join('')}</p>
        </div>
      `;
    } else {
      detailContent = `<p><b>Thời gian:</b> ${timeStr}</p><p><b>Nội dung bài tập:</b></p><pre style="white-space:pre-wrap; background:var(--bg); padding:12px; border-radius:var(--radius-sm); font-size:12px;">${esc(JSON.stringify(item.data, null, 2))}</pre>`;
    }

    if (container) {
      container.innerHTML = `
        <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:12px;">
          <button class="btn btn-outline" id="back-to-history-list" style="padding:6px 14px; font-size:13px;">
            ← Quay lại danh sách lịch sử
          </button>
          <span style="font-size:12px; color:var(--text-secondary);">${timeStr}</span>
        </div>
        ${detailContent}
      `;

      const backBtn = document.querySelector('#back-to-history-list');
      if (backBtn) backBtn.onclick = () => renderHistoryList(gameId);
    }
  }

  function openMatchingStatsModal() {
    if (!state.matchingStats) loadMatchingStats();
    const stats = state.matchingStats || { aggregates: {}, records: [] };
    const body = document.querySelector('#history-modal-body');
    const title = document.querySelector('#history-modal-title');
    const modal = document.querySelector('#history-modal');
    if (!body || !title || !modal) return;

    title.textContent = t('stats.title', '📊 Thống kê Nối từ (Word Matching)');

    const bestTimeStr = (stats.aggregates && stats.aggregates.best_time_sec !== 999999) ?
      `${Math.floor(stats.aggregates.best_time_sec / 60)}m ${stats.aggregates.best_time_sec % 60}s` : 'N/A';

    let html = `
      <div class="stats-grid stats-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:20px;">
        <div class="stat-card" style="padding: 12px; background:var(--color-surface-tint); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color: var(--primary);">${stats.aggregates?.total_games || 0}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Số bài đã chơi</div>
        </div>
        <div class="stat-card" style="padding: 12px; background:var(--color-surface-tint); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color: var(--success);">${stats.aggregates?.avg_accuracy || 0}%</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Độ chính xác TB</div>
        </div>
        <div class="stat-card" style="padding: 12px; background:var(--color-surface-tint); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color: var(--primary);">${bestTimeStr}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Thời gian nhanh nhất</div>
        </div>
        <div class="stat-card" style="padding: 12px; background:var(--color-surface-tint); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color:var(--error);">${stats.aggregates?.total_wrong || 0}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Tổng số lần ghép sai</div>
        </div>
      </div>
    `;

    html += `<h4 style="margin: 0 0 10px; font-size:14px; font-weight:700;">📋 30 lượt chơi gần đây</h4>`;
    if (!stats.records || !stats.records.length) {
      html += `<p style="text-align: center; color: var(--text-secondary); font-style: italic; padding: 20px 0; font-size:13px;">Chưa có dữ liệu thống kê nào được ghi nhận.</p>`;
    } else {
      html += `<div style="max-height: 240px; overflow-y: auto; border: 1px solid var(--border); border-radius: 6px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
          <thead>
            <tr style="background:var(--color-surface-tint); border-bottom: 1px solid var(--border);">
              <th style="padding: 8px 12px;">Thời gian</th>
              <th style="padding: 8px 12px;">Số cặp</th>
              <th style="padding: 8px 12px;">Độ chính xác</th>
              <th style="padding: 8px 12px;">Thời gian làm</th>
              <th style="padding: 8px 12px;">Số lần sai</th>
            </tr>
          </thead>
          <tbody>
            ${stats.records.map(r => {
              const dt = new Date(r.time);
              const dtStr = `${dt.getDate()}/${dt.getMonth()+1} ${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`;
              const tStr = `${Math.floor(r.elapsed_sec / 60)}m ${r.elapsed_sec % 60}s`;
              return `
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                  <td style="padding: 8px 12px; color: var(--text-secondary);">${dtStr}</td>
                  <td style="padding: 8px 12px; font-weight: 600;">${r.matched}/${r.pairs}</td>
                  <td style="padding: 8px 12px; color: ${r.accuracy === 100 ? 'var(--success)' : 'inherit'}; font-weight: ${r.accuracy === 100 ? '700' : 'normal'};">${r.accuracy}%</td>
                  <td style="padding: 8px 12px;">${tStr}</td>
                  <td style="padding: 8px 12px; color: ${r.wrong > 0 ? 'var(--error)' : 'inherit'};">${r.wrong}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>`;
    }

    html += `
      <div style="text-align: right; margin-top: 16px;">
        <button class="btn btn-outline" id="clear-matching-stats-btn" style="color:var(--error); border-color: rgba(239, 68, 68, 0.3); padding: 6px 12px; font-size: 12px; font-weight: 600; cursor:pointer;">🗑️ Xóa thống kê</button>
      </div>
    `;

    body.innerHTML = html;
    modal.hidden = false;

    const clearBtn = body.querySelector('#clear-matching-stats-btn');
    if (clearBtn) {
      clearBtn.onclick = () => {
        if (confirm(t('confirm.clear_stats', 'Bạn có chắc chắn muốn xóa toàn bộ dữ liệu thống kê nối từ?'))) {
          state.matchingStats = {
            aggregates: {
              total_games: 0,
              total_correct: 0,
              total_wrong: 0,
              avg_accuracy: 0,
              avg_time_sec: 0,
              best_time_sec: 999999
            },
            records: []
          };
          saveMatchingStats();
          openMatchingStatsModal();
        }
      };
    }
  }

  // ╔══════════════════════════════════════════════════════════════╗
  // ║  SECTION 6: BOOTSTRAP & STARTUP                             ║
  // ╚══════════════════════════════════════════════════════════════╝
  function render() {
    if (state.route === 'home') {
      if (window.HubHome?.home) window.HubHome.home();
      else home();
    } else {
      game();
    }
  }

  async function startApp() {
    const handleSave = () => { flushSavePrefs(); savePrefs(); };
    window.addEventListener('beforeunload', handleSave);
    window.addEventListener('pagehide', handleSave);

    const watchdog = new Promise(resolve => setTimeout(resolve, 4000));

    const bootTask = (async () => {
      if (window.Utils && typeof window.Utils.initI18n === 'function') {
        await window.Utils.initI18n().catch(e => console.warn("initI18n failed:", e));
      }

      if (typeof window.ManifestClient !== 'undefined' && window.ManifestClient.loadManifests) {
        await window.ManifestClient.loadManifests().catch(e => console.warn("loadManifests failed:", e));
      }

      try {
        const settings = await Bridge.sendAsync('get_settings', {}, 2000).catch(() => ({}));
        if (settings && Object.keys(settings).length) Object.assign(state.userPrefs, settings);
        const p = await Bridge.sendAsync('load_prefs', {}, 2000).catch(() => ({}));
        if (p && Object.keys(p).length) Object.assign(state.userPrefs, p);
        state.userPrefs.learn_lang = (settings && settings.learn_lang) || state.userPrefs.learn_lang || state.userPrefs.language || 'en';
        state.userPrefs.language = state.userPrefs.learn_lang;
        document.documentElement.lang = state.userPrefs.ui_lang || 'en';
      } catch (e) { console.warn("Failed to load language settings:", e); }

      try {
        const langsData = await Bridge.sendAsync('get_supported_languages', {}, 2000).catch(() => ({}));
        if (langsData && langsData.learn_languages) {
          state.supportedLanguages = langsData.learn_languages;
          state.uiLanguages = langsData.ui_languages || ['en', 'vi'];
        }
      } catch (e) {
        console.warn("Failed to load supported languages:", e);
      }
    })();

    await Promise.race([bootTask, watchdog]);
    render();
  }

  if (!window.Bridge) window.Bridge = {};
  window.Bridge.updateStatus = function(text) {
    const el = document.querySelector('#loading-text');
    if (el) el.textContent = text;
  };

  const appObj = {
    start: startApp,
    navigate: nav,
    retry: () => { state.answers = {}; game(); }
  };
  window.App = appObj;
  return appObj;
})();

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (window.App && typeof window.App.start === 'function') window.App.start();
  });
} else {
  if (window.App && typeof window.App.start === 'function') window.App.start();
}
