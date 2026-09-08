/**
 * Persistence & LocalStorage Manager for Anki AI Learning Hub.
 */
window.HubPersistence = (() => {
  const PFX = 'aihub_';
  let _savePrefsTimer = null;

  function loadPrefs(state) {
    try {
      const p = localStorage.getItem(PFX + 'prefs');
      if (p) Object.assign(state.userPrefs, JSON.parse(p));
    } catch (e) {}

    // Restore ui_lang
    try {
      const savedUiLang = localStorage.getItem('ai_learning_hub_prefs_ui_lang');
      if (savedUiLang && typeof Utils !== 'undefined') {
        Utils.currentLang = savedUiLang;
      }
    } catch (e) {}
  }

  function loadMatchingStats(state) {
    const defaultStats = {
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
    try {
      const stats = localStorage.getItem(PFX + 'matching_stats');
      state.matchingStats = stats ? JSON.parse(stats) : defaultStats;
    } catch (e) {
      state.matchingStats = defaultStats;
    }
  }

  function saveMatchingStats(state) {
    try {
      if (state.matchingStats) {
        localStorage.setItem(PFX + 'matching_stats', JSON.stringify(state.matchingStats));
      }
    } catch (e) {}
  }

  function loadHistory(state) {
    try {
      const h = localStorage.getItem(PFX + 'history');
      if (h) {
        state.history = JSON.parse(h) || {};
        delete state.history['matching'];
      }
      loadMatchingStats(state);
    } catch (e) {}
  }

  function saveHistory(state) {
    try {
      if (state.history) {
        delete state.history['matching'];
        localStorage.setItem(PFX + 'history', JSON.stringify(state.history));
      }
    } catch (e) {
      try {
        if (state.history) {
          Object.keys(state.history).forEach(k => {
            if (Array.isArray(state.history[k]) && state.history[k].length > 10) {
              state.history[k] = state.history[k].slice(0, 10);
            }
          });
          localStorage.setItem(PFX + 'history', JSON.stringify(state.history));
        }
      } catch (_) {}
    }
  }

  function savePrefs(state) {
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
    if (lg) {
      p.language = lg.value;
      p.learn_lang = lg.value;
    }
    if (nb) p.num_blanks = nb.value;
    if (fs) p.focus = fs.value;
    if (sl) p.sample_limit = sl.value;
    p.pairs = state.pairs || [];
    p.seen = Array.from(state.seen || []);

    state.userPrefs = p;
    try {
      localStorage.setItem(PFX + 'prefs', JSON.stringify(p));
    } catch (e) {}

    if (typeof Bridge !== 'undefined' && Bridge.send) {
      Bridge.send('save_prefs', p);
    }
  }

  function debouncedSavePrefs(state, delayMs = 300) {
    if (_savePrefsTimer) clearTimeout(_savePrefsTimer);
    _savePrefsTimer = setTimeout(() => {
      _savePrefsTimer = null;
      savePrefs(state);
    }, delayMs);
  }

  function flushSavePrefs(state) {
    if (_savePrefsTimer) {
      clearTimeout(_savePrefsTimer);
      _savePrefsTimer = null;
      savePrefs(state);
    }
  }

  function restorePrefs(state, onPreview) {
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
    if (lg && (p.learn_lang || p.language)) lg.value = p.learn_lang || p.language;
    const nb = document.querySelector('#num_blanks');
    if (nb && p.num_blanks) nb.value = p.num_blanks;
    const fs = document.querySelector('#focus');
    if (fs && p.focus) fs.value = p.focus;

    if (p.pairs && Array.isArray(p.pairs) && p.pairs.length) {
      state.pairs = p.pairs;
      if (p.seen && Array.isArray(p.seen)) {
        state.seen = new Set(p.seen);
      }
      if (typeof onPreview === 'function') onPreview();
    }
  }

  function clearPrefs(state) {
    state.userPrefs = {};
    state.pairs = [];
    if (state.seen && state.seen.clear) state.seen.clear();
    try {
      localStorage.removeItem(PFX + 'prefs');
    } catch (e) {}
  }

  function getWeakWords() {
    try {
      const data = localStorage.getItem('ai_learning_hub_weak_words');
      return data ? JSON.parse(data) : [];
    } catch (_) {}
    return [];
  }

  function addWeakWord(word) {
    try {
      if (!word) return;
      const list = getWeakWords();
      if (!list.includes(word)) {
        list.push(word);
        if (list.length > 100) list.shift();
        localStorage.setItem('ai_learning_hub_weak_words', JSON.stringify(list));
      }
    } catch (_) {}
  }

  return {
    loadPrefs,
    loadMatchingStats,
    saveMatchingStats,
    loadHistory,
    saveHistory,
    savePrefs,
    debouncedSavePrefs,
    flushSavePrefs,
    restorePrefs,
    clearPrefs,
    getWeakWords,
    addWeakWord
  };
})();

if (typeof window !== 'undefined' && window.HubPersistence) {
  window.getWeakWords = window.HubPersistence.getWeakWords;
  window.addWeakWord = window.HubPersistence.addWeakWord;
}
