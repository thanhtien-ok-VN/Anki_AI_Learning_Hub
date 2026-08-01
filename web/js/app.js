const App = (() => {
  const games = [['fill_blank','✍️','Fill in the Blank'],['cloze','📖','Cloze'],['translation','🌐','Translation'],['unscramble','🧩','Word Unscramble'],['matching','🔗','Word Matching'],['story','📚','Story'],['sentence_transform','🔄','Sentence Transform'],['taboo','🚫','Taboo']];
  const PFX = 'aihub_';

  function loadPrefs() {
    try {
      const p = localStorage.getItem(PFX + 'prefs');
      if (p) Object.assign(state.userPrefs, JSON.parse(p));
    } catch (e) {}
  }

  function loadMatchingStats() {
    try {
      const stats = localStorage.getItem(PFX + 'matching_stats');
      if (stats) {
        state.matchingStats = JSON.parse(stats);
      } else {
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
      }
    } catch (e) {
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
    }
  }

  function saveMatchingStats() {
    try {
      if (state.matchingStats) {
        localStorage.setItem(PFX + 'matching_stats', JSON.stringify(state.matchingStats));
      }
    } catch (e) {}
  }

  function loadHistory() {
    try {
      const h = localStorage.getItem(PFX + 'history');
      if (h) {
        state.history = JSON.parse(h) || {};
        delete state.history['matching'];
      }
      loadMatchingStats();
    } catch (e) {}
  }

  function saveHistory() {
    try {
      if (state.history) {
        delete state.history['matching'];
        localStorage.setItem(PFX + 'history', JSON.stringify(state.history));
      }
    } catch (e) {}
  }

  function savePrefs() {
    const d = document.querySelector('#deck');
    const m = document.querySelector('#model');
    const t = document.querySelector('#term');
    const df = document.querySelector('#definition');
    const l = document.querySelector('#level');
    const c = document.querySelector('#count');
    const tp = document.querySelector('#topic');
    const lg = document.querySelector('#language');
    const nb = document.querySelector('#num_blanks');
    const fs = document.querySelector('#focus');
    const sl = document.querySelector('#sample-limit');

    const p = { ...state.userPrefs };
    if (d && d.value) p.deck = d.value;
    if (m && m.value) p.model = m.value;
    if (t && t.value) p.term = t.value;
    if (df && df.value) p.definition = df.value;
    if (l) p.level = l.value;
    if (c) p.count = c.value;
    if (tp) p.topic = tp.value;
    if (lg) p.language = lg.value;
    if (nb) p.num_blanks = nb.value;
    if (fs) p.focus = fs.value;
    if (sl) p.sample_limit = sl.value;
    p.pairs = state.pairs || [];
    p.seen = Array.from(state.seen || []);

    state.userPrefs = p;
    try {
      localStorage.setItem(PFX + 'prefs', JSON.stringify(p));
    } catch (e) {}
    Bridge.send('save_prefs', p);
  }

  function restorePrefs() {
    const p = state.userPrefs;
    if (!p) return;

    const sl = document.querySelector('#sample-limit');
    if (sl && p.sample_limit) sl.value = p.sample_limit;
    const l = document.querySelector('#level');
    if (l && p.level) l.value = p.level;
    const c = document.querySelector('#count');
    if (c && p.count) c.value = p.count;
    const tp = document.querySelector('#topic');
    if (tp && p.topic) tp.value = p.topic;
    const lg = document.querySelector('#language');
    if (lg && p.language) lg.value = p.language;
    const nb = document.querySelector('#num_blanks');
    if (nb && p.num_blanks) nb.value = p.num_blanks;
    const fs = document.querySelector('#focus');
    if (fs && p.focus) fs.value = p.focus;

    if (p.pairs && Array.isArray(p.pairs) && p.pairs.length) {
      state.pairs = p.pairs;
      if (p.seen && Array.isArray(p.seen)) {
        state.seen = new Set(p.seen);
      }
      preview();
    }
  }

  function clearPrefs() {
    state.userPrefs = {};
    state.pairs = [];
    state.seen.clear();
    try {
      localStorage.removeItem(PFX + 'prefs');
    } catch (e) {}
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

  const state = { route: 'home', decks: [], pairs: [], seen: new Set(), exercise: null, index: 0, answers: {}, busy: false, history: {}, userPrefs: {} };
  loadPrefs();
  loadHistory();

  const root = document.querySelector('#app');
  const t = (key, fallback, ...args) => {
    if (window.t) return window.t(key, fallback, ...args);
    let text = fallback || key;
    if (args.length > 0) {
      args.forEach((val, idx) => {
        text = text.replace(new RegExp('\\{' + idx + '\\}', 'g'), val ?? '');
      });
    }
    return text;
  };
  const normalizeText = text => {
    if (!text) return "";
    return String(text)
      .trim()
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[.,!?;:]$/, '')
      .replace(/\s+/g, ' ');
  };
  const normalizeAnswer = s => normalizeText(s).trim().toLowerCase();
  const norm = normalizeText;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const timers = [];
  const activeIntervals = [];

  const setSafeTimeout = (fn, delay) => {
    const id = setTimeout(fn, delay);
    timers.push(id);
    return id;
  };

  const setSafeInterval = (fn, delay) => {
    const id = setInterval(fn, delay);
    activeIntervals.push(id);
    return id;
  };

  const disposeCurrentGame = () => {
    while (timers.length > 0) {
      clearTimeout(timers.pop());
    }
    while (activeIntervals.length > 0) {
      clearInterval(activeIntervals.pop());
    }
  };

  const statusState = { key: '', shownAt: 0 };
  const bridgeMessage = error => {
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
    };
    return messages[error?.error_code] || error?.message || t('app.operation_failed', 'Thao tác không thể hoàn tất.');
  };

  const clearStatus = () => {
    const banner = document.querySelector('#status-banner');
    if (banner) banner.hidden = true;
    statusState.key = '';
  };

  const showStatus = error => {
    const banner = document.querySelector('#status-banner');
    const message = document.querySelector('#status-banner-message');
    if (!banner || !message) return;
    const key = error?.error_code || String(error?.message || error || 'status');
    const now = Date.now();
    if (statusState.key === key && now - statusState.shownAt < 30000) {
      statusState.shownAt = now;
    } else {
      statusState.key = key;
      statusState.shownAt = now;
    }
    message.textContent = typeof error === 'string' ? error : bridgeMessage(error);
    banner.hidden = false;
  };

  const showBridgeFailure = error => showStatus(error);
  window.addEventListener('aihub:bridge-success', clearStatus);
  document.querySelector('#status-banner-close')?.addEventListener('click', clearStatus);

  const getWeakWords = () => {
    try {
      const data = localStorage.getItem('ai_learning_hub_weak_words');
      return data ? JSON.parse(data) : [];
    } catch (_) {}
    return [];
  };

  const addWeakWord = word => {
    try {
      if (!word) return;
      const list = getWeakWords();
      if (!list.includes(word)) {
        list.push(word);
        if (list.length > 100) list.shift();
        localStorage.setItem('ai_learning_hub_weak_words', JSON.stringify(list));
      }
    } catch (_) {}
  };



  const nav = r => {
    disposeCurrentGame();
    abortActiveRequests();
    state.route = r;
    location.hash = r === 'home' ? '' : r;
    render();
  };
  const shell = body => {
    state.busy = false;
    root.innerHTML = `<div class="timer-bar"><span class="timer-label">${esc(t('app.title', 'AI Learning Hub'))}</span><span id="busy-label"></span><button id="close-hub" aria-label="${esc(t('app.close_hub', 'Đóng Hub'))}">${esc(t('app.close_hub', 'Đóng Hub'))}</button></div>${body}<div id="loading" class="loading-overlay" hidden><div class="spinner"></div><span id="loading-text">${esc(t('app.processing', 'Đang xử lý…'))}</span><button id="loading-cancel-btn" class="btn" style="margin-top:16px; background:#ef4444; color:white; border:none; padding:8px 20px; border-radius:6px; font-weight:600; cursor:pointer;" type="button">${esc(t('app.cancel_gen', 'Hủy tạo bài'))}</button></div>`;
    document.querySelector('#loading').hidden = true;
  };

  function setBusy(on, text = t('app.generating', 'Đang tạo bài…')) {
    state.busy = on;
    const e = document.querySelector('#loading');
    if (e) {
      e.hidden = !on;
      const tEl = document.querySelector('#loading-text');
      if (tEl) tEl.textContent = text;
      const cBtn = document.querySelector('#loading-cancel-btn');
      if (cBtn) {
        cBtn.textContent = text.includes('tạo bài') || text.includes('Generating') ? t('app.cancel_gen', 'Hủy tạo bài') : t('app.cancel_action', 'Hủy thao tác');
      }
    }
    const cancelGen = document.querySelector('#cancel-gen');
    if (cancelGen) {
      cancelGen.style.display = on ? 'inline-block' : 'none';
    }
    document.querySelectorAll('button,input,select,textarea').forEach(x => {
      if (x.id !== 'close-hub' && x.id !== 'loading-cancel-btn' && x.id !== 'cancel-gen' && x.id !== 'back') {
        x.disabled = on;
      }
    });
  }

  function home() {
    shell('<main class="container"><div class="header" style="padding-top:50px"><h1>' + esc(t('app.title', 'AI Learning Hub')) + '</h1><p>' + esc(t('app.home_subtitle', 'Chọn một game để học từ bộ thẻ Anki')) + '</p><div class="api-check"><button class="btn btn-outline" id="test-keys">' + esc(t('app.test_api', 'Kiểm tra API')) + '</button><span id="api-result" aria-live="polite"></span></div></div><div class="game-grid">' + games.map(g => '<button class="game-card" data-game="' + g[0] + '"><div class="icon">' + g[1] + '</div><h3>' + esc(t(g[0] + '.title', g[2])) + '</h3><p>' + esc(getGameDesc(g[0])) + '</p></button>').join('') + '</div></main>');
    bindCommon();
    document.querySelectorAll('[data-game]').forEach(e => e.onclick = () => nav(e.dataset.game));
    document.querySelector('#test-keys').onclick = testKeys;
  }

  function getGameDesc(id) {
    const m = {
      fill_blank: t('desc.fill_blank', 'Điền từ vào chỗ trống trong câu'),
      cloze: t('desc.cloze', 'Điền từ vào đoạn văn có chỗ trống'),
      translation: t('desc.translation', 'Dịch câu từ tiếng Việt sang ngoại ngữ'),
      unscramble: t('desc.unscramble', 'Sắp xếp từ thành câu hoàn chỉnh'),
      matching: t('desc.matching', 'Nối từ với định nghĩa tương ứng'),
      story: t('desc.story', 'Đọc truyện và trả lời câu hỏi'),
      sentence_transform: t('desc.sentence_transform', 'Biến đổi câu theo yêu cầu ngữ pháp'),
      taboo: t('desc.taboo', 'Đoán từ qua mô tả (không dùng từ cấm)')
    };
    return m[id] || t('desc.default', 'Luyện tập tương tác');
  }

  function source() {
    return `<section class="config-panel source-panel"><h3>${esc(t('source.title', 'Nguồn từ vựng Anki'))}</h3><label>${esc(t('source.search', 'Tìm deck'))} <input id="deck-search" placeholder="${esc(t('source.search_placeholder', 'Gõ một phần tên deck…'))}"></label><select id="deck" class="deck-list" size="7"></select><div class="selector-grid"><label>${esc(t('source.note_type', 'Note type'))}<select id="model"><option>${esc(t('source.select_deck_first', 'Chọn deck'))}</option></select></label><label>${esc(t('source.term', 'Thuật ngữ'))}<select id="term"><option>${esc(t('source.select_notetype_first', 'Chọn note type'))}</option></select></label><label>${esc(t('source.definition', 'Định nghĩa'))}<select id="definition"><option>${esc(t('source.select_notetype_first', 'Chọn note type'))}</option></select></label></div><div class="config-row"><label>${esc(t('source.sample_count', 'Số từ mẫu'))} <input id="sample-limit" type="number" value="20" min="1" max="50"></label><button id="sample" class="btn btn-outline">${esc(t('source.get_samples', 'Lấy mẫu'))}</button><button id="reset-samples" class="btn btn-outline">${esc(t('source.reset_round', 'Làm mới vòng'))}</button></div><p id="source-status" class="source-status">${esc(t('source.status', 'Mẫu được chọn ngẫu nhiên, không lặp trong phiên Hub.'))}</p><details id="sample-preview"><summary>${esc(t('source.preview_empty', 'Chưa có mẫu để xem'))}</summary><ol id="sample-list"></ol></details></section>`;
  }

  function controls(id) {
    let max = id === 'matching' ? 20 : 5, min = id === 'matching' ? 5 : (id === 'story' ? 3 : 1), extra = '';
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
      return '<section class="config-panel"><div class="selector-grid">' + countSelect + '</div><div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-top:12px;"><button class="btn primary" id="generate">' + esc(t('controls.generate', 'Tạo bài')) + '</button></div></section>';
    }

    return '<section class="config-panel"><div class="selector-grid"><label>' + esc(t('app.language', 'Ngôn ngữ')) + '<select id="language"><option value="en">' + esc(t('app.language_en', 'English')) + '</option><option value="zh">' + esc(t('app.language_zh', '中文 (Chinese)')) + '</option></select></label><label>' + esc(t('app.level', 'Trình độ')) + '<select id="level"><option value="beginner">' + esc(t('controls.level_beginner', 'A1 Beginner')) + '</option><option value="elementary">' + esc(t('controls.level_elementary', 'A2 Elementary')) + '</option><option value="intermediate" selected>' + esc(t('controls.level_intermediate', 'B1 Intermediate')) + '</option><option value="upper_intermediate">' + esc(t('controls.level_upper_intermediate', 'B2 Upper-intermediate')) + '</option><option value="advanced">' + esc(t('controls.level_advanced', 'C1–C2 Advanced')) + '</option></select></label>' + countSelect + extra + '<label>' + esc(t('app.topic', 'Chủ đề')) + '<input id="topic" value="daily_life"></label></div><div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-top:12px;"><button class="btn primary" id="generate">' + esc(t('controls.generate', 'Tạo bài')) + '</button><button class="btn" id="cancel-gen" style="display:none; background:#ef4444; color:white; border:none; padding:10px 20px; font-weight:600;" type="button">' + esc(t('app.cancel_gen', 'Hủy tạo bài')) + '</button></div></section>';
  }

  function game() {
    const g = games.find(x => x[0] === state.route);
    const titleText = t(g[0] + '.title', g[2]);
    shell(`<main class="container game-page" style="padding-top:50px">
      <div class="game-header">
        <button id="back" class="back-btn">${esc(t('app.back_hub', '← Hub'))}</button>
        <h2 class="game-title">${g[1]} ${esc(titleText)}</h2>
        <button id="open-history-btn" class="history-btn">${esc(t('app.history', '📜 Lịch sử'))}</button>
      </div>
      ${source()}
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
    bindSource().then(() => {
      restorePrefs();
    });

    const gameId = g[0];
    resetGameState(gameId);

    document.querySelector('#back').onclick = () => { savePrefs(); nav('home'); };
    document.querySelector('#generate').onclick = () => { savePrefs(); generate(g[0]); };

    const histBtn = document.querySelector('#open-history-btn');
    if (histBtn) {
      if (g[0] === 'matching') {
        histBtn.style.display = 'inline-flex';
        histBtn.textContent = '📊 Thống kê';
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

  function openHistoryModal(gameId) {
    const modal = document.querySelector('#history-modal');
    if (!modal) return;
    renderHistoryList(gameId);
    modal.hidden = false;
  }

  function renderHistoryList(gameId) {
    const historyList = state.history[gameId] || [];
    const container = document.querySelector('#history-modal-body');
    const title = document.querySelector('#history-modal-title');
    if (title) title.textContent = t('app.history_title', '📜 Lịch sử làm bài');

    if (!historyList.length) {
      container.innerHTML = '<div class="empty-state"><p>' + esc(t('app.no_history', 'Chưa có lịch sử làm bài nào.')) + '</p></div>';
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
          <div class="history-card-sub" style="margin-bottom:8px;">
            Bài tập ${totalQ} câu
          </div>
          <button class="btn btn-outline view-detail-btn" data-idx="${idx}" style="font-size:12px; padding:4px 12px;">
            Xem chi tiết →
          </button>
        </div>
      `;
    }).join('');

    container.innerHTML = `<div class="history-list-grid">${itemsHtml}</div>`;

    container.querySelectorAll('.view-detail-btn').forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        renderHistoryDetail(gameId, +btn.dataset.idx);
      };
    });
  }

  function buildOptionDetailsHtml(q, chosen) {
    const optTrans = q.options_translations || [];
    const details = q.options_details || [];

    const items = q.options.map((opt, idx) => {
      let word = typeof opt === 'object' ? opt.word : opt;
      let isAns = typeof opt === 'object' ? opt.is_correct : (idx === q.correct_index);
      let reason = typeof opt === 'object' ? opt.reason : (details[idx]?.reason || (isAns ? (q.explanation_short || 'Từ phù hợp ngữ cảnh câu.') : 'Phương án gây nhiễu.'));
      let tr = typeof opt === 'object' ? '' : (details[idx]?.translation || optTrans[idx] || '');

      const isUserChoice = idx === chosen;
      const letter = String.fromCharCode(65 + idx);

      let badgeBg = isAns ? '#d1fae5' : (isUserChoice ? '#fee2e2' : 'var(--bg)');
      let badgeColor = isAns ? '#047857' : (isUserChoice ? '#b91c1c' : 'var(--text-secondary)');
      let badgeLabel = isAns ? '✓ Đáp án đúng' : (isUserChoice ? '✕ Bạn chọn' : 'Từ gây nhiễu');
      let borderColor = isAns ? 'var(--success)' : (isUserChoice ? 'var(--error)' : 'var(--border)');

      return `
        <div style="padding:10px 12px; border-left:4px solid ${borderColor}; background:var(--bg); border-radius:4px; margin-bottom:8px; text-align:left;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:4px;">
            <span style="font-size:14px;"><b>${letter}. ${esc(word)}</b> ${tr ? `<span style="color:var(--text-secondary); font-size:13px;">— ${esc(tr)}</span>` : ''}</span>
            <span style="font-size:11px; padding:2px 8px; border-radius:10px; font-weight:600; background:${badgeBg}; color:${badgeColor}; border:1px solid ${borderColor};">${badgeLabel}</span>
          </div>
          <div style="font-size:13px; color:var(--text); line-height:1.4;">
            <b>Lý do:</b> ${esc(reason)}
          </div>
        </div>
      `;
    }).join('');

    return `
      <div style="margin-top:14px; text-align:left;">
        <b style="font-size:14px;">📊 Phân tích chi tiết các lựa chọn:</b>
        <div style="margin-top:8px;">
          ${items}
        </div>
      </div>
    `;
  }

  function renderHistoryDetail(gameId, idx) {
    const item = state.history[gameId]?.[idx];
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

      detailContent = questions.map((q, qIdx) => {
        const chosen = userAnswers[qIdx];
        
        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;
        const isCorrect = chosen === correctIdx;

        const sentenceText = q.sentence || q.sentence_with_blank || '';
        const trans = q.full_translation || q.sentence_translation || q.full_sentence_translation || 'Không có bản dịch';
        const explanation = q.explanation || q.explanation_short || '';

        return `
          <div class="question-card" style="margin-bottom:16px;">
            <div class="q-number">Câu ${qIdx + 1}/${questions.length}</div>
            <div class="q-text" style="font-size:16px; font-weight:600;">${esc(sentenceText)}</div>

            <div class="feedback ${chosen !== undefined ? (isCorrect ? 'good' : 'bad') : ''}" style="margin-top:12px;">
              ${chosen !== undefined ? `
                <div style="font-weight:700; font-size:15px; margin-bottom:8px; color:${isCorrect ? 'var(--success)' : 'var(--error)'};">
                  ${isCorrect ? 'Chính xác! ✓' : 'Chưa đúng ✕'}
                </div>
              ` : '<div style="color:var(--text-secondary); margin-bottom:8px;">(Chưa làm bài)</div>'}

              <div style="margin-bottom:8px;">
                <b>🌐 Dịch câu hoàn chỉnh:</b> ${esc(trans)}
              </div>

              <div style="margin-bottom:8px;">
                <b>💡 Lý do chọn:</b> ${esc(explanation)}
              </div>

              ${q.grammar_note ? `<div style="margin-bottom:8px;"><b>📌 Ghi chú ngữ pháp:</b> ${esc(q.grammar_note)}</div>` : ''}

              ${buildOptionDetailsHtml(q, chosen)}
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
        const correctOpt = b.options[b.correct_index] || b.answer || '';
        const chosenOpt = chosen !== undefined ? b.options[chosen] : 'Chưa chọn';
        const meaning = b.meaning_vi || b.meaning_in_vietnamese || '';

        return `
          <div style="padding:10px; border:1px solid var(--border); border-radius:var(--radius-sm); margin-bottom:10px; background:var(--bg);">
            <b>Blank [${bIdx + 1}]</b>: <b style="color:var(--success);">${esc(correctOpt)}</b> ${meaning ? `(${esc(meaning)})` : ''}
            <div>Kết quả: <span style="font-weight:600; color:${isCorrect ? 'var(--success)' : 'var(--error)'};">${isCorrect ? '✓ Đúng' : '✕ Sai'}</span> (Bạn chọn: <i>${esc(chosenOpt)}</i>)</div>
            <div style="font-size:13px; color:var(--text-secondary); margin-top:4px;">💡 ${esc(b.explanation || b.explanation_short || '')}</div>
          </div>
        `;
      }).join('');

      detailContent = `
        <div class="question-card" style="margin-bottom:16px;">
          <p><b>Đoạn văn hoàn chỉnh:</b></p>
          <div class="cloze-paragraph" style="background:var(--bg); padding:12px; border-radius:var(--radius-sm);">
            ${esc(data.full_solution_text || data.paragraph_full || data.paragraph_with_blanks || data.paragraph || '')}
          </div>
          ${(data.story_translation || data.sentence_meaning || data.paragraph_translation) ? `<p style="margin-top:8px;"><b>🌐 Dịch đoạn văn:</b> ${esc(data.story_translation || data.sentence_meaning || data.paragraph_translation)}</p>` : ''}
          <hr style="margin:16px 0;">
          <p><b>Chi tiết từng chỗ trống:</b></p>
          ${blanksHtml}
        </div>
      `;
    } else if (gameId === 'matching' && (item.data?.pairs || item.data?.items)) {
      let pairsList = [];
      if (item.data.items) {
        const termItems = item.data.items.filter(it => it.type === 'term');
        termItems.forEach(tItem => {
          const dItem = item.data.items.find(it => it.type === 'definition' && it.pair_id === tItem.pair_id);
          pairsList.push({ term: tItem.content, definition: dItem ? dItem.content : '' });
        });
      } else {
        pairsList = item.data.pairs;
      }
      const total = item.total || pairsList.length;
      const score = item.score !== null && item.score !== undefined ? item.score : total;
      const wrongCount = item.wrongCount || 0;
      const accuracy = item.accuracy !== undefined ? item.accuracy : 100;
      const timeSec = item.timeSec || 0;
      const mins = Math.floor(timeSec / 60);
      const secs = timeSec % 60;
      const timeFormatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

      const pairsHtml = pairsList.map((p, pIdx) => `
        <li style="margin-bottom:8px; padding:8px 12px; background:var(--bg); border:1px solid var(--border); border-radius:var(--radius-sm); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <b>${pIdx + 1}. ${esc(p.term || p.word)}</b> ➔ <span style="color:var(--primary); font-weight:500;">${esc(p.definition || p.meaning)}</span>
        </li>
      `).join('');

      detailContent = `
        <div class="question-card">
          <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap:10px; margin-bottom:16px;">
            <div style="background:var(--bg); padding:10px; border-radius:var(--radius-sm); text-align:center; border:1px solid var(--border);">
              <div style="font-size:11px; color:var(--text-secondary);">Đã nối</div>
              <div style="font-weight:700; color:var(--primary); margin-top:2px;">${score}/${total} cặp</div>
            </div>
            <div style="background:var(--bg); padding:10px; border-radius:var(--radius-sm); text-align:center; border:1px solid var(--border);">
              <div style="font-size:11px; color:var(--text-secondary);">Lần chọn sai</div>
              <div style="font-weight:700; color:${wrongCount > 0 ? 'var(--error)' : 'var(--success)'}; margin-top:2px;">${wrongCount} lần</div>
            </div>
            <div style="background:var(--bg); padding:10px; border-radius:var(--radius-sm); text-align:center; border:1px solid var(--border);">
              <div style="font-size:11px; color:var(--text-secondary);">Tỉ lệ chính xác</div>
              <div style="font-weight:700; color:${accuracy >= 80 ? 'var(--success)' : 'var(--primary)'}; margin-top:2px;">${accuracy}%</div>
            </div>
            <div style="background:var(--bg); padding:10px; border-radius:var(--radius-sm); text-align:center; border:1px solid var(--border);">
              <div style="font-size:11px; color:var(--text-secondary);">Thời gian</div>
              <div style="font-weight:700; color:var(--text); margin-top:2px;">${timeFormatted}</div>
            </div>
          </div>
          <p style="font-weight:600; margin-bottom:10px;">Danh sách các cặp từ vựng:</p>
          <ul style="list-style:none; padding:0; margin:0;">${pairsHtml}</ul>
        </div>
      `;
    } else if (gameId === 'unscramble' && (item.data?.questions || item.data?.sentences)) {
      const qs = item.data.questions || item.data.sentences || [];
      detailContent = qs.map((q, qIdx) => `
        <div class="question-card" style="margin-bottom:12px;">
          <p><b>Câu ${qIdx + 1}:</b> ${esc(q.hint || '')}</p>
          <p style="color:var(--success); font-weight:600;">➔ ${esc(q.correct_sentence)}</p>
          ${(q.meaning_vi || q.translation || q.sentence_meaning) ? `<p style="font-size:13px; color:var(--text-secondary);">🌐 ${esc(q.meaning_vi || q.translation || q.sentence_meaning)}</p>` : ''}
        </div>
      `).join('');
    } else if (gameId === 'story' && (item.data?.story || item.data?.questions)) {
      const isNewStory = !!item.data.questions;
      const qs = isNewStory ? item.data.questions : (item.data.comprehension_questions || []);
      const userAnswers = item.answers || {};

      const qsHtml = qs.map((q, qIdx) => {
        const chosen = userAnswers[qIdx];
        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;

        const isCorrect = chosen === correctIdx;
        const correctOptText = typeof q.options[correctIdx] === 'object' ? q.options[correctIdx].text : q.options[correctIdx];
        const chosenOptText = chosen !== undefined ? (typeof q.options[chosen] === 'object' ? q.options[chosen].text : q.options[chosen]) : 'Chưa chọn';

        return `
          <div style="margin-bottom:10px; padding:10px; background:var(--bg); border:1px solid var(--border); border-radius:var(--radius-sm);">
            <p style="margin-bottom:4px;"><b>${qIdx + 1}. ${esc(q.question)}</b></p>
            <p style="margin:0; font-size:13px;">Đáp án đúng: <b style="color:var(--success);">${esc(correctOptText)}</b></p>
            ${chosen !== undefined ? `<p style="margin:2px 0 0; font-size:13px; color:${isCorrect ? 'var(--success)' : 'var(--error)'};">Bạn đã chọn: ${esc(chosenOptText)} ${isCorrect ? '✓' : '✕'}</p>` : ''}
          </div>
        `;
      }).join('');

      const storyContent = typeof item.data.story === 'object' ? item.data.story.content : item.data.story;

      detailContent = `
        <div class="question-card">
          <div class="story-text" style="font-size:14px; max-height:200px; overflow-y:auto; background:rgba(0,0,0,0.02); padding:10px; border-radius:4px;">${esc(storyContent).replace(/\n\n/g, '<br><br>')}</div>
          <p><b>Câu hỏi đọc hiểu:</b></p>
          ${qsHtml}
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

    container.innerHTML = `
      <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:12px;">
        <button class="btn btn-outline" id="back-to-history-list" style="padding:6px 14px; font-size:13px;">
          ← Quay lại danh sách lịch sử
        </button>
        <span style="font-size:12px; color:var(--text-secondary);">${timeStr}</span>
      </div>
      ${detailContent}
    `;

    document.querySelector('#back-to-history-list').onclick = () => renderHistoryList(gameId);
  }

  function bindCommon() {
    const closeBtn = document.querySelector('#close-hub');
    if (closeBtn) {
      closeBtn.onclick = () => {
        abortActiveRequests();
        clearPrefs();
        Bridge.send('close_hub');
      };
    }
    const cancelBtn = document.querySelector('#loading-cancel-btn');
    if (cancelBtn) {
      cancelBtn.onclick = () => {
        abortActiveRequests();
        setBusy(false);
        showStatus('Đã hủy thao tác.');
      };
    }
    const cancelGen = document.querySelector('#cancel-gen');
    if (cancelGen) {
      cancelGen.onclick = () => {
        abortActiveRequests();
        setBusy(false);
        showStatus('Đã hủy tạo bài.');
      };
    }
  }

  function options(sel, items, label = x => x.name) {
    const e = document.querySelector(sel);
    if (!e) return;
    e.innerHTML = '<option value="">-- Chọn --</option>' + items.map(x => '<option value="' + esc(x.id ?? x) + '">' + esc(label(x)) + '</option>').join('');
  }

  function drawDecks(q = '') {
    const e = document.querySelector('#deck');
    if (!e) return;
    const items = state.decks.filter(d => d.name.toLowerCase().includes(q.toLowerCase()));
    e.innerHTML = items.map(d => '<option value="' + d.id + '">' + '\u3000'.repeat(d.level) + esc(d.name) + '</option>').join('') || '<option value="">Không tìm thấy deck</option>';
  }

  async function bindSource() {
    const signal = getSignal();
    try {
      state.decks = (await Bridge.sendAsync('list_decks', {}, { signal })).decks || [];
      drawDecks();

      const p = state.userPrefs;
      const deckElem = document.querySelector('#deck');
      if (p.deck && deckElem) {
        deckElem.value = p.deck;
        await loadModels();
      }
    } catch (e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return;
      showBridgeFailure(e);
    }

    const deckSearch = document.querySelector('#deck-search');
    if (deckSearch) deckSearch.oninput = e => drawDecks(e.target.value);

    const deckEl = document.querySelector('#deck');
    if (deckEl) {
      deckEl.onchange = async () => {
        await loadModels();
        savePrefs();
      };
    }

    const modelEl = document.querySelector('#model');
    if (modelEl) {
      modelEl.onchange = async () => {
        await loadFields();
        savePrefs();
      };
    }

    const termEl = document.querySelector('#term');
    if (termEl) termEl.onchange = () => savePrefs();

    const defEl = document.querySelector('#definition');
    if (defEl) defEl.onchange = () => savePrefs();

    const slEl = document.querySelector('#sample-limit');
    if (slEl) slEl.oninput = () => savePrefs();

    ['#language', '#level', '#count', '#num_blanks', '#focus'].forEach(sel => {
      const el = document.querySelector(sel);
      if (el) el.onchange = () => savePrefs();
    });

    const topicEl = document.querySelector('#topic');
    if (topicEl) topicEl.oninput = () => savePrefs();

    const sampleBtn = document.querySelector('#sample');
    if (sampleBtn) sampleBtn.onclick = sample;

    const resetBtn = document.querySelector('#reset-samples');
    if (resetBtn) {
      resetBtn.onclick = () => {
        state.seen.clear();
        state.pairs = [];
        savePrefs();
        preview();
      };
    }
  }

  async function loadModels() {
    state.seen.clear();
    state.pairs = [];
    const signal = getSignal();
    try {
      const deckVal = document.querySelector('#deck')?.value;
      if (!deckVal) return;
      options('#model', (await Bridge.sendAsync('get_source_models', { deck_id: +deckVal }, { signal })).models || []);
      options('#term', []);
      options('#definition', []);

      const p = state.userPrefs;
      const modelElem = document.querySelector('#model');
      if (p.model && modelElem && Array.from(modelElem.options).some(o => o.value == p.model)) {
        modelElem.value = p.model;
        await loadFields();
      }
    } catch (e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return;
      showBridgeFailure(e);
    }
  }

  async function loadFields() {
    state.seen.clear();
    state.pairs = [];
    const signal = getSignal();
    try {
      const modelVal = document.querySelector('#model')?.value;
      if (!modelVal) return;
      const f = (await Bridge.sendAsync('get_source_fields', { model_id: +modelVal }, { signal })).fields || [];
      options('#term', f, x => x);
      options('#definition', f, x => x);

      const p = state.userPrefs;
      const termElem = document.querySelector('#term');
      const defElem = document.querySelector('#definition');
      if (p.term && termElem && Array.from(termElem.options).some(o => o.value === p.term)) {
        termElem.value = p.term;
      }
      if (p.definition && defElem && Array.from(defElem.options).some(o => o.value === p.definition)) {
        defElem.value = p.definition;
      }
    } catch (e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return;
      showBridgeFailure(e);
    }
  }

  function request() {
    const deck_id = +document.querySelector('#deck').value;
    const model_id = +document.querySelector('#model').value;
    const term_field = document.querySelector('#term').value;
    const definition_field = document.querySelector('#definition').value;
    if (!deck_id || !model_id || !term_field || !definition_field) throw Error('Hãy chọn deck, note type và hai trường.');
    return { deck_id, model_id, term_field, definition_field, limit: +document.querySelector('#sample-limit').value || 20, excluded_pair_keys: [...state.seen], weak_words: getWeakWords() };
  }

  function preview() {
    const d = document.querySelector('#sample-preview');
    if (!d) return;
    d.querySelector('summary').textContent = state.pairs.length ? 'Xem ' + state.pairs.length + ' từ mẫu' : 'Chưa có mẫu để xem';
    d.querySelector('#sample-list').innerHTML = state.pairs.map(x => '<li><b>' + esc(x.term) + '</b> — ' + esc(x.definition) + '</li>').join('');
  }

  async function sample() {
    const signal = getSignal();
    try {
      const data = await Bridge.sendAsync('sample_vocab_pairs', request(), { signal });
      if (data.exhausted) throw Error('Đã dùng hết mẫu trong vòng này. Bấm Làm mới vòng.');
      state.pairs = data.pairs || [];
      state.pairs.forEach(x => state.seen.add(x.key));
      const srcStat = document.querySelector('#source-status');
      if (srcStat) srcStat.textContent = `Đã lấy ${data.total} cặp ngẫu nhiên.`;
      preview();
      savePrefs();
      return !!state.pairs.length;
    } catch (e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return false;
      showBridgeFailure(e);
      return false;
    }
  }


  async function generate(id, optsOverride){
    const signal = getSignal();
    try {
      disposeCurrentGame();
      if (!optsOverride) resetGameState(id);
      setBusy(true);
      if(!state.pairs.length && !optsOverride && !await sample()) {
        if (signal.aborted) return;
      }
      if (signal.aborted) return;

      if (id === 'matching' && state.pairs.length < 5) {
        showStatus('error', t('app.matching_vocab_limit', 'Không đủ từ vựng để nối. Cần ít nhất 5 từ vựng.'));
        setBusy(false);
        return;
      }

      let opts;
      if (optsOverride) {
        opts = optsOverride;
      } else {
        const lang = document.querySelector('#language');
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
      state.exercise = await Bridge.sendAsync('generate', opts, { signal });
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
      if (!signal.aborted) setBusy(false);
    }
  }

  function addHistory(id, data) {
    if (id === 'matching') return null;
    if (!state.history) state.history = {};
    if (!state.history[id]) state.history[id] = [];

    let totalQ = 0;
    if (id === 'fill_blank') totalQ = data.questions ? data.questions.length : 0;
    else if (id === 'cloze') totalQ = data.blanks ? data.blanks.length : 0;
    else if (id === 'story') totalQ = data.comprehension_questions ? data.comprehension_questions.length : 0;
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
    if (state.history[id].length > 50) state.history[id].length = 50;
    state.currentHistoryItem = item;
    saveHistory();
    return item;
  }
  const buttons=(opts,name,chosen)=>opts.map((o,i)=>`<button class="option-btn ${chosen===i?'selected':''}" data-choice="${i}">${String.fromCharCode(65+i)}. ${esc(o)}</button>`).join('');

  /* ---- PLAY: route to renderers ---- */
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
    if (id === 'unscramble' && x.sentences && !x.questions) {
      x.questions = x.sentences;
      delete x.sentences;
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

  function openMatchingStatsModal() {
    if (!state.matchingStats) loadMatchingStats();
    const stats = state.matchingStats;
    const body = document.querySelector('#history-modal-body');
    const title = document.querySelector('#history-modal-title');
    const modal = document.querySelector('#history-modal');
    if (!body || !title || !modal) return;

    title.textContent = '📊 Thống kê Nối từ (Word Matching)';

    const bestTimeStr = stats.aggregates.best_time_sec !== 999999 ? 
      `${Math.floor(stats.aggregates.best_time_sec / 60)}m ${stats.aggregates.best_time_sec % 60}s` : 'N/A';

    let html = `
      <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 20px;">
        <div class="stat-card" style="padding: 12px; background: rgba(0,0,0,0.02); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color: var(--primary);">${stats.aggregates.total_games}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Số bài đã chơi</div>
        </div>
        <div class="stat-card" style="padding: 12px; background: rgba(0,0,0,0.02); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color: var(--success);">${stats.aggregates.avg_accuracy}%</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Độ chính xác TB</div>
        </div>
        <div class="stat-card" style="padding: 12px; background: rgba(0,0,0,0.02); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color: var(--primary);">${bestTimeStr}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Thời gian nhanh nhất</div>
        </div>
        <div class="stat-card" style="padding: 12px; background: rgba(0,0,0,0.02); border: 1px solid var(--border); border-radius: 6px; text-align: center;">
          <div style="font-size: 20px; font-weight: 700; color: #ef4444;">${stats.aggregates.total_wrong}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">Tổng số lần ghép sai</div>
        </div>
      </div>
    `;

    html += `<h4 style="margin: 0 0 10px; font-size:14px; font-weight:700;">📋 30 lượt chơi gần đây</h4>`;
    if (!stats.records.length) {
      html += `<p style="text-align: center; color: var(--text-secondary); font-style: italic; padding: 20px 0; font-size:13px;">Chưa có dữ liệu thống kê nào được ghi nhận.</p>`;
    } else {
      html += `<div style="max-height: 240px; overflow-y: auto; border: 1px solid var(--border); border-radius: 6px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
          <thead>
            <tr style="background: rgba(0,0,0,0.03); border-bottom: 1px solid var(--border);">
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
                  <td style="padding: 8px 12px; color: ${r.wrong > 0 ? '#ef4444' : 'inherit'};">${r.wrong}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>`;
    }

    html += `
      <div style="text-align: right; margin-top: 16px;">
        <button class="btn btn-outline" id="clear-matching-stats-btn" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.3); padding: 6px 12px; font-size: 12px; font-weight: 600; cursor:pointer;">🗑️ Xóa thống kê</button>
      </div>
    `;

    body.innerHTML = html;
    modal.hidden = false;

    const clearBtn = body.querySelector('#clear-matching-stats-btn');
    if (clearBtn) {
      clearBtn.onclick = () => {
        if (confirm('Bạn có chắc chắn muốn xóa toàn bộ dữ liệu thống kê của trò chơi Nối từ không?')) {
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

  function play(id) {
    const d = document.querySelector('#play');
    let x = state.exercise;
    if (!x) { d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu bài tập.</p></div>'; return; }
    x = normalizeExercise(id, x);
    if (!state.answers) state.answers = {};
    if (id === 'fill_blank') renderFillBlank(x);
    else if (id === 'cloze') renderCloze(x);
    else if (id === 'matching') renderMatching(x);
    else if (id === 'unscramble') renderUnscrambleAll(x);
    else if (id === 'story') renderStory(x);
    else if (id === 'translation') renderTranslation(x);
    else if (id === 'sentence_transform') renderSentenceTransform(x);
    else if (id === 'taboo') renderTaboo(x);
  }

  /* ---- FILL-BLANK: all questions vertical ---- */
  /* ---- FILL-BLANK: all questions vertical ---- */
  function renderFillBlank(x) {
    const d = document.querySelector('#play');
    if (!x?.questions?.length) { d.innerHTML = '<div class="empty-state"><p>Không có câu hỏi.</p></div>'; return; }
    const isGraded = !!state.isGraded;
    const gameId = state.route;

    let score = 0;
    if (isGraded) {
      x.questions.forEach((q, i) => {
        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;
        if (state.answers[i] === correctIdx) score++;
      });
    }

    const cardsHtml = x.questions.map((q, i) => {
      const chosen = state.answers[i];
      const optsHtml = q.options.map((o, idx) => {
        let cls = 'option-btn';
        let disabledAttr = '';
        let word = typeof o === 'object' ? o.word : o;
        let isCorrectOpt = typeof o === 'object' ? o.is_correct : (idx === q.correct_index);

        if (isGraded) {
          disabledAttr = 'disabled';
          if (isCorrectOpt) {
            cls += ' correct';
          } else if (idx === chosen) {
            cls += ' wrong';
          }
        } else {
          if (idx === chosen) {
            cls += ' selected';
          }
        }

        return `
          <button class="${cls}" data-q="${i}" data-choice="${idx}" ${disabledAttr}>
            ${String.fromCharCode(65 + idx)}. ${esc(word)}
          </button>
        `;
      }).join('');

      let feedbackHtml = '';
      if (isGraded) {
        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;
        const isCorrect = chosen === correctIdx;

        feedbackHtml = `
          <div class="feedback ${isCorrect ? 'good' : 'bad'}" style="margin-top:16px; padding:16px; border-radius:8px;">
            <div style="font-weight:700; font-size:16px; margin-bottom:12px; color:${isCorrect ? 'var(--success)' : 'var(--error)'};">
              ${isCorrect ? 'Chính xác! ✓' : 'Chưa đúng ✕'}
            </div>
            
            <div style="margin-bottom:10px;">
              <b>🌐 Dịch câu hoàn chỉnh:</b>
              <div style="margin-top:4px; padding:10px 12px; background:rgba(0,0,0,0.03); border-radius:6px; font-size:13.5px; line-height:1.5;">
                ${esc(q.full_translation || q.sentence_translation || q.full_sentence_translation || 'Không có bản dịch')}
              </div>
            </div>

            <div style="margin-bottom:10px;">
              <b>💡 Lý do chọn:</b>
              <div style="margin-top:4px; padding:10px 12px; background:rgba(0,0,0,0.03); border-radius:6px; font-size:13.5px; line-height:1.5;">
                ${esc(q.explanation || q.explanation_short || 'Không có giải thích')}
              </div>
            </div>

            ${q.grammar_note ? `
            <div style="margin-bottom:10px;">
              <b>📌 Ghi chú ngữ pháp:</b>
              <div style="margin-top:4px; padding:10px 12px; background:rgba(0,0,0,0.03); border-radius:6px; font-size:13.5px; line-height:1.5;">
                ${esc(q.grammar_note)}
              </div>
            </div>
            ` : ''}

            ${buildOptionDetailsHtml(q, chosen)}
          </div>
        `;
      }

      return `
        <div class="question-card" id="qcard-${i}">
          <div class="q-number">Câu ${i + 1}/${x.questions.length}</div>
          <div class="q-text" style="font-size:16px; font-weight:600; margin-bottom:12px;">${esc(q.sentence || q.sentence_with_blank)}</div>
          <div class="options-grid" id="choices-${i}">
            ${optsHtml}
          </div>
          ${!isGraded ? `
            <div style="margin-top: 10px; text-align: right;">
              <button class="btn btn-outline hint-btn" data-hint-q="${i}" style="padding: 4px 10px; font-size: 12.5px; border-color: #eab308; color: #ca8a04;">
                💡 Gợi ý
              </button>
              <div class="hint-text-box" id="hint-text-${i}" style="font-size: 13px; color: var(--text-secondary); margin-top: 6px; text-align: left; display: none; background: rgba(234, 179, 8, 0.05); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #eab308;"></div>
            </div>
          ` : ''}
          <div id="feedback-${i}">${feedbackHtml}</div>
        </div>
      `;
    }).join('');

    const submitHtml = isGraded ? `
      <div id="fill-overall-feedback">
        <div class="feedback ${score === x.questions.length ? 'good' : 'bad'}" style="text-align:center; margin-top:20px;">
          <h3 style="margin-bottom:8px;">Kết quả: ${score}/${x.questions.length} câu đúng</h3>
        </div>
      </div>
    ` : `
      <div style="text-align:center; margin: 24px 0 12px 0;">
        <button class="btn primary" id="grade-fill-blank" style="padding: 12px 36px; font-size: 16px;">
          Chấm điểm
        </button>
      </div>
      <div id="fill-overall-feedback"></div>
    `;

    d.innerHTML = cardsHtml + submitHtml;

    if (!isGraded) {
      d.querySelectorAll('[data-choice]').forEach(b => {
        b.onclick = () => {
          if (state.isGraded) return;
          const qIdx = +b.dataset.q;
          const cIdx = +b.dataset.choice;
          state.answers[qIdx] = cIdx;
          const choices = document.querySelectorAll(`#choices-${qIdx} [data-choice]`);
          choices.forEach(btn => btn.classList.remove('selected'));
          b.classList.add('selected');
        };
      });

      d.querySelectorAll('[data-hint-q]').forEach(btn => {
        let hintLevel = 0;
        btn.onclick = () => {
          const qIdx = +btn.dataset.hintQ;
          const q = x.questions[qIdx];
          const textEl = document.querySelector(`#hint-text-${qIdx}`);
          if (!textEl) return;
          textEl.style.display = 'block';

          let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
          if (correctIdx === -1) correctIdx = q.correct_index;
          const correctOpt = q.options[correctIdx];
          const word = typeof correctOpt === 'object' ? correctOpt.word : correctOpt;
          const translation = q.user_definition || q.meaning_vi || (typeof correctOpt === 'object' ? correctOpt.translation : '');

          hintLevel++;
          if (hintLevel === 1) {
            textEl.innerHTML = `⭐ <b>Gợi ý 1:</b> Chữ cái đầu là: <code style="font-size:14px; font-weight:700;">${word.charAt(0)}</code>`;
          } else if (hintLevel === 2) {
            textEl.innerHTML = `⭐ <b>Gợi ý 1:</b> Chữ cái đầu là: <code>${word.charAt(0)}</code><br>⭐ <b>Gợi ý 2:</b> Nghĩa: <i>${translation || 'Không có'}</i>`;
          } else if (hintLevel === 3) {
            textEl.innerHTML = `⭐ <b>Đáp án là:</b> <code>${word}</code> (Đã tự động điền & tính sai câu này)`;
            state.answers[qIdx] = correctIdx;
            if (!state.hintedQuestions) state.hintedQuestions = new Set();
            state.hintedQuestions.add(qIdx);

            const choices = document.querySelectorAll(`#choices-${qIdx} [data-choice]`);
            choices.forEach(btn => btn.classList.remove('selected'));
            const correctBtn = document.querySelector(`#choices-${qIdx} [data-choice="${correctIdx}"]`);
            if (correctBtn) correctBtn.classList.add('selected');

            btn.disabled = true;
            btn.style.opacity = '0.5';
          }
        };
      });

      const gradeBtn = document.querySelector('#grade-fill-blank');
      if (gradeBtn) {
        gradeBtn.onclick = () => {
          state.isGraded = true;
          let score = 0;
          x.questions.forEach((q, i) => {
            let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
            if (correctIdx === -1) correctIdx = q.correct_index;
            const wasHinted = state.hintedQuestions && state.hintedQuestions.has(i);
            const isCorrect = state.answers[i] === correctIdx && !wasHinted;
            if (isCorrect) {
              score++;
            } else {
              const correctOpt = q.options[correctIdx];
              const termWord = typeof correctOpt === 'object' ? correctOpt.word : correctOpt;
              addWeakWord(termWord);
            }
          });

          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { ...state.answers };
            state.currentHistoryItem.score = score;
          }
          saveHistory();

          renderFillBlank(x);
        };
      }
    }
  }

  /* ---- CLOZE: paragraph with selects + top word bank ---- */
  function renderCloze(x) {
    const d = document.querySelector('#play');
    if (!x?.blanks?.length) { d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu điền từ.</p></div>'; return; }
    const isGraded = !!state.isGraded;
    const gameId = state.route;

    const isNewSchema = !!x.paragraph;
    const targetWords = x.blanks.map(b => isNewSchema ? b.answer : (b.correct_word || (b.options ? b.options[b.correct_index] : ''))).filter(Boolean);
    const seen = new Set();
    const sortedWords = targetWords
      .filter(w => {
        const k = String(w).toLowerCase();
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
      })
      .sort((a, b) => a.localeCompare(b));

    x.blanks.forEach(b => {
      b.options = sortedWords;
      const target = (isNewSchema ? b.answer : b.correct_word) || '';
      const foundIdx = sortedWords.findIndex(w => w.toLowerCase() === target.toLowerCase());
      if (foundIdx !== -1) {
        b.correct_index = foundIdx;
      }
    });

    const wordBankHtml = `
      <div class="word-bank-box">
        <div class="word-bank-title">Danh sách từ để chọn (${sortedWords.length} từ)</div>
        <div class="word-bank-chips">
          ${sortedWords.map(w => `<span class="word-chip-static">${esc(w)}</span>`).join('')}
        </div>
      </div>
    `;

    // Process paragraph with inline selects
    let rawText = isNewSchema ? x.paragraph : (x.paragraph_with_blanks || '');
    let blankIdx = 0;
    const placeholderRegex = /(\[BLANK_\d+\]|\[\d+\]|\(\d+\)|\[blank_\d+\]|_{2,})/gi;

    let processedParagraph = rawText.replace(placeholderRegex, (match) => {
      if (blankIdx >= x.blanks.length) return match;
      const i = blankIdx++;
      const b = x.blanks[i];
      const chosen = state.answers[i];

      let selectClass = 'cloze-inline-select';
      let disabledAttr = isGraded ? 'disabled' : '';

      if (isGraded) {
        if (chosen === b.correct_index) {
          selectClass += ' correct';
        } else if (chosen !== undefined && chosen !== '') {
          selectClass += ' wrong';
        }
      }

      const optionsHtml = b.options.map((opt, oIdx) => `
        <option value="${oIdx}" ${chosen === oIdx ? 'selected' : ''}>${esc(opt)}</option>
      `).join('');

      return `<select class="${selectClass}" data-blank="${i}" ${disabledAttr}>
        <option value="">-- [${i + 1}] --</option>
        ${optionsHtml}
      </select>`;
    });

    while (blankIdx < x.blanks.length) {
      const i = blankIdx++;
      const b = x.blanks[i];
      const chosen = state.answers[i];
      let selectClass = 'cloze-inline-select';
      let disabledAttr = isGraded ? 'disabled' : '';
      if (isGraded) {
        if (chosen === b.correct_index) selectClass += ' correct';
        else if (chosen !== undefined && chosen !== '') selectClass += ' wrong';
      }
      const optionsHtml = b.options.map((opt, oIdx) => `
        <option value="${oIdx}" ${chosen === oIdx ? 'selected' : ''}>${esc(opt)}</option>
      `).join('');

      processedParagraph += ` <select class="${selectClass}" data-blank="${i}" ${disabledAttr}>
        <option value="">-- [${i + 1}] --</option>
        ${optionsHtml}
      </select>`;
    }

    let score = 0;
    if (isGraded) {
      x.blanks.forEach((b, i) => {
        if (state.answers[i] === b.correct_index) score++;
      });
    }

    let feedbackHtml = '';
    if (isGraded) {
      const explanations = x.blanks.map((b, i) => {
        const correctOpt = b.options[b.correct_index];
        const chosenOpt = state.answers[i] !== undefined ? b.options[state.answers[i]] : 'Chưa chọn';
        const isOk = state.answers[i] === b.correct_index;
        const vnMeaning = (b.meaning_vi || b.meaning_in_vietnamese) ? ` (${b.meaning_vi || b.meaning_in_vietnamese})` : '';

        return `
          <div style="margin-bottom: 10px; font-size: 14px;">
            <b>[${i + 1}]</b> <span style="color: ${isOk ? 'var(--success)' : 'var(--error)'}; font-weight:600;">${isOk ? '✓ Đúng' : '✕ Sai'}</span>
            — Đáp án: <b style="color: var(--success);">${esc(correctOpt)}</b>${esc(vnMeaning)}
            ${!isOk ? `<span style="color: var(--text-secondary);">(Bạn chọn: ${esc(chosenOpt)})</span>` : ''}
            ${b.hint ? `<div style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">💡 Gợi ý: ${esc(b.hint)}</div>` : ''}
            <div style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">
              💡 Giải thích: ${esc(b.explanation || b.explanation_short || '')}
            </div>
          </div>
        `;
      }).join('');

      const transHtml = (x.story_translation || x.paragraph_translation || x.sentence_meaning)
        ? `<div style="margin-top:12px; padding-top:10px; border-top:1px dashed var(--border); font-size:14px;">
             <b>🌐 Dịch đoạn văn:</b> ${esc(x.story_translation || x.paragraph_translation || x.sentence_meaning)}
             ${x.context_summary ? `<br><b>📝 Tóm tắt ngữ cảnh:</b> ${esc(x.context_summary)}` : ''}
             ${x.full_solution_text ? `<br><b>📖 Đoạn văn hoàn chỉnh:</b> ${esc(x.full_solution_text)}` : ''}
           </div>`
        : '';

      feedbackHtml = `
        <div class="feedback ${score === x.blanks.length ? 'good' : 'bad'}" style="margin-top:20px;">
          <h3 style="margin-bottom:12px; text-align:center;">Kết quả: ${score}/${x.blanks.length} câu đúng</h3>
          ${explanations}
          ${transHtml}
        </div>
      `;
    }

    const submitBtnHtml = isGraded ? '' : `
      <div style="text-align:center; margin-top:20px;">
        <button class="btn primary" id="grade-cloze" style="padding: 10px 32px; font-size: 15px;">Chấm điểm</button>
      </div>
    `;

    d.innerHTML = `
      <div class="question-card">
        ${wordBankHtml}
        <div class="cloze-paragraph">
          ${processedParagraph}
        </div>
        ${submitBtnHtml}
        <div id="cloze-feedback-area">${feedbackHtml}</div>
      </div>
    `;

    if (!isGraded) {
      d.querySelectorAll('select.cloze-inline-select').forEach(sel => {
        sel.onchange = () => {
          const bIdx = +sel.dataset.blank;
          const val = sel.value;
          state.answers[bIdx] = val !== '' ? +val : undefined;
        };
      });

      const gradeBtn = document.querySelector('#grade-cloze');
      if (gradeBtn) {
        gradeBtn.onclick = () => {
          state.isGraded = true;
          let s = 0;
          x.blanks.forEach((b, i) => {
            if (state.answers[i] === b.correct_index) s++;
          });

          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { ...state.answers };
            state.currentHistoryItem.score = s;
          }
          saveHistory();

          renderCloze(x);
        };
      }
    }
  }

  /* ---- MATCHING: 5-Slot Card Refill Engine & Bidirectional Matching ---- */
  function renderMatching(x) {
    const d = document.querySelector('#play');
    if (!x || !x.pairs || !x.pairs.length) {
      d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu từ vựng để nối.</p></div>';
      return;
    }

    // Normalize pairs list with unique IDs
    const pairs = x.pairs.map((p, idx) => ({
      id: p.id || ('p_' + Math.random().toString(36).substring(2, 9) + '_' + idx),
      word: p.term || p.word || '',
      meaning: p.definition || p.meaning || ''
    }));

    const totalPairsCount = pairs.length;
    const SLOT_COUNT = 5;

    // Tracking state
    let matchedPairIds = new Set();
    let activeWords = new Array(SLOT_COUNT).fill(null); // { pairId, word }
    let activeMeanings = new Array(SLOT_COUNT).fill(null); // { pairId, meaning }

    let selectedWordIdx = null; // index 0..4 in activeWords
    let selectedMeaningIdx = null; // index 0..4 in activeMeanings

    let wrongCount = 0;
    let matchedCount = 0;
    let totalAttempts = 0;
    let isEvaluating = false;
    let isFinished = false;

    let startTime = Date.now();
    let timerInterval = null;

    // Audio synthesizer
    function playSound(type) {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        if (type === 'match') {
          osc.type = 'sine';
          osc.frequency.setValueAtTime(523.25, ctx.currentTime);
          osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.08);
          osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.16);
          gain.gain.setValueAtTime(0.12, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
          osc.start();
          osc.stop(ctx.currentTime + 0.3);
        } else if (type === 'wrong') {
          osc.type = 'sawtooth';
          osc.frequency.setValueAtTime(220, ctx.currentTime);
          osc.frequency.setValueAtTime(180, ctx.currentTime + 0.08);
          gain.gain.setValueAtTime(0.12, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
          osc.start();
          osc.stop(ctx.currentTime + 0.25);
        }
      } catch (_) {}
    }

    // Helper functions to query unplaced items
    function getUnplacedWordPairs() {
      return pairs.filter(p => !matchedPairIds.has(p.id) && !activeWords.some(slot => slot && slot.pairId === p.id));
    }

    function getUnplacedMeaningPairs() {
      return pairs.filter(p => !matchedPairIds.has(p.id) && !activeMeanings.some(slot => slot && slot.pairId === p.id));
    }

    function getFullyUnplacedPairs() {
      return pairs.filter(p => !matchedPairIds.has(p.id) && !activeWords.some(s => s && s.pairId === p.id) && !activeMeanings.some(s => s && s.pairId === p.id));
    }

    function getMatchedPairsOnScreen() {
      const wordPairIds = new Set(activeWords.filter(Boolean).map(s => s.pairId));
      return activeMeanings.filter(s => s && wordPairIds.has(s.pairId)).map(s => s.pairId);
    }

    // Initialize the 5-slot screen
    function initBoard() {
      matchedPairIds.clear();
      activeWords = new Array(SLOT_COUNT).fill(null);
      activeMeanings = new Array(SLOT_COUNT).fill(null);

      // K guaranteed matching pairs (at least 2-3 pairs)
      const k = Math.min(Math.min(3, Math.ceil(SLOT_COUNT / 2)), pairs.length);
      const shuffledPairs = [...pairs].sort(() => Math.random() - 0.5);
      const guaranteedPairs = shuffledPairs.slice(0, k);

      const leftIndices = [0, 1, 2, 3, 4].sort(() => Math.random() - 0.5);
      const rightIndices = [0, 1, 2, 3, 4].sort(() => Math.random() - 0.5);

      for (let i = 0; i < k; i++) {
        const p = guaranteedPairs[i];
        activeWords[leftIndices[i]] = { pairId: p.id, word: p.word };
        activeMeanings[rightIndices[i]] = { pairId: p.id, meaning: p.meaning };
      }

      // Fill remaining empty left slots with distractor words
      const remainingWordPairs = getUnplacedWordPairs().sort(() => Math.random() - 0.5);
      for (let i = 0; i < SLOT_COUNT; i++) {
        if (!activeWords[i] && remainingWordPairs.length > 0) {
          const p = remainingWordPairs.pop();
          activeWords[i] = { pairId: p.id, word: p.word };
        }
      }

      // Fill remaining empty right slots with distractor meanings
      const remainingMeaningPairs = getUnplacedMeaningPairs().sort(() => Math.random() - 0.5);
      for (let i = 0; i < SLOT_COUNT; i++) {
        if (!activeMeanings[i] && remainingMeaningPairs.length > 0) {
          const p = remainingMeaningPairs.pop();
          activeMeanings[i] = { pairId: p.id, meaning: p.meaning };
        }
      }
    }

    // Refill slots after a successful match
    function refillSlots(emptyLeftIdx, emptyRightIdx) {
      const matchesOnScreen = getMatchedPairsOnScreen();

      if (matchesOnScreen.length > 0) {
        // Normal refill from unplaced pool
        const availWords = getUnplacedWordPairs().sort(() => Math.random() - 0.5);
        if (availWords.length > 0) {
          const p = availWords[0];
          activeWords[emptyLeftIdx] = { pairId: p.id, word: p.word };
        }

        const availMeanings = getUnplacedMeaningPairs().sort(() => Math.random() - 0.5);
        if (availMeanings.length > 0) {
          const p = availMeanings[0];
          activeMeanings[emptyRightIdx] = { pairId: p.id, meaning: p.meaning };
        }
      } else {
        // Forced refill (no match on screen - "bị tắc"): force a full matching pair onto screen
        const unplacedBoth = getFullyUnplacedPairs().sort(() => Math.random() - 0.5);
        if (unplacedBoth.length > 0) {
          const forcedPair = unplacedBoth[0];
          activeWords[emptyLeftIdx] = { pairId: forcedPair.id, word: forcedPair.word };
          activeMeanings[emptyRightIdx] = { pairId: forcedPair.id, meaning: forcedPair.meaning };
        } else {
          // Fallback if no full pair left, fill individually from available
          const availWords = getUnplacedWordPairs();
          if (availWords.length > 0) activeWords[emptyLeftIdx] = { pairId: availWords[0].id, word: availWords[0].word };
          const availMeanings = getUnplacedMeaningPairs();
          if (availMeanings.length > 0) activeMeanings[emptyRightIdx] = { pairId: availMeanings[0].id, meaning: availMeanings[0].meaning };
        }
      }
    }

    function evaluateMatch() {
      if (selectedWordIdx === null || selectedMeaningIdx === null || isEvaluating) return;
      isEvaluating = true;
      totalAttempts++;

      const wSlot = activeWords[selectedWordIdx];
      const mSlot = activeMeanings[selectedMeaningIdx];

      const leftBtn = d.querySelector(`.match-card[data-col="left"][data-idx="${selectedWordIdx}"]`);
      const rightBtn = d.querySelector(`.match-card[data-col="right"][data-idx="${selectedMeaningIdx}"]`);

      if (wSlot && mSlot && wSlot.pairId === mSlot.pairId) {
        // MATCHED
        matchedCount++;
        matchedPairIds.add(wSlot.pairId);
        playSound('match');

        if (leftBtn) {
          leftBtn.classList.remove('selected');
          leftBtn.classList.add('matched');
        }
        if (rightBtn) {
          rightBtn.classList.remove('selected');
          rightBtn.classList.add('matched');
        }

        const emptyL = selectedWordIdx;
        const emptyR = selectedMeaningIdx;

        setSafeTimeout(() => {
          activeWords[emptyL] = null;
          activeMeanings[emptyR] = null;
          selectedWordIdx = null;
          selectedMeaningIdx = null;
          isEvaluating = false;

          refillSlots(emptyL, emptyR);

          if (matchedCount >= totalPairsCount || (!activeWords.some(Boolean) && !activeMeanings.some(Boolean))) {
            finishGame();
          } else {
            renderBoard();
          }
        }, 380);

      } else {
        // WRONG
        wrongCount++;
        playSound('wrong');

        if (leftBtn) {
          leftBtn.classList.remove('selected');
          leftBtn.classList.add('wrong');
        }
        if (rightBtn) {
          rightBtn.classList.remove('selected');
          rightBtn.classList.add('wrong');
        }

        setSafeTimeout(() => {
          if (leftBtn) {
            leftBtn.classList.remove('wrong');
            leftBtn.classList.remove('selected');
          }
          if (rightBtn) {
            rightBtn.classList.remove('wrong');
            rightBtn.classList.remove('selected');
          }
          selectedWordIdx = null;
          selectedMeaningIdx = null;
          isEvaluating = false;
          renderBoard();
        }, 450);
      }
    }

    function handleCardClick(col, idx) {
      if (isEvaluating || isFinished) return;

      if (col === 'left') {
        if (!activeWords[idx]) return;
        selectedWordIdx = selectedWordIdx === idx ? null : idx;
      } else if (col === 'right') {
        if (!activeMeanings[idx]) return;
        selectedMeaningIdx = selectedMeaningIdx === idx ? null : idx;
      }

      renderBoard();

      if (selectedWordIdx !== null && selectedMeaningIdx !== null) {
        evaluateMatch();
      }
    }

    function finishGame() {
      if (isFinished) return;
      isFinished = true;
      if (timerInterval) clearInterval(timerInterval);

      const elapsedSec = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      const mins = Math.floor(elapsedSec / 60);
      const secs = elapsedSec % 60;
      const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      const accuracy = totalAttempts > 0 ? Math.round((matchedCount / totalAttempts) * 100) : (matchedCount > 0 ? 100 : 0);

      // Cập nhật thống kê tích lũy
      if (!state.matchingStats) loadMatchingStats();
      const stats = state.matchingStats;
      const record = {
        time: Date.now(),
        pairs: totalPairsCount,
        matched: matchedCount,
        wrong: wrongCount,
        attempts: totalAttempts,
        elapsed_sec: elapsedSec,
        accuracy: accuracy
      };

      stats.records.unshift(record);
      if (stats.records.length > 30) stats.records.length = 30;

      stats.aggregates.total_games += 1;
      stats.aggregates.total_correct += matchedCount;
      stats.aggregates.total_wrong += wrongCount;
      
      const totalAccSum = stats.records.reduce((sum, r) => sum + r.accuracy, 0);
      stats.aggregates.avg_accuracy = Math.round(totalAccSum / stats.records.length);

      const totalTimeSum = stats.records.reduce((sum, r) => sum + r.elapsed_sec, 0);
      stats.aggregates.avg_time_sec = Math.round(totalTimeSum / stats.records.length);

      if (accuracy === 100 && elapsedSec < stats.aggregates.best_time_sec) {
        stats.aggregates.best_time_sec = elapsedSec;
      }

      saveMatchingStats();

      const bestTimeStr = stats.aggregates.best_time_sec !== 999999 ? 
        `${Math.floor(stats.aggregates.best_time_sec / 60)}m ${stats.aggregates.best_time_sec % 60}s` : 'N/A';

      const statsSummaryHtml = `
        <div class="stats-summary-box" style="margin-top: 20px; padding: 12px; border-top: 1px dashed var(--border); font-size: 13px; color: var(--text-secondary);">
          🏆 <b>Thống kê tích lũy:</b> Đã chơi: <b>${stats.aggregates.total_games}</b> bài · Độ chính xác TB: <b>${stats.aggregates.avg_accuracy}%</b> · Nhanh nhất (100% đúng): <b>${bestTimeStr}</b>
        </div>
      `;

      d.innerHTML = `
        <div class="feedback good" style="text-align:center; padding: 24px;">
          <h2 style="margin-bottom:12px; color: var(--success);">🎉 Ghép đôi hoàn thành!</h2>
          <div style="font-size:16px; margin-bottom:20px; line-height:1.6;">
            <p>⏱️ Thời gian: <b>${timeStr}</b></p>
            <p>🎯 Ghép đúng: <b>${matchedCount}/${totalPairsCount}</b> cặp từ</p>
            <p>❌ Số lần ghép sai: <b>${wrongCount}</b> lần</p>
            <p>📊 Độ chính xác: <b>${accuracy}%</b></p>
          </div>
          ${statsSummaryHtml}
          <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; margin-top:20px;">
            <button class="btn primary" id="restart-matching-btn" style="padding: 10px 24px;">🔄 Chơi lại bài này</button>
            <button class="btn btn-outline" id="new-matching-btn" style="padding: 10px 24px;">⚡ Tạo bài nối mới</button>
          </div>
        </div>
      `;

      resetGameState('matching');
      const restartBtn = d.querySelector('#restart-matching-btn');
      if (restartBtn) restartBtn.onclick = () => renderMatching(x);
      const newBtn = d.querySelector('#new-matching-btn');
      if (newBtn) newBtn.onclick = () => nav('home');
    }

    function renderBoard() {
      if (isFinished) return;

      const elapsedSec = Math.max(0, Math.round((Date.now() - startTime) / 1000));
      const mins = Math.floor(elapsedSec / 60);
      const secs = elapsedSec % 60;
      const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      const accuracy = totalAttempts > 0 ? Math.round((matchedCount / totalAttempts) * 100) : 100;

      const leftSlotsHtml = activeWords.map((slot, i) => {
        if (!slot) return `<div class="match-slot empty-slot"></div>`;
        const isSelected = selectedWordIdx === i;
        return `
          <div class="match-slot">
            <button class="match-card ${isSelected ? 'selected' : ''}" data-col="left" data-idx="${i}">
              ${esc(slot.word)}
            </button>
          </div>
        `;
      }).join('');

      const rightSlotsHtml = activeMeanings.map((slot, i) => {
        if (!slot) return `<div class="match-slot empty-slot"></div>`;
        const isSelected = selectedMeaningIdx === i;
        return `
          <div class="match-slot">
            <button class="match-card ${isSelected ? 'selected' : ''}" data-col="right" data-idx="${i}">
              ${esc(slot.meaning)}
            </button>
          </div>
        `;
      }).join('');

      d.innerHTML = `
        <div class="matching-container">
          <div class="matching-toolbar">
            <div class="matching-stats-group">
              <span class="matching-stat-badge">⏱️ <span id="m-timer">${timeStr}</span></span>
              <span class="matching-stat-badge">🎯 <span style="color:var(--primary);">${matchedCount}/${totalPairsCount}</span> cặp</span>
              <span class="matching-stat-badge">❌ Sai: <span style="color:${wrongCount > 0 ? 'var(--error)' : 'inherit'};">${wrongCount}</span></span>
              <span class="matching-stat-badge">📊 <span style="color:${accuracy >= 80 ? 'var(--success)' : 'var(--primary)'};">${accuracy}%</span></span>
            </div>
            <button class="btn btn-outline" id="finish-matching-btn" style="padding:6px 14px; font-size:13px; color:var(--error); border-color:var(--error);">
              🏁 Kết thúc
            </button>
          </div>

          <div class="match-board">
            <div class="match-col">
              <div class="match-col-header">Từ vựng</div>
              ${leftSlotsHtml}
            </div>
            <div class="match-col">
              <div class="match-col-header">Nghĩa</div>
              ${rightSlotsHtml}
            </div>
          </div>
        </div>
      `;

      d.querySelectorAll('[data-col]').forEach(btn => {
        btn.onclick = () => {
          handleCardClick(btn.dataset.col, +btn.dataset.idx);
        };
      });

      const finishBtn = d.querySelector('#finish-matching-btn');
      if (finishBtn) {
        finishBtn.onclick = () => finishGame();
      }
    }

    initBoard();

    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setSafeInterval(() => {
      if (isFinished) {
        clearInterval(timerInterval);
        return;
      }
      const timerEl = document.querySelector('#m-timer');
      if (timerEl) {
        const elapsedSec = Math.max(0, Math.round((Date.now() - startTime) / 1000));
        const mins = Math.floor(elapsedSec / 60);
        const secs = elapsedSec % 60;
        timerEl.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      }
    }, 1000);

    renderBoard();
  }

  let unscrambleDragState = null;

  function renderUnscrambleAll(x) {
    const d = document.querySelector('#play');
    if (!x?.questions?.length) { d.innerHTML = '<div class="empty-state"><p>Không có câu hỏi.</p></div>'; return; }
    const isGraded = !!state.isGraded;
    const gameId = state.route;

    let score = 0;
    if (isGraded) {
      x.questions.forEach((q, i) => {
        const feedbackObj = state.answers[`feedback_${i}`];
        if (feedbackObj && feedbackObj.correct) score++;
      });
    }

    const cardsHtml = x.questions.map((q, i) => {
      const chosen = state.answers[i] || [];
      const isCorrect = isGraded && state.answers[`feedback_${i}`]?.correct;
      const feedbackObj = isGraded ? state.answers[`feedback_${i}`] : null;
      const isUnanswered = isGraded && (!feedbackObj || feedbackObj.unanswered);

      let cardClass = 'question-card unscramble-card fade-in';
      if (isGraded) {
        if (isUnanswered) cardClass += ' unanswered-card';
        else cardClass += isCorrect ? ' correct-card' : ' wrong-card';
      }

      // Đề bài (các từ xáo trộn nối bằng " / ")
      const rawPromptText = `<b>Đề bài:</b> ${q.shuffled_words.join(' / ')}`;

      // Khung hiển thị câu đang ghép/câu đúng nổi bật theo 3 kịch bản
      let sentenceDisplayHtml = '';
      if (isGraded) {
        if (isCorrect) {
          // Kịch bản 1: Đúng (Correct)
          sentenceDisplayHtml = `
            <div class="unscramble-correct-box" style="margin-top:12px; padding:14px 16px; border:2px solid var(--success); border-radius:8px; background:rgba(46, 204, 113, 0.02);">
              <div style="font-size:12px; font-weight:700; color:white; background:var(--success); padding:3px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">🟢 ĐÚNG</div>
              <p style="margin:4px 0 8px; font-size:15px; font-weight:600; color:var(--success);">🎉 ${esc(feedbackObj.praise || 'Chính xác! Lựa chọn trật tự từ hoàn hảo.')}</p>
              <div style="font-size:18px; font-weight:700; color:var(--success); margin:8px 0;">
                ✓ ${esc(q.correct_sentence)}
              </div>
              ${feedbackObj.highlight ? `
                <p style="margin:8px 0 0; font-size:13.5px; color:var(--text-secondary); line-height:1.4;">
                  💡 <b>Điểm sáng:</b> ${esc(feedbackObj.highlight)}
                </p>
              ` : ''}
            </div>
          `;
        } else if (isUnanswered) {
          // Kịch bản 3: Bỏ trống (Unanswered)
          sentenceDisplayHtml = `
            <div class="unscramble-unanswered-box" style="margin-top:12px; padding:14px 16px; border:2px solid var(--border); border-radius:8px; background:rgba(0,0,0,0.02);">
              <div style="font-size:12px; font-weight:700; color:white; background:var(--text-secondary); padding:3px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">⚪ CHƯA TRẢ LỜI</div>
              <div style="font-size:18px; font-weight:700; color:var(--primary); margin:8px 0;">
                ✅ ${esc(q.correct_sentence)}
              </div>
              ${q.meaning_vi ? `<p style="margin:6px 0; font-size:14px;">📖 <b>Dịch nghĩa:</b> ${esc(q.meaning_vi)}</p>` : ''}
              ${q.core_structure ? `<p style="margin:6px 0; font-size:13.5px; color:var(--text-secondary);">💡 <b>Cấu trúc chính:</b> <code>${esc(q.core_structure)}</code></p>` : ''}
            </div>
          `;
        } else {
          // Kịch bản 2: Sai (Incorrect)
          sentenceDisplayHtml = `
            <div class="unscramble-wrong-box" style="margin-top:12px; padding:14px 16px; border:2px solid #ef4444; border-radius:8px; background:rgba(239, 68, 68, 0.02);">
              <div style="font-size:12px; font-weight:700; color:white; background:#ef4444; padding:3px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">🔴 SAI</div>
              <p style="margin:4px 0 8px; font-size:14px; font-weight:600; color:#ef4444;">⚠️ Vị trí sai: ${esc(feedbackObj.error_position || 'Trật tự các từ chưa đúng.')}</p>
              
              <div class="unscramble-compare" style="margin:10px 0; padding:10px; border-left:3px solid #ef4444; background:rgba(239,68,68,0.02); border-radius:4px;">
                <p style="margin:2px 0; font-size:13.5px;">❌ <b>Câu của bạn:</b> <span style="color:#ef4444; font-weight:600;">${esc(chosen.join(' '))}</span></p>
                <p style="margin:2px 0; font-size:13.5px;">✅ <b>Đáp án đúng:</b> <span style="color:var(--success); font-weight:600;">${esc(q.correct_sentence)}</span></p>
              </div>

              ${feedbackObj.rule ? `
                <p style="margin:8px 0 0; font-size:13.5px; color:var(--text-secondary); line-height:1.4;">
                  💡 <b>Giải thích:</b> ${esc(feedbackObj.rule)}
                </p>
              ` : ''}
            </div>
          `;
        }
      } else {
        sentenceDisplayHtml = `
          <div class="unscramble-sentence-box" id="sentence-box-${i}" style="min-height:58px; padding:12px 16px; border:2px dashed var(--border); border-radius:8px; display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:12px; background:rgba(0,0,0,0.01); transition:all 0.2s;">
            <span style="color:var(--text-secondary); font-style:italic;">Bấm hoặc kéo các từ bên dưới vào đây...</span>
          </div>
        `;
      }

      // Hàng chip từ để chọn (chỉ hiện khi chưa chấm)
      let chipsHtml = '';
      if (!isGraded) {
        chipsHtml = `
          <div class="drag-container" id="chips-container-${i}" style="margin-top:14px; display:flex; flex-wrap:wrap; gap:8px; padding:12px 0; min-height:48px; border-radius:8px; transition:all 0.2s;"></div>
        `;
      }

      return `
        <div class="${cardClass}" style="margin-bottom:24px; padding:16px; border:1px solid var(--border); border-radius:8px; background:var(--card-bg);">
          <p style="font-size:14.5px; color:var(--text-secondary); margin-bottom:10px; line-height:1.4;">${rawPromptText}</p>
          ${sentenceDisplayHtml}
          ${chipsHtml}
        </div>
      `;
    }).join('');

    let submitBtnHtml = '';
    if (isGraded) {
      submitBtnHtml = `
        <div class="result-summary-bar" style="margin-top:24px; padding:16px; background:var(--card-bg); border:1px solid var(--border); border-radius:8px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:16px; font-weight:700;">
            📊 Kết quả bài làm: <span style="font-size:20px; color:${score===x.questions.length?'var(--success)':'var(--primary)'}">${score}/${x.questions.length}</span> câu chính xác.
          </div>
          <button class="btn" id="story-new-btn">Tạo bài mới</button>
        </div>
      `;
    } else {
      submitBtnHtml = `
        <div style="text-align:right; margin-top:24px;">
          <button class="btn" id="grade-unscramble" style="padding:10px 24px; font-weight:700;">Nộp bài & Chấm điểm</button>
        </div>
      `;
    }

    d.innerHTML = cardsHtml + submitBtnHtml;

    // Cập nhật DOM cục bộ ban đầu của từng card câu hỏi
    x.questions.forEach((q, i) => {
      if (!isGraded) {
        updateUnscrambleCardDOM(i, q);
      }
    });

    function updateUnscrambleCardDOM(qIdx, question) {
      const chosenBox = d.querySelector(`#sentence-box-${qIdx}`);
      const chipsBox = d.querySelector(`#chips-container-${qIdx}`);
      if (!chosenBox || !chipsBox) return;

      const chosen = state.answers[qIdx] || [];
      const remainingWords = question.shuffled_words.filter((w, j) => {
        const timesInShuffled = question.shuffled_words.slice(0, j + 1).filter(x => x === w).length;
        const timesInChosen = chosen.filter(x => x === w).length;
        return timesInChosen < timesInShuffled;
      });

      // 1. Cập nhật ô chứa các từ đã chọn
      if (chosen.length) {
        chosenBox.innerHTML = chosen.map((w, wIdx) => 
          `<button class="drag-word" draggable="true" data-back-idx="${wIdx}" style="padding:6px 12px; background:var(--primary); color:white; border:none; border-radius:4px; font-size:14px; font-weight:600; cursor:pointer; box-shadow:0 2px 4px rgba(0,0,0,0.08); transition:all 0.2s;">${esc(w)}</button>`
        ).join('');

        chosenBox.querySelectorAll('[data-back-idx]').forEach(btn => {
          // Sự kiện click (Dự phòng)
          btn.onclick = () => {
            const wIdx = +btn.dataset.backIdx;
            state.answers[qIdx].splice(wIdx, 1);
            updateUnscrambleCardDOM(qIdx, question);
          };
          // Sự kiện Drag
          btn.ondragstart = (e) => {
            unscrambleDragState = { qIdx, word: btn.textContent, type: 'chosen', index: +btn.dataset.backIdx };
            e.dataTransfer.effectAllowed = 'move';
          };
        });
      } else {
        chosenBox.innerHTML = '<span style="color:var(--text-secondary); font-style:italic;">Bấm hoặc kéo các từ bên dưới vào đây...</span>';
      }

      // 2. Cập nhật các chips từ gợi ý
      chipsBox.innerHTML = remainingWords.map((w) => 
        `<button class="drag-word" draggable="true" data-word="${esc(w)}" style="padding:6px 12px; background:var(--card-bg); border:1px solid var(--border); border-radius:4px; font-size:14px; cursor:pointer; box-shadow:0 1px 3px rgba(0,0,0,0.05); transition:all 0.2s;">${esc(w)}</button>`
      ).join('');

      chipsBox.querySelectorAll('[data-word]').forEach(btn => {
        // Sự kiện click (Dự phòng)
        btn.onclick = () => {
          const word = btn.dataset.word;
          if (!state.answers[qIdx]) state.answers[qIdx] = [];
          state.answers[qIdx].push(word);
          updateUnscrambleCardDOM(qIdx, question);
        };
        // Sự kiện Drag
        btn.ondragstart = (e) => {
          unscrambleDragState = { qIdx, word: btn.dataset.word, type: 'chip' };
          e.dataTransfer.effectAllowed = 'copy';
        };
      });

      // 3. Sự kiện Drop/DragOver cho ChosenBox
      chosenBox.ondragover = (e) => {
        if (unscrambleDragState && unscrambleDragState.qIdx === qIdx) {
          e.preventDefault();
          chosenBox.style.border = '2px dashed var(--primary)';
          chosenBox.style.background = 'rgba(54, 162, 235, 0.03)';
        }
      };
      chosenBox.ondragleave = () => {
        chosenBox.style.border = '2px dashed var(--border)';
        chosenBox.style.background = 'rgba(0,0,0,0.01)';
      };
      chosenBox.ondrop = (e) => {
        e.preventDefault();
        chosenBox.style.border = '2px dashed var(--border)';
        chosenBox.style.background = 'rgba(0,0,0,0.01)';
        if (!unscrambleDragState || unscrambleDragState.qIdx !== qIdx) return;

        if (unscrambleDragState.type === 'chip') {
          // Kéo từ chip vào hộp
          if (!state.answers[qIdx]) state.answers[qIdx] = [];
          state.answers[qIdx].push(unscrambleDragState.word);
        } else if (unscrambleDragState.type === 'chosen') {
          // Kéo đổi vị trí trong hộp
          const chosenArr = state.answers[qIdx] || [];
          const movedWord = chosenArr.splice(unscrambleDragState.index, 1)[0];
          
          const targetBtn = e.target.closest('[data-back-idx]');
          if (targetBtn) {
            const targetIdx = +targetBtn.dataset.backIdx;
            chosenArr.splice(targetIdx, 0, movedWord);
          } else {
            chosenArr.push(movedWord);
          }
        }
        updateUnscrambleCardDOM(qIdx, question);
        unscrambleDragState = null;
      };

      // 4. Sự kiện Drop/DragOver cho ChipsBox (thả trả lại chip)
      chipsBox.ondragover = (e) => {
        if (unscrambleDragState && unscrambleDragState.qIdx === qIdx && unscrambleDragState.type === 'chosen') {
          e.preventDefault();
          chipsBox.style.background = 'rgba(0,0,0,0.04)';
        }
      };
      chipsBox.ondragleave = () => {
        chipsBox.style.background = 'transparent';
      };
      chipsBox.ondrop = (e) => {
        e.preventDefault();
        chipsBox.style.background = 'transparent';
        if (!unscrambleDragState || unscrambleDragState.qIdx !== qIdx) return;

        if (unscrambleDragState.type === 'chosen') {
          // Gỡ từ
          state.answers[qIdx].splice(unscrambleDragState.index, 1);
          updateUnscrambleCardDOM(qIdx, question);
        }
        unscrambleDragState = null;
      };
    }

    // Nút nộp bài chấm điểm
    if (!isGraded) {
      const gradeBtn = document.querySelector('#grade-unscramble');
      if (gradeBtn) {
        gradeBtn.onclick = async () => {
          try {
            setBusy(true, 'Đang chấm bài bằng AI...');
            const signal = getSignal();
            
            for (let i = 0; i < x.questions.length; i++) {
              if (signal.aborted) return;
              const q = x.questions[i];
              const userAns = (state.answers[i] || []).join(' ');
              
              if (!userAns.trim()) {
                // Kịch bản 3: Chưa làm -> Không cần gọi AI chấm
                state.answers[`feedback_${i}`] = {
                  correct: false,
                  unanswered: true
                };
                continue;
              }

              const feedback = await Bridge.sendAsync('ai_grade', {
                gamemode: 'unscramble',
                level: document.querySelector('#level').value,
                user_answer: userAns,
                expected: q.correct_sentence,
                correct_sentence: q.correct_sentence
              }, { signal });
              
              state.answers[`feedback_${i}`] = feedback;
            }

            state.isGraded = true;
            setBusy(false);

            let finalScore = 0;
            x.questions.forEach((q, i) => {
              if (state.answers[`feedback_${i}`]?.correct) finalScore++;
            });

            const historyItem = addHistory(gameId, x);
            state.currentHistoryItem = historyItem;
            if (state.currentHistoryItem) {
              state.currentHistoryItem.answers = { ...state.answers };
              state.currentHistoryItem.score = finalScore;
            }
            saveHistory();

            renderUnscrambleAll(x);
          } catch (e) {
            setBusy(false);
            showBridgeFailure(e);
          }
        };
      }
    } else {
      const newBtn = document.querySelector('#story-new-btn');
      if (newBtn) {
        newBtn.onclick = () => generate(gameId);
      }
    }
  }

  function resetGameState(gameId) {
    state.exercise = null;
    state.answers = {};
    state.isGraded = false;
    state.index = 0;
    state.currentHistoryItem = null;
    state.hintedQuestions = new Set();
    if (gameId === 'taboo') {
      state.tabooCursor = 0;
      state.tabooOrder = [];
    }
    const d = document.querySelector('#play');
    if (d) d.innerHTML = '';
  }

  /* ---- STORY: read + comprehension questions (Vertical options, Detailed Explanation & Evidence) ---- */
  function renderStory(x) {
    const d = document.querySelector('#play');
    if (!d) return;
    if (!x || !x.story) {
      d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu bài đọc.</p></div>';
      return;
    }

    const isGraded = !!state.isGraded;
    const gameId = state.route;
    
    const isNewSchema = !!x.questions;
    const questions = isNewSchema ? (x.questions || []) : (x.comprehension_questions || []);

    let score = 0;
    if (isGraded && questions.length) {
      questions.forEach((q, i) => {
        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;
        if (state.answers[i] === correctIdx) score++;
      });
    }

    const targetWords = questions
      .filter(q => q.type === 'vocabulary' && q.target_word)
      .map(q => q.target_word);

    function highlightWords(text, words) {
      if (!words || !words.length) return esc(text);
      const sortedWords = [...words]
        .filter(Boolean)
        .map(w => w.trim())
        .filter(w => w.length > 0)
        .sort((a, b) => b.length - a.length);

      if (!sortedWords.length) return esc(text);

      const escapedText = esc(text);
      const escapedSortedWords = sortedWords.map(w => esc(w).replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'));
      const escPattern = new RegExp(`\\b(${escapedSortedWords.join('|')})\\b`, 'gi');

      return escapedText.replace(escPattern, (match) => `<b class="story-target-word">${match}</b>`);
    }

    let title = "";
    let content = "";
    let fullTranslation = "";

    if (typeof x.story === 'object') {
      title = x.story.title || "";
      content = x.story.content || "";
      fullTranslation = x.story.full_translation || "";
    } else {
      content = String(x.story || "");
    }

    const passageHtml = `
      <div class="story-passage-card">
        <div class="story-passage-header">
          <span class="story-passage-title">📖 ${title ? esc(title) : 'Bài đọc hiểu (Reading Passage)'}</span>
          <span class="story-passage-badge">${questions.length} câu hỏi</span>
        </div>
        <div class="story-passage-content" style="font-size:15px; line-height:1.6;">
          ${highlightWords(content, targetWords).replace(/\n\n/g, '<br><br>')}
        </div>
        ${fullTranslation ? `
          <details style="margin-top:12px; border-top:1px dashed var(--border); padding-top:10px;">
            <summary style="cursor:pointer; font-weight:600; color:var(--primary);">🌐 Xem bản dịch tiếng Việt</summary>
            <div style="margin-top:8px; font-size:14.5px; color:var(--text); line-height:1.6;">
              ${esc(fullTranslation).replace(/\n\n/g, '<br><br>')}
            </div>
          </details>
        ` : ''}
      </div>
    `;

    if (!questions.length) {
      d.innerHTML = `
        <div class="story-container">
          ${passageHtml}
          <div class="feedback bad" style="margin-top:20px; padding:16px; border-radius:8px;">
            <p style="margin:0;"><b>⚠️ Không thể tạo câu hỏi tự động:</b> Rất tiếc, hệ thống không thể khởi tạo bộ câu hỏi đọc hiểu cho bài này. Vui lòng đọc nội dung trên hoặc bấm <b>"Tạo bài"</b> để tạo bài đọc mới.</p>
          </div>
        </div>
      `;
      return;
    }

    // Questions list
    const questionsHtml = questions.map((q, i) => {
      const chosen = state.answers[i];

      const optionsHtml = q.options.map((opt, oIdx) => {
        let btnCls = 'story-option-btn';
        let disabledAttr = isGraded ? 'disabled' : '';
        let optText = typeof opt === 'object' ? opt.text : opt;

        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;

        if (isGraded) {
          if (oIdx === correctIdx) {
            btnCls += ' correct';
          } else if (oIdx === chosen) {
            btnCls += ' wrong';
          }
        } else {
          if (oIdx === chosen) {
            btnCls += ' selected';
          }
        }

        const optionLetter = String.fromCharCode(65 + oIdx);

        return `
          <button class="${btnCls}" data-q="${i}" data-choice="${oIdx}" ${disabledAttr}>
            <span class="story-option-letter">${optionLetter}.</span>
            <span class="story-option-text">${esc(optText)}</span>
          </button>
        `;
      }).join('');

      // Explanation & Evidence block after grading
      let explanationHtml = '';
      if (isGraded) {
        const quoteText = q.evidence_quote || q.quote_evidence || q.evidence || '';
        const quoteSection = quoteText ? `
          <div class="story-evidence-box">
            <span class="story-box-icon">📌</span>
            <div>
              <b>Dẫn chứng trong bài đọc:</b>
              <div class="story-quote-text">"${esc(quoteText)}"</div>
            </div>
          </div>
        ` : '';

        const explanationSection = q.explanation ? `
          <div class="story-explanation-box">
            <span class="story-box-icon">💡</span>
            <div>
              <b>Giải thích đáp án:</b>
              <div class="story-exp-text">${esc(q.explanation)}</div>
            </div>
          </div>
        ` : '';

        explanationHtml = `
          <div class="story-feedback-details fade-in">
            ${explanationSection}
            ${quoteSection}
          </div>
        `;
      }

      let qStatusBadge = '';
      let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
      if (correctIdx === -1) correctIdx = q.correct_index;

      if (isGraded) {
        if (chosen === undefined) {
          qStatusBadge = `<span class="q-badge unselected">Chưa làm</span>`;
        } else if (chosen === correctIdx) {
          qStatusBadge = `<span class="q-badge correct">✓ Đúng</span>`;
        } else {
          qStatusBadge = `<span class="q-badge wrong">✕ Sai</span>`;
        }
      }

      const typeBadge = q.type ? `<span class="q-type-badge">${esc(q.type)}</span>` : '';

      return `
        <div class="story-question-card ${isGraded ? (chosen === correctIdx ? 'correct-border' : 'wrong-border') : ''}">
          <div class="story-q-header">
            <span class="story-q-number">Câu ${i + 1}/${questions.length} ${typeBadge}</span>
            ${qStatusBadge}
          </div>
          <p class="story-q-text">${esc(q.question)}</p>
          <div class="story-options-column" id="story-opts-${i}">
            ${optionsHtml}
          </div>
          ${explanationHtml}
        </div>
      `;
    }).join('');

    // Bottom submit / score header
    let footerHtml = '';
    if (isGraded) {
      const accuracyPct = Math.round((score / questions.length) * 100);
      footerHtml = `
        <div class="story-result-summary fade-in">
          <div class="story-score-title">🎉 Kết quả bài đọc hiểu</div>
          <div class="story-score-main">${score} / ${questions.length} câu đúng (${accuracyPct}%)</div>
          ${x.discussion_prompt ? `
            <div style="margin-top: 14px; text-align: left; padding: 14px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px;">
              <b>💬 Gợi ý thảo luận/nói:</b>
              <p style="margin: 6px 0 0 0; font-style: italic; font-size:14px; line-height:1.5;">${esc(x.discussion_prompt)}</p>
            </div>
          ` : ''}
          <div class="story-actions">
            <button class="btn primary" id="story-retry-btn">🔄 Làm lại bài này</button>
            <button class="btn btn-outline" id="story-new-btn">⚡ Tạo bài đọc mới</button>
          </div>
        </div>
      `;
    } else {
      footerHtml = `
        <div class="story-submit-bar">
          <button class="btn primary" id="story-grade-btn" style="padding: 12px 36px; font-size: 16px;">
            Chấm điểm toàn bộ
          </button>
        </div>
      `;
    }

    d.innerHTML = `
      <div class="story-container">
        ${passageHtml}
        <div class="story-questions-section">
          ${questionsHtml}
        </div>
        ${footerHtml}
      </div>
    `;

    // Handlers
    if (!isGraded) {
      d.querySelectorAll('[data-choice]').forEach(btn => {
        btn.onclick = () => {
          if (state.isGraded) return;
          const qIdx = +btn.dataset.q;
          const cIdx = +btn.dataset.choice;

          state.answers[qIdx] = cIdx;
          const opts = d.querySelectorAll(`#story-opts-${qIdx} [data-choice]`);
          opts.forEach(o => o.classList.remove('selected'));
          btn.classList.add('selected');
        };
      });

      const gradeBtn = document.querySelector('#story-grade-btn');
      if (gradeBtn) {
        gradeBtn.onclick = () => {
          state.isGraded = true;
          let currentScore = 0;
          questions.forEach((q, i) => {
            let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
            if (correctIdx === -1) correctIdx = q.correct_index;
            if (state.answers[i] === correctIdx) currentScore++;
          });

          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { ...state.answers };
            state.currentHistoryItem.score = currentScore;
          }
          saveHistory();

          renderStory(x);
        };
      }
    } else {
      const retryBtn = document.querySelector('#story-retry-btn');
      if (retryBtn) {
        retryBtn.onclick = () => {
          state.answers = {};
          state.isGraded = false;
          play(gameId);
        };
      }

      const newBtn = document.querySelector('#story-new-btn');
      if (newBtn) {
        newBtn.onclick = () => generate(gameId);
      }
    }
  }

  /* ---- TRANSLATION: 1 sentence, detailed AI grade ---- */
  function renderTranslation(x){
    if (!x || (!x.source_sentence && (!x.sentences || !x.sentences.length))) { const d=document.querySelector('#play'); if(d)d.innerHTML='<div class="empty-state"><p>Không có dữ liệu bài tập.</p></div>'; return; }
    const isNewSchema = !!x.source_sentence;
    const sourceText = isNewSchema ? x.source_sentence : (x.sentences && x.sentences[0] ? x.sentences[0].source_text : '');
    const targetText = isNewSchema ? x.reference_translation : (x.sentences && x.sentences[0] ? x.sentences[0].target_text : '');
    const alternativeTranslations = isNewSchema ? x.alternative_translations : [];

    document.querySelector('#play').innerHTML='<div class="question-card"><p class="q-text">'+esc(sourceText)+'</p><textarea id="answer" placeholder="'+esc(t('placeholder.translation', 'Nhập bản dịch…'))+'"></textarea><button class="btn" id="grade">'+esc(t('app.grade', 'Chấm điểm'))+'</button><div id="feedback"></div></div>';
    document.querySelector('#grade').onclick=async()=>{
      const signal = getSignal();
      try{
        setBusy(true, t('app.grading', 'Đang chấm điểm…'));
        let r=await Bridge.sendAsync('ai_grade',{
          gamemode:'translation',
          level:document.querySelector('#level').value,
          user_answer:document.querySelector('#answer').value,
          expected:targetText,
          reference_translation:targetText,
          source_text:sourceText,
          source_sentence:sourceText
        }, { signal });
        
        if (signal.aborted) return;
        const fb=document.querySelector('#feedback');
        if(!fb)return;
        
        let html='<div class="feedback '+(r.correct?'good':'bad')+'"><b>'+(r.correct?esc(t('feedback.exact', 'Chính xác!')):esc(t('feedback.needs_improvement', 'Cần cải thiện')))+'</b>';
        
        // Hiển thị Đánh giá chung
        if (typeof r.score !== 'undefined') {
          const lv = r.level || (r.correct ? 'Đạt' : 'Cần cải thiện');
          html += `<div class="overall-grade" style="margin-top:10px; padding:10px; background:rgba(0,0,0,0.02); border-radius:6px; border-left:4px solid ${r.correct?'var(--success)':'var(--error)'}">
            <p style="margin: 0;">📊 <b>${esc(t('feedback.overall_grade', 'ĐÁNH GIÁ CHUNG'))}:</b> Điểm số: <span style="font-size:16px; font-weight:700; color:${r.correct?'var(--success)':'var(--error)'}">${r.score}/10</span> (${esc(lv)})</p>
          </div>`;
        }
        
        // Hiển thị Phân tích lỗi
        if (r.errors && r.errors.length) {
          html += '<hr><p><b>🔍 ' + esc(t('feedback.error_analysis', 'PHÂN TÍCH LỖI:')) + '</b></p>';
          r.errors.forEach(err => {
            if (typeof err === 'object' && err.name) {
              html += `<div class="error-item" style="margin-bottom:12px; padding:8px 12px; border-left:3px solid var(--error); background:rgba(239, 68, 68, 0.02); border-radius:4px;">
                <p style="margin:2px 0;">🔴 <b>Lỗi:</b> ${esc(err.name)}</p>
                <p style="margin:2px 0; padding-left:14px; font-size:13px;">❌ <b>Lỗi sai:</b> <span style="color:var(--error);">${esc(err.wrong)}</span> ➔ <b>Vì sao sai:</b> <i>${esc(err.reason)}</i></p>
                <p style="margin:2px 0; padding-left:14px; font-size:13px;">💡 <b>Gợi ý sửa:</b> <span style="color:var(--success); font-weight:600;">${esc(err.suggestion)}</span> ➔ <b>Vì sao sửa:</b> <i>${esc(err.why)}</i></p>
              </div>`;
            } else {
              html += `<p>• ${esc(err)}</p>`;
            }
          });
        } else if (r.explanation || r.feedback) {
          html += `<p>${esc(r.explanation || r.feedback)}</p>`;
        }
        
        // Hiển thị Đáp án gợi ý
        if (r.suggested_answers) {
          html += '<hr><p><b>✅ ' + esc(t('feedback.suggested_answers_title', 'ĐÁP ÁN GỢI Ý:')) + '</b></p>';
          if (r.suggested_answers.common) {
            html += `<p style="margin:4px 0;">• <b>Thông thường (Common):</b> <span style="color:var(--success); font-weight:600;">${esc(r.suggested_answers.common)}</span></p>`;
          }
          if (r.suggested_answers.advanced) {
            html += `<p style="margin:4px 0;">• <b>Nâng cao (Advanced):</b> <span style="color:var(--success); font-weight:600;">${esc(r.suggested_answers.advanced)}</span></p>`;
          }
        } else {
          html += '<p>' + esc(t('feedback.answer_label', 'Đáp án: {0}', targetText)) + '</p>';
        }
        

        if (alternativeTranslations && alternativeTranslations.length) {
          html += '<p><b>' + esc(t('feedback.alt_translations', 'Cách dịch khác:')) + '</b></p><ul>';
          alternativeTranslations.forEach(a => {
            const txt = typeof a === 'object' ? a.text : a;
            const note = typeof a === 'object' ? a.note : '';
            html += `<li>${esc(txt)} ${note ? `<i>(${esc(note)})</i>` : ''}</li>`;
          });
          html += '</ul>';
        }
        
        html+='<button class="btn" id="retry-trans">'+esc(t('app.retry', 'Làm lại'))+'</button></div>';
        fb.innerHTML=html;
        const retryBtn=document.querySelector('#retry-trans');
        if(retryBtn)retryBtn.onclick=()=>{state.answers={};play(state.route)}
      }catch(e){
        if(e.name==='AbortError'||e.error_code==='E_ABORTED')return;
        showBridgeFailure(e);
      }finally{
        if(!signal.aborted)setBusy(false)
      }
    }
  }

  /* ---- SENTENCE TRANSFORM: 1 sentence, focus selector, detailed ---- */
  function renderSentenceTransform(x){
    if (!x?.questions?.length) { const d=document.querySelector('#play'); if(d)d.innerHTML='<div class="empty-state"><p>Không có câu hỏi.</p></div>'; return; }
    const q=x.questions[0];
    const originalText = q.original || q.original_sentence || '';
    const instructionText = q.prompt || q.instruction || '';
    const expectedText = q.expected_answer || '';
    const normExpected = q.normalized_answer || norm(expectedText);

    document.querySelector('#play').innerHTML='<div class="question-card"><p class="q-text"><b>'+esc(t('feedback.requirement', 'Yêu cầu:'))+'</b> '+esc(instructionText)+'</p><p class="q-text"><b>'+esc(t('feedback.original_sentence', 'Câu gốc:'))+'</b> '+esc(originalText)+'</p><textarea id="answer" placeholder="'+esc(t('placeholder.sentence_transform', 'Nhập câu trả lời...'))+'"></textarea><div style="display:flex; gap:12px; margin-top:12px;"><button class="btn primary" id="grade">'+esc(t('app.grade', 'Chấm điểm'))+'</button><button class="btn btn-outline" id="hint-transform" style="border-color: #eab308; color: #ca8a04;">💡 Gợi ý</button></div><div class="hint-text-box" id="hint-text-transform" style="font-size: 13px; color: var(--text-secondary); margin-top: 10px; display: none; background: rgba(234, 179, 8, 0.05); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #eab308;"></div><div id="feedback"></div></div>';
    
    let hintLevel = 0;
    const hintBtn = document.querySelector('#hint-transform');
    if (hintBtn) {
      hintBtn.onclick = () => {
        const textEl = document.querySelector('#hint-text-transform');
        if (!textEl) return;
        textEl.style.display = 'block';
        hintLevel++;
        if (hintLevel === 1) {
          const firstWord = expectedText.split(' ')[0] || '';
          textEl.innerHTML = `⭐ <b>Gợi ý 1:</b> Từ bắt đầu tiên của đáp án là: <code style="font-size:14px; font-weight:700;">${firstWord}</code>`;
        } else if (hintLevel === 2) {
          const firstWord = expectedText.split(' ')[0] || '';
          textEl.innerHTML = `⭐ <b>Gợi ý 1:</b> Từ đầu tiên là: <code>${firstWord}</code><br>⭐ <b>Gợi ý 2:</b> Quy tắc ngữ pháp: <i>${q.grammar_rule || 'Không có'}</i>`;
        } else if (hintLevel === 3) {
          textEl.innerHTML = `⭐ <b>Đáp án là:</b> <code>${expectedText}</code> (Bạn đã xem đáp án nên câu này không tính điểm)`;
          document.querySelector('#answer').value = expectedText;
          if (!state.hintedQuestions) state.hintedQuestions = new Set();
          state.hintedQuestions.add(0);
          hintBtn.disabled = true;
          hintBtn.style.opacity = '0.5';
        }
      };
    }

    document.querySelector('#grade').onclick=async()=>{
      const signal = getSignal();
      try{
        setBusy(true, t('app.grading', 'Đang chấm điểm…'));
        
        const ansVal = document.querySelector('#answer').value;
        const userNorm = norm(ansVal);
        
        let isCorrect = userNorm === normExpected;
        
        if (!isCorrect && q.acceptable_variations) {
          q.acceptable_variations.forEach(v => {
            const vText = typeof v === 'object' ? v.text : v;
            if (norm(vText) === userNorm) {
              isCorrect = true;
            }
          });
        }

        let localFeedback = "";
        if (!isCorrect && q.common_errors) {
          q.common_errors.forEach(e => {
            const errText = typeof e === 'object' ? e.error : e;
            if (norm(errText) === userNorm) {
              localFeedback = typeof e === 'object' ? e.feedback : '';
            }
          });
        }

        let r;
        const wasHinted = state.hintedQuestions && state.hintedQuestions.has(0);
        if (isCorrect) {
          r = { correct: !wasHinted, score: wasHinted ? 0.0 : 10.0, explanation: wasHinted ? 'Bạn đã dùng gợi ý xem đáp án.' : 'Chính xác! Câu trả lời của bạn trùng khớp với đáp án chuẩn.' };
        } else {
          r=await Bridge.sendAsync('ai_grade',{
            gamemode:'sentence_transform',
            level:document.querySelector('#level').value,
            user_answer:ansVal,
            expected:expectedText,
            expected_answer:expectedText,
            instruction:instructionText,
            prompt:instructionText,
            original:originalText
          }, { signal });
        }

        if (signal.aborted) return;
        if (!r.correct && state.pairs && state.pairs[0]) {
          addWeakWord(state.pairs[0].term);
        }
        const fb=document.querySelector('#feedback');
        if(!fb)return;

        let html = '';
        if (r.correct) {
          html += '<div class="feedback good"><b>🎉 ' + esc(t('feedback.exact', 'Chính xác!')) + '</b>';
          html += `<p style="margin-top:10px;">• <b>Câu trả lời của bạn:</b> <span style="color:var(--success); font-weight:600;">${esc(ansVal)}</span></p>`;
          if (r.explanation) {
            html += `<p style="color:var(--text-secondary); font-size:13px; margin:4px 0;"><i>(${esc(r.explanation)})</i></p>`;
          }
        } else {
          html += '<div class="feedback bad"><b>❌ ' + esc(t('feedback.needs_improvement', 'Chưa chính xác rồi!')) + '</b>';
          html += `<p style="margin-top:10px;">• <b>Câu trả lời của bạn:</b> <span style="color:var(--error); font-weight:600;">${esc(ansVal)}</span></p>`;
          html += `<p>• <b>Đáp án chuẩn:</b> <span style="color:var(--success); font-weight:600;">${esc(expectedText)}</span></p>`;
          
          // Phân tích lỗi chi tiết 4 bước từ AI
          if (r.specific_error || r.why_wrong || r.how_to_fix || r.why_fix) {
            html += `<hr><p><b>🔍 Phân tích chi tiết lỗi sai:</b></p>
            <div class="error-item" style="margin-bottom:12px; padding:8px 12px; border-left:3px solid var(--error); background:rgba(239, 68, 68, 0.02); border-radius:4px;">
              <p style="margin:2px 0;">🔴 <b>Lỗi:</b> ${esc(r.specific_error || 'Lỗi cấu trúc/Từ vựng')}</p>
              <p style="margin:2px 0; padding-left:14px; font-size:13px;">❌ <b>Lỗi sai:</b> <span style="color:var(--error);">${esc(ansVal)}</span> ➔ <b>Vì sao sai:</b> <i>${esc(r.why_wrong || 'Chưa biến đổi đúng cấu trúc ngữ pháp yêu cầu')}</i></p>
              <p style="margin:2px 0; padding-left:14px; font-size:13px;">💡 <b>Cách sửa:</b> <span style="color:var(--success); font-weight:600;">${esc(r.how_to_fix || expectedText)}</span> ➔ <b>Vì sao sửa:</b> <i>${esc(r.why_fix || 'Đảm bảo đúng quy tắc biến đổi câu')}</i></p>
            </div>`;
          } else if (r.explanation || r.feedback) {
            html += `<p>${esc(r.explanation || r.feedback)}</p>`;
          }
        }

        const grammar = q.grammar_rule || r.grammar_rule;
        if (grammar) {
          html += '<hr><p><b>📌 Quy tắc ngữ pháp:</b> ' + esc(grammar) + '</p>';
        }

        const variations = q.acceptable_variations || r.acceptable_variations;
        if (variations && variations.length) {
          html += '<p>✅ <b>Các biến thể đúng khác:</b></p><ul>';
          variations.forEach(v => {
            const txt = typeof v === 'object' ? v.text : v;
            const note = typeof v === 'object' ? v.note : '';
            html += `<li>${esc(txt)} ${note ? `<i>(${esc(note)})</i>` : ''}</li>`;
          });
          html += '</ul>';
        }

        html+='<button class="btn" id="retry-trans">'+esc(t('app.retry', 'Làm lại'))+'</button></div>';
        fb.innerHTML=html;
        const retryBtn=document.querySelector('#retry-trans');
        if(retryBtn)retryBtn.onclick=()=>{state.answers={};play(state.route)}
      }catch(e){
        if(e.name==='AbortError'||e.error_code==='E_ABORTED')return;
        showBridgeFailure(e);
      }finally{
        if(!signal.aborted)setBusy(false)
      }
    }
  }

  /* ---- TABOO: batch rounds, concept → English, AI grade ---- */
  function renderTaboo(x){
    if (!x?.rounds?.length) { const d=document.querySelector('#play'); if(d)d.innerHTML='<div class="empty-state"><p>Không có dữ liệu bài tập.</p></div>'; return; }
    
    // Tự động sinh trật tự xáo trộn ban đầu nếu chưa có hoặc số lượng không khớp
    if (!state.tabooOrder || !state.tabooOrder.length || state.tabooOrder.length !== x.rounds.length) {
      state.tabooOrder = Array.from({ length: x.rounds.length }, (_, i) => i);
      for (let i = state.tabooOrder.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [state.tabooOrder[i], state.tabooOrder[j]] = [state.tabooOrder[j], state.tabooOrder[i]];
      }
      state.tabooCursor = 0;
    }

    const currentRoundIdx = state.tabooOrder[state.tabooCursor];
    const q = x.rounds[currentRoundIdx];
    const langLabel = state.userPrefs.language || 'en';
    const secretWord = q.target_word || '';
    const forbidden = q.taboo_words || [];
    const clueText = q.clue || '';
    
    document.querySelector('#play').innerHTML=`
      <div class="question-card taboo-card fade-in">
        <div style="font-size: 13.5px; color: var(--text-secondary); margin-bottom: 12px; font-weight:600;">Lượt chơi ${state.tabooCursor + 1} / ${x.rounds.length}</div>
        <div class="secret-word">???</div>
        <div class="forbidden">${forbidden.map(w=>'<span>🚫 '+esc(w)+'</span>').join('')}</div>
        <div class="description">${esc(clueText)}</div>
        <textarea id="answer" placeholder="${esc(t('placeholder.taboo', 'Nhập từ bạn đoán bằng {0}...', langLabel))}"></textarea>
        <div style="display:flex; gap:12px; margin-top:12px;">
          <button class="btn primary" id="grade">${esc(t('app.grade', 'Chấm điểm'))}</button>
          <button class="btn btn-outline" id="hint-taboo" style="border-color: #eab308; color: #ca8a04;">💡 Gợi ý</button>
        </div>
        <div class="hint-text-box" id="hint-text-taboo" style="font-size: 13px; color: var(--text-secondary); margin-top: 10px; display: none; background: rgba(234, 179, 8, 0.05); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #eab308;"></div>
        <div id="feedback"></div>
        
        <div class="taboo-guide-callout" style="margin-top: 24px; padding: 12px; background: rgba(0,0,0,0.02); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 13px; line-height: 1.4; color: var(--text-secondary);">
          💡 <b>HƯỚNG DẪN ĐOÁN TỪ (01 LẦN GỬI):</b>
          <ul style="margin: 4px 0 0 16px; padding: 0;">
            <li>Nhập nhiều từ hoặc cụm từ đoán cách nhau bằng dấu phẩy.</li>
            <li>Chỉ cần 1 trong các từ bạn nhập là đáp án đúng hoặc đồng nghĩa, bạn sẽ thắng.</li>
            <li>Ví dụ: <code>hobby, habit, custom, routine</code>.</li>
            <li><i>Chú ý: Tuyệt đối tránh sử dụng các từ cấm ở trên!</i></li>
          </ul>
        </div>
      </div>
    `;
    
    let hintLevel = 0;
    const hintBtn = document.querySelector('#hint-taboo');
    if (hintBtn) {
      hintBtn.onclick = () => {
        const textEl = document.querySelector('#hint-text-taboo');
        if (!textEl) return;
        textEl.style.display = 'block';
        hintLevel++;
        if (hintLevel === 1) {
          textEl.innerHTML = `⭐ <b>Gợi ý 1:</b> Từ này bắt đầu bằng chữ: <code style="font-size:14px; font-weight:700;">${secretWord.charAt(0).toUpperCase()}</code>`;
        } else if (hintLevel === 2) {
          textEl.innerHTML = `⭐ <b>Gợi ý 1:</b> Từ này bắt đầu bằng chữ: <code>${secretWord.charAt(0).toUpperCase()}</code><br>⭐ <b>Gợi ý 2:</b> Nghĩa tiếng Việt: <i>${q.meaning_vi || 'Không có'}</i>`;
        } else if (hintLevel === 3) {
          textEl.innerHTML = `⭐ <b>Đáp án là:</b> <code>${secretWord}</code> (Bạn đã xem đáp án nên câu này không tính điểm)`;
          document.querySelector('#answer').value = secretWord;
          if (!state.hintedQuestions) state.hintedQuestions = new Set();
          state.hintedQuestions.add(currentRoundIdx);
          hintBtn.disabled = true;
          hintBtn.style.opacity = '0.5';
        }
      };
    }

    document.querySelector('#grade').onclick=async()=>{
      const signal = getSignal();
      try{
        setBusy(true, t('app.grading', 'Đang chấm điểm…'));
        const guessInput = document.querySelector('#answer').value.trim();
        const guessList = guessInput.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
        const correctWord = secretWord.trim().toLowerCase();
        const localMatch = guessList.includes(correctWord);

        let r;
        if (localMatch) {
          const wasHinted = state.hintedQuestions && state.hintedQuestions.has(currentRoundIdx);
          r = {
            correct: !wasHinted,
            score: wasHinted ? 0.0 : 10.0,
            explanation: wasHinted ? 'Bạn đã dùng gợi ý xem đáp án.' : 'Chính xác! Bạn đã đoán đúng từ mục tiêu.',
            guess_feedback: guessList.map(g => ({
              guess: g,
              accepted: g === correctWord,
              reason_vi: g === correctWord ? (wasHinted ? 'Đoán đúng nhưng đã xem gợi ý đáp án.' : 'Chính xác! Trùng khớp hoàn toàn với đáp án mục tiêu.') : 'Không phải đáp án mục tiêu.'
            }))
          };
        } else {
          r=await Bridge.sendAsync('ai_grade',{
            gamemode:'taboo',
            level:document.querySelector('#level').value,
            user_answer:guessInput,
            target_word:secretWord,
            meaning_vi:q.meaning_vi || '',
            taboo_words:forbidden.join(', '),
            sample_acceptable_phrases:(q.sample_acceptable_phrases || []).join(', '),
            sample_forbidden_phrases:(q.sample_forbidden_phrases || []).join(', ')
          }, { signal });
        }

        if (signal.aborted) return;
        if (!r.correct) {
          addWeakWord(secretWord);
        }
        
        // Khóa input và nút submit sau khi chấm
        const ansInput = document.querySelector('#answer');
        const grdBtn = document.querySelector('#grade');
        if (ansInput) ansInput.disabled = true;
        if (grdBtn) grdBtn.disabled = true;
        if (hintBtn) {
          hintBtn.disabled = true;
          hintBtn.style.opacity = '0.5';
        }

        const fb=document.querySelector('#feedback');
        if(!fb)return;
        
        let html = '<div class="feedback '+(r.correct?'good':'bad')+'"><b>📊 KẾT QUẢ CHẤM ĐIỂM</b><hr>';
        html += `<p style="font-size: 15px;"><b>${r.correct ? '🎯 CHÍNH XÁC' : '❌ CHƯA CHÍNH XÁC'}</b></p>`;
        html += `<p>📥 <b>Danh sách từ bạn đã nhập:</b> ${guessList.map(g => `<code>${esc(g)}</code>`).join(', ') || 'Chưa nhập'}</p>`;
        html += `<p>🔑 <b>Đáp án đúng:</b> <span style="color:var(--success); font-weight:700;">${esc(secretWord.toUpperCase())}</span> ${q.phonetic ? `<code style="font-size:13.5px; color:var(--text-secondary); margin-left:6px;">${esc(q.phonetic)}</code>` : ''}</p>`;
        if (q.meaning_vi) {
          html += `<p>🇻🇳 <b>Dịch nghĩa:</b> ${esc(q.meaning_vi)}</p>`;
        }
        
        if (r.ai_analysis || r.explanation || r.feedback) {
          html += '<hr><p><b>💡 PHÂN TÍCH TỪ AI:</b></p>';
          if (r.word_definition) {
            html += `<p>• <b>Nghĩa gốc:</b> ${esc(r.word_definition)}</p>`;
          }
          html += `<p>• <b>Nhận xét:</b> ${esc(r.ai_analysis || r.explanation || r.feedback)}</p>`;
        }
        
        const feedbackList = r.guess_feedback || [];
        if (!feedbackList.length) {
          if (r.accepted_phrases && r.accepted_phrases.length) {
            r.accepted_phrases.forEach(item => feedbackList.push({ guess: item.phrase, accepted: true, reason_vi: item.explanation_vi }));
          }
          if (r.rejected_phrases && r.rejected_phrases.length) {
            r.rejected_phrases.forEach(item => feedbackList.push({ guess: item.phrase, accepted: false, reason_vi: item.reason_vi }));
          }
          if (!feedbackList.length) {
            guessList.forEach(g => {
              const isCorrect = g === correctWord;
              feedbackList.push({
                guess: g,
                accepted: isCorrect,
                reason_vi: isCorrect ? 'Khớp đáp án mục tiêu.' : (forbidden.includes(g.toUpperCase()) ? 'Vi phạm từ cấm!' : 'Không trùng khớp hoặc không phải từ đồng nghĩa.')
              });
            });
          }
        }

        const acceptedGuesses = feedbackList.filter(item => item.accepted);
        const rejectedGuesses = feedbackList.filter(item => !item.accepted);

        if (acceptedGuesses.length) {
          html += '<hr><p><b>✅ CÁC TỪ ĐƯỢC CHẤP NHẬN:</b></p><ul>';
          acceptedGuesses.forEach(item => {
            html += `<li><code>${esc(item.guess)}</code> ➔ <i>${esc(item.reason_vi)}</i></li>`;
          });
          html += '</ul>';
        }
        
        if (rejectedGuesses.length) {
          html += '<hr><p><b>❌ CÁC TỪ KHÔNG ĐƯỢC CHẤP NHẬN:</b></p><ul>';
          rejectedGuesses.forEach(item => {
            html += `<li><code>${esc(item.guess)}</code> ➔ <span style="color:var(--error);">${esc(item.reason_vi)}</span></li>`;
          });
          html += '</ul>';
        }

        const hasNext = state.tabooCursor < state.tabooOrder.length - 1;
        let btnHtml = '';
        if (hasNext) {
          btnHtml = `<button class="btn primary" id="next-taboo">➡️ Câu tiếp</button>`;
        } else {
          btnHtml = `<button class="btn primary" id="new-taboo-batch">⚡ Tạo bài mới</button>`;
        }
        btnHtml += ` <button class="btn btn-outline" id="retry-taboo-round" style="margin-left: 8px;">🔄 Làm lại câu này</button>`;

        html += `<div style="margin-top:16px;">${btnHtml}</div></div>`;
        fb.innerHTML=html;

        if (hasNext) {
          document.querySelector('#next-taboo').onclick = () => {
            state.tabooCursor++;
            renderTaboo(x);
          };
        } else {
          document.querySelector('#new-taboo-batch').onclick = () => {
            state.answers = {};
            generate(state.route);
          };
        }

        document.querySelector('#retry-taboo-round').onclick = () => {
          if (state.hintedQuestions) state.hintedQuestions.delete(currentRoundIdx);
          renderTaboo(x);
        };
      }catch(e){
        if(e.name==='AbortError'||e.error_code==='E_ABORTED')return;
        showBridgeFailure(e);
      }finally{
        if(!signal.aborted)setBusy(false)
      }
    }
  }

  /* ---- API KEY TESTER ---- */
  async function testKeys(){
    const button=document.querySelector('#test-keys'),out=document.querySelector('#api-result');
    const signal = getSignal();
    try{
      if(button)button.innerHTML='<span class="button-spinner"></span> ' + esc(t('app.testing_api', 'Đang kiểm tra…'));
      setBusy(true, t('app.testing_api_status', 'Đang kiểm tra API…'));
      const data=await Bridge.sendAsync('test_all_keys', {}, { signal });
      if (signal.aborted) return;
      const results=data.results||[],ok=results.filter(item=>item.ok).length;
      if (out) {
        let html = '<div class="api-tester-container" style="display:flex; flex-direction:column; gap:8px; width:100%; margin-top:12px; font-size:13px; text-align:left;">';
        results.forEach(item => {
          let statusIcon = item.ok ? '✅' : '❌';
          let statusText = item.ok ? t('app.api_ok', 'Hoạt động') : t('app.api_fail', 'Lỗi');
          
          if (!item.ok && item.error_code === 'E_RATE_LIMIT') {
            statusIcon = '⚠️';
            statusText = t('app.api_rate_limited', 'Bị giới hạn (Rate Limited)');
          }

          let details = '';
          if (item.ok && item.model) {
            details = ` - Model: <code>${esc(item.model)}</code>`;
          } else if (item.error) {
            details = ` - Lỗi: <span style="color:var(--error); font-weight:600;">${esc(item.error)}</span>`;
          }

          html += `
            <div class="api-key-row" style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; border:1px solid var(--border); border-radius:var(--radius-sm); background:var(--card-bg);">
              <div>
                <span style="font-weight:600;">${esc(t('app.key_label', 'Key {0}', item.key))}</span>${details}
              </div>
              <span class="api-key-status ${item.ok ? 'ok' : 'fail'}" style="font-weight:600;">
                ${statusIcon} ${statusText}
              </span>
            </div>
          `;
        });
        html += `
          <div style="margin-top:10px; font-weight:600; text-align:center; font-size:14px; width:100%;">
            ${esc(t('app.api_active_count', '{0}/{1} hoạt động', ok, results.length))}
          </div>
        </div>`;
        out.innerHTML = html;
      }
    }catch(e){
      if(e.name==='AbortError'||e.error_code==='E_ABORTED')return;
      showBridgeFailure(e);
    }finally{
      if(!signal.aborted){
        setBusy(false);
        if(button)button.innerHTML=esc(t('app.test_api', 'Kiểm tra API'))
      }
    }
  }

  function render(){state.route==='home'?home():game()}
  async function startApp(){
    const handleSave = () => { savePrefs(); };
    window.addEventListener('beforeunload', handleSave);
    window.addEventListener('pagehide', handleSave);

    if (window.Utils && typeof window.Utils.initI18n === 'function') {
      await window.Utils.initI18n();
    }

    try {
      const p = await Bridge.sendAsync('load_prefs');
      if (p && Object.keys(p).length) {
        Object.assign(state.userPrefs, p);
      }
    } catch (e) {
      console.warn("Failed to load prefs from Python:", e);
    }

    render();
  }
  if (!window.Bridge) window.Bridge = {};
  window.Bridge.updateStatus = function(text) {
    const el = document.querySelector('#loading-text');
    if (el) el.textContent = text;
  };
  return {start:startApp,navigate:nav,retry:()=>{state.answers={};play(state.route)}}
})();window.App=App;document.addEventListener('DOMContentLoaded',App.start);
