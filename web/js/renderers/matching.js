/**
 * Matching (Word Matching Board Engine) game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  const shuffleArray = arr => {
    if (typeof window.shuffleArray === 'function') return window.shuffleArray(arr);
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = a[i];
      a[i] = a[j];
      a[j] = tmp;
    }
    return a;
  };

  function renderMatching(x) {
    const d = document.querySelector('#play');
    if (!x || !x.pairs || !x.pairs.length) {
      if (d) d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu từ vựng để nối.</p></div>';
      return;
    }

    const state = window.HubState || {};
    const setSafeTimeout = window.setSafeTimeout || setTimeout;
    const setSafeInterval = window.setSafeInterval || setInterval;
    const clearSafeInterval = window.clearSafeInterval || clearInterval;

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

    // Audio synthesizer with shared AudioContext and node cleanup
    function playSound(type) {
      try {
        const getCtx = window.getSharedAudioContext;
        const ctx = getCtx ? getCtx() : null;
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.onended = () => {
          try {
            osc.disconnect();
            gain.disconnect();
          } catch (_) {}
        };

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

    function getHalfCompletePairs() {
      const activeWordIds = new Set(activeWords.filter(Boolean).map(s => s.pairId));
      const activeMeaningIds = new Set(activeMeanings.filter(Boolean).map(s => s.pairId));

      const halfWords = []; // word is on screen, meaning is not
      const halfMeanings = []; // meaning is on screen, word is not

      pairs.forEach(p => {
        if (matchedPairIds.has(p.id)) return;
        const wOn = activeWordIds.has(p.id);
        const mOn = activeMeaningIds.has(p.id);
        if (wOn && !mOn) {
          halfWords.push(p);
        } else if (mOn && !wOn) {
          halfMeanings.push(p);
        }
      });
      return { halfWords, halfMeanings };
    }

    // Initialize the 5-slot screen
    function initBoard() {
      matchedPairIds.clear();
      activeWords = new Array(SLOT_COUNT).fill(null);
      activeMeanings = new Array(SLOT_COUNT).fill(null);

      // Balanced board invariant: If pairs.length <= 5, place all pairs so both sides are balanced.
      const G = pairs.length <= 5 ? pairs.length : 4;
      const shuffledPairs = shuffleArray(pairs);
      const guaranteed = shuffledPairs.slice(0, G);

      const leftIndices = shuffleArray([0, 1, 2, 3, 4]);
      const rightIndices = shuffleArray([0, 1, 2, 3, 4]);

      for (let i = 0; i < G; i++) {
        const p = guaranteed[i];
        activeWords[leftIndices[i]] = { pairId: p.id, word: p.word };
        activeMeanings[rightIndices[i]] = { pairId: p.id, meaning: p.meaning };
      }

      // Collect empty slots
      const emptyLefts = [];
      const emptyRights = [];
      for (let i = 0; i < SLOT_COUNT; i++) {
        if (!activeWords[i]) emptyLefts.push(i);
        if (!activeMeanings[i]) emptyRights.push(i);
      }

      // Fill remaining empty slots with disjoint half-pairs from the pool
      const pool = shuffledPairs.slice(G);
      const shuffledPool = shuffleArray(pool);

      // Place words on left
      for (let i = 0; i < emptyLefts.length; i++) {
        if (i < shuffledPool.length) {
          const p = shuffledPool[i];
          activeWords[emptyLefts[i]] = { pairId: p.id, word: p.word };
        }
      }

      // Place meanings on right, offset by emptyLefts.length to ensure disjointness
      for (let i = 0; i < emptyRights.length; i++) {
        const poolIdx = i + emptyLefts.length;
        if (poolIdx < shuffledPool.length) {
          const p = shuffledPool[poolIdx];
          activeMeanings[emptyRights[i]] = { pairId: p.id, meaning: p.meaning };
        }
      }
    }

    // Refill slots after a successful match
    function refillSlots(emptyLeftIdx, emptyRightIdx) {
      const { halfWords, halfMeanings } = getHalfCompletePairs();

      const shufHalfWords = shuffleArray(halfWords);
      const shufHalfMeanings = shuffleArray(halfMeanings);

      if (shufHalfWords.length > 0) {
        const C = shufHalfWords[0];
        const unplaced = shuffleArray(getFullyUnplacedPairs());
        if (unplaced.length > 0) {
          const D = unplaced[0];
          activeWords[emptyLeftIdx] = { pairId: D.id, word: D.word };
          activeMeanings[emptyRightIdx] = { pairId: C.id, meaning: C.meaning };
          return;
        }
      }

      if (shufHalfMeanings.length > 0) {
        const C = shufHalfMeanings[0];
        const unplaced = shuffleArray(getFullyUnplacedPairs());
        if (unplaced.length > 0) {
          const D = unplaced[0];
          activeWords[emptyLeftIdx] = { pairId: C.id, word: C.word };
          activeMeanings[emptyRightIdx] = { pairId: D.id, meaning: D.meaning };
          return;
        }
      }

      if (shufHalfWords.length > 0 && shufHalfMeanings.length > 0) {
        const A = shufHalfWords[0];
        const B = shufHalfMeanings[0];
        if (A.id !== B.id) {
          activeWords[emptyLeftIdx] = { pairId: B.id, word: B.word };
          activeMeanings[emptyRightIdx] = { pairId: A.id, meaning: A.meaning };
          return;
        }
      }

      const unplaced = shuffleArray(getFullyUnplacedPairs());
      if (unplaced.length >= 2) {
        const C = unplaced[0];
        const D = unplaced[1];
        activeWords[emptyLeftIdx] = { pairId: C.id, word: C.word };
        activeMeanings[emptyRightIdx] = { pairId: D.id, meaning: D.meaning };
        return;
      }

      const availWords = shuffleArray(getUnplacedWordPairs());
      let leftPairId = null;
      if (availWords.length > 0) {
        const p = availWords[0];
        leftPairId = p.id;
        activeWords[emptyLeftIdx] = { pairId: p.id, word: p.word };
      }

      let availMeanings = getUnplacedMeaningPairs();
      if (leftPairId) {
        availMeanings = availMeanings.filter(m => m.id !== leftPairId);
      }
      if (availMeanings.length === 0) {
        availMeanings = getUnplacedMeaningPairs();
      }
      availMeanings = shuffleArray(availMeanings);
      if (availMeanings.length > 0) {
        const p = availMeanings[0];
        activeMeanings[emptyRightIdx] = { pairId: p.id, meaning: p.meaning };
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

    function updateCardSelections() {
      d.querySelectorAll('.match-card[data-col="left"]').forEach(btn => {
        const idx = +btn.dataset.idx;
        btn.classList.toggle('selected', selectedWordIdx === idx);
      });
      d.querySelectorAll('.match-card[data-col="right"]').forEach(btn => {
        const idx = +btn.dataset.idx;
        btn.classList.toggle('selected', selectedMeaningIdx === idx);
      });
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

      updateCardSelections();

      if (selectedWordIdx !== null && selectedMeaningIdx !== null) {
        evaluateMatch();
      }
    }

    function finishGame() {
      if (isFinished) return;
      isFinished = true;
      if (timerInterval) clearSafeInterval(timerInterval);

      const elapsedSec = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      const mins = Math.floor(elapsedSec / 60);
      const secs = elapsedSec % 60;
      const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      const accuracy = totalAttempts > 0 ? Math.round((matchedCount / totalAttempts) * 100) : (matchedCount > 0 ? 100 : 0);

      if (window.HubPersistence && window.HubPersistence.loadMatchingStats) {
        if (!state.matchingStats) window.HubPersistence.loadMatchingStats(state);
      }
      const stats = state.matchingStats || { aggregates: {}, records: [] };
      const record = {
        time: Date.now(),
        pairs: totalPairsCount,
        matched: matchedCount,
        wrong: wrongCount,
        attempts: totalAttempts,
        elapsed_sec: elapsedSec,
        accuracy: accuracy
      };

      if (!stats.records) stats.records = [];
      stats.records.unshift(record);
      if (stats.records.length > 30) stats.records.length = 30;

      if (!stats.aggregates) {
        stats.aggregates = { total_games: 0, total_correct: 0, total_wrong: 0, avg_accuracy: 0, avg_time_sec: 0, best_time_sec: 999999 };
      }
      stats.aggregates.total_games = (stats.aggregates.total_games || 0) + 1;
      stats.aggregates.total_correct = (stats.aggregates.total_correct || 0) + matchedCount;
      stats.aggregates.total_wrong = (stats.aggregates.total_wrong || 0) + wrongCount;

      const totalAccSum = stats.records.reduce((sum, r) => sum + r.accuracy, 0);
      stats.aggregates.avg_accuracy = Math.round(totalAccSum / stats.records.length);

      const totalTimeSum = stats.records.reduce((sum, r) => sum + r.elapsed_sec, 0);
      stats.aggregates.avg_time_sec = Math.round(totalTimeSum / stats.records.length);

      if (accuracy === 100 && elapsedSec < (stats.aggregates.best_time_sec ?? 999999)) {
        stats.aggregates.best_time_sec = elapsedSec;
      }

      if (window.HubPersistence && window.HubPersistence.saveMatchingStats) {
        window.HubPersistence.saveMatchingStats(state);
      }

      const bestTimeStr = stats.aggregates.best_time_sec !== 999999 ?
        `${Math.floor(stats.aggregates.best_time_sec / 60)}m ${stats.aggregates.best_time_sec % 60}s` : 'N/A';

      const statsSummaryHtml = `
        <div class="stats-summary-box" style="margin-top: 20px; padding: 12px; border-top: 1px dashed var(--border); font-size: 13px; color: var(--text-secondary);">
          ${t('matching.accumulated_stats', '🏆 Thống kê tích lũy:')} <b>${t('matching.played_games', 'Đã chơi: {0} bài', stats.aggregates.total_games)}</b> · <b>${t('matching.avg_accuracy_label', 'Độ chính xác TB: {0}%', stats.aggregates.avg_accuracy)}</b> · <b>${t('matching.fastest_label', 'Nhanh nhất (100% đúng): {0}', bestTimeStr)}</b>
        </div>
      `;

      d.innerHTML = `
        <div class="feedback good" style="text-align:center; padding: 24px;">
          <h2 style="margin-bottom:12px; color: var(--success);">${t('matching.complete', '🎉 Ghép đôi hoàn thành!')}</h2>
          <div style="font-size:16px; margin-bottom:20px; line-height:1.6;">
            <p>⏱️ ${t('matching.time_label', 'Thời gian')}: <b>${timeStr}</b></p>
            <p>🎯 ${t('matching.matched_count', 'Ghép đúng')}: <b>${matchedCount}/${totalPairsCount}</b></p>
            <p>❌ ${t('matching.wrong_count', 'Số lần ghép sai')}: <b>${wrongCount}</b></p>
            <p>📊 ${t('matching.accuracy', 'Độ chính xác')}: <b>${accuracy}%</b></p>
          </div>
          ${statsSummaryHtml}
          <div class="flex justify-center flex-wrap gap-3 mt-5">
            <button class="btn primary" id="restart-matching-btn" style="padding: 10px 24px;">${t('matching.play_again', '🔄 Chơi lại bài này')}</button>
            <button class="btn btn-outline" id="new-matching-btn" style="padding: 10px 24px;">${t('matching.new_game', '⚡ Tạo bài nối mới')}</button>
          </div>
        </div>
      `;

      if (typeof window.resetGameState === 'function') {
        window.resetGameState('matching');
      }
      const restartBtn = d.querySelector('#restart-matching-btn');
      if (restartBtn) restartBtn.onclick = () => renderMatching(x);
      const newBtn = d.querySelector('#new-matching-btn');
      if (newBtn) newBtn.onclick = () => { if (typeof window.nav === 'function') window.nav('home'); };
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
              <span class="matching-stat-badge">🎯 <span style="color:var(--primary);">${matchedCount}/${totalPairsCount}</span></span>
              <span class="matching-stat-badge">❌ <span style="color:${wrongCount > 0 ? 'var(--error)' : 'inherit'};">${wrongCount}</span></span>
              <span class="matching-stat-badge">📊 <span style="color:${accuracy >= 80 ? 'var(--success)' : 'var(--primary)'};">${accuracy}%</span></span>
            </div>
            <button class="btn btn-outline" id="finish-matching-btn" style="padding:6px 14px; font-size:13px; color:var(--error); border-color:var(--error);">
              ${t('matching.finish_btn', '🏁 Kết thúc')}
            </button>
          </div>

          <div class="match-board">
            <div class="match-col">
              <div class="match-col-header">${t('matching.terms_col', 'Từ vựng')}</div>
              ${leftSlotsHtml}
            </div>
            <div class="match-col">
              <div class="match-col-header">${t('matching.defs_col', 'Nghĩa')}</div>
              ${rightSlotsHtml}
            </div>
          </div>
        </div>
      `;

      // Event delegation on .match-board instead of attaching handlers to each card
      const boardEl = d.querySelector('.match-board');
      if (boardEl) {
        boardEl.onclick = e => {
          const btn = e.target.closest('.match-card');
          if (btn && btn.dataset.col && btn.dataset.idx !== undefined) {
            handleCardClick(btn.dataset.col, +btn.dataset.idx);
          }
        };
      }

      const finishBtn = d.querySelector('#finish-matching-btn');
      if (finishBtn) {
        finishBtn.onclick = () => finishGame();
      }
    }

    initBoard();

    if (timerInterval) clearSafeInterval(timerInterval);
    timerInterval = setSafeInterval(() => {
      if (isFinished) {
        clearSafeInterval(timerInterval);
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

  window.renderMatching = renderMatching;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('matching', { render: renderMatching });
  }
})();
