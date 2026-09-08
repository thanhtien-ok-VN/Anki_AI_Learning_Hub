/**
 * Source vocabulary & deck selection panel module.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  function source() {
    return `<section class="config-panel source-panel"><h3>${esc(t('source.title', 'Nguồn từ vựng Anki'))}</h3><label>${esc(t('source.search', 'Tìm deck'))} <input id="deck-search" placeholder="${esc(t('source.search_placeholder', 'Gõ một phần tên deck…'))}"></label><select id="deck" class="deck-list" size="7"></select><div class="selector-grid"><label>${esc(t('source.note_type', 'Note type'))}<select id="model"><option value="">${esc(t('source.select_deck_first', 'Chọn deck'))}</option></select></label><label>${esc(t('source.term', 'Thuật ngữ'))}<select id="term"><option value="">${esc(t('source.select_term_first', 'Chọn trường từ khóa'))}</option></select></label><label>${esc(t('source.definition', 'Định nghĩa'))}<select id="definition"><option value="">${esc(t('source.select_def_first', 'Chọn trường định nghĩa'))}</option></select></label></div><div class="config-row"><label>${esc(t('source.sample_count', 'Số từ mẫu'))} <input id="sample-limit" type="number" value="20" min="1" max="50"></label><button id="sample" class="btn btn-outline">${esc(t('source.get_samples', 'Lấy mẫu'))}</button><button id="reset-samples" class="btn btn-outline">${esc(t('source.reset_round', 'Làm mới vòng'))}</button></div><p id="source-status" class="source-status">${esc(t('source.status', 'Mẫu được chọn ngẫu nhiên, không lặp trong phiên Hub.'))}</p><details id="sample-preview"><summary>${esc(t('source.preview_empty', 'Chưa có mẫu để xem'))}</summary><ol id="sample-list"></ol></details></section>`;
  }

  function buildLanguageOptionsHtml() {
    const state = window.HubState || {};
    const uiLang = (typeof Utils !== 'undefined' && Utils.currentLang) || state.userPrefs?.ui_lang || 'en';
    const learnLang = state.userPrefs?.learn_lang || state.userPrefs?.language || 'en';
    const langs = state.supportedLanguages || [];
    return langs.map(lang => {
      const displayName = lang.names?.[uiLang] || lang.native || lang.code;
      const selected = lang.code === learnLang ? 'selected' : '';
      return `<option value="${lang.code}" ${selected}>${esc(displayName)}</option>`;
    }).join('');
  }

  function options(sel, items, label = x => x.name) {
    const e = document.querySelector(sel);
    if (!e) return;
    const defaultPlaceholder = t('app.select_placeholder', '-- Chọn --');
    e.innerHTML = '<option value="">' + esc(defaultPlaceholder) + '</option>' + items.map(x => '<option value="' + esc(x.id ?? x) + '">' + esc(label(x)) + '</option>').join('');
  }

  function drawDecks(q = '') {
    const state = window.HubState || {};
    const e = document.querySelector('#deck');
    if (!e) return;
    const items = (state.decks || []).filter(d => d.name.toLowerCase().includes(q.toLowerCase()));
    e.innerHTML = items.map(d => '<option value="' + d.id + '">' + '\u3000'.repeat(d.level) + esc(d.name) + '</option>').join('') || '<option value="">Không tìm thấy deck</option>';
  }

  async function loadModels() {
    const state = window.HubState || {};
    if (state.seen?.clear) state.seen.clear();
    state.pairs = [];
    const getSignal = window.getSignal || (() => null);
    const signal = getSignal();
    try {
      const deckVal = document.querySelector('#deck')?.value;
      if (!deckVal) return;
      options('#model', (await Bridge.sendAsync('get_source_models', { deck_id: +deckVal }, { signal })).models || []);
      options('#term', []);
      options('#definition', []);

      const p = state.userPrefs || {};
      const modelElem = document.querySelector('#model');
      if (p.model && modelElem && Array.from(modelElem.options).some(o => o.value == p.model)) {
        modelElem.value = p.model;
        await loadFields();
      }
    } catch (e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return;
      if (typeof window.showBridgeFailure === 'function') window.showBridgeFailure(e);
    }
  }

  async function loadFields() {
    const state = window.HubState || {};
    if (state.seen?.clear) state.seen.clear();
    state.pairs = [];
    const getSignal = window.getSignal || (() => null);
    const signal = getSignal();
    try {
      const modelVal = document.querySelector('#model')?.value;
      if (!modelVal) return;
      const f = (await Bridge.sendAsync('get_source_fields', { model_id: +modelVal }, { signal })).fields || [];
      options('#term', f, x => x);
      options('#definition', f, x => x);

      const p = state.userPrefs || {};
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
      if (typeof window.showBridgeFailure === 'function') window.showBridgeFailure(e);
    }
  }

  function request() {
    const state = window.HubState || {};
    const deck_id = +document.querySelector('#deck')?.value;
    const model_id = +document.querySelector('#model')?.value;
    const term_field = document.querySelector('#term')?.value;
    const definition_field = document.querySelector('#definition')?.value;
    if (!deck_id || !model_id || !term_field || !definition_field) throw Error(t('app.select_fields_first', 'Hãy chọn deck, note type và hai trường.'));
    const weakWords = typeof window.getWeakWords === 'function' ? window.getWeakWords() : [];
    return {
      deck_id,
      model_id,
      term_field,
      definition_field,
      limit: +document.querySelector('#sample-limit')?.value || 20,
      excluded_pair_keys: [...(state.seen || [])],
      weak_words: weakWords
    };
  }

  function preview() {
    const state = window.HubState || {};
    const d = document.querySelector('#sample-preview');
    if (!d) return;
    const pairs = state.pairs || [];
    d.querySelector('summary').textContent = pairs.length
      ? t('source.preview_count', 'Mẫu từ vựng ({0} từ)', pairs.length)
      : t('source.preview_empty', 'Chưa có mẫu để xem');
    d.querySelector('#sample-list').innerHTML = pairs.map(x => '<li><b>' + esc(x.term) + '</b> — ' + esc(x.definition) + '</li>').join('');
  }

  async function sample() {
    const state = window.HubState || {};
    const getSignal = window.getSignal || (() => null);
    const signal = getSignal();
    try {
      const data = await Bridge.sendAsync('sample_vocab_pairs', request(), { signal });
      if (data.exhausted) throw Error(t('app.round_exhausted', 'Đã dùng hết mẫu trong vòng này. Bấm Làm mới vòng.'));
      if (typeof window.clearStatus === 'function') window.clearStatus();
      state.pairs = data.pairs || [];
      state.pairs.forEach(x => {
        if (state.seen?.add) state.seen.add(x.key);
      });
      const srcStat = document.querySelector('#source-status');
      if (srcStat) srcStat.textContent = t('app.pairs_loaded', 'Đã lấy {0} cặp ngẫu nhiên.', data.total);
      preview();
      if (window.HubPersistence?.savePrefs) {
        window.HubPersistence.savePrefs(state);
      } else if (typeof window.savePrefs === 'function') {
        window.savePrefs();
      }
      return !!state.pairs.length;
    } catch (e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return false;
      if (typeof window.showBridgeFailure === 'function') window.showBridgeFailure(e);
      return false;
    }
  }

  async function bindSource() {
    const state = window.HubState || {};
    const getSignal = window.getSignal || (() => null);
    const signal = getSignal();
    try {
      state.decks = (await Bridge.sendAsync('list_decks', {}, { signal })).decks || [];
      drawDecks();

      const p = state.userPrefs || {};
      const deckElem = document.querySelector('#deck');
      if (p.deck && deckElem) {
        deckElem.value = p.deck;
        await loadModels();
      }
    } catch (e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return;
      if (typeof window.showBridgeFailure === 'function') window.showBridgeFailure(e);
    }

    const deckSearch = document.querySelector('#deck-search');
    if (deckSearch) deckSearch.oninput = e => drawDecks(e.target.value);

    const savePrefsFn = () => {
      if (window.HubPersistence?.savePrefs) window.HubPersistence.savePrefs(state);
      else if (typeof window.savePrefs === 'function') window.savePrefs();
    };
    const debouncedSavePrefsFn = () => {
      if (window.HubPersistence?.debouncedSavePrefs) window.HubPersistence.debouncedSavePrefs(state);
      else if (typeof window.debouncedSavePrefs === 'function') window.debouncedSavePrefs();
    };

    const deckEl = document.querySelector('#deck');
    if (deckEl) {
      deckEl.onchange = async () => {
        await loadModels();
        savePrefsFn();
      };
    }

    const modelEl = document.querySelector('#model');
    if (modelEl) {
      modelEl.onchange = async () => {
        await loadFields();
        savePrefsFn();
      };
    }

    const termEl = document.querySelector('#term');
    if (termEl) termEl.onchange = () => savePrefsFn();

    const defEl = document.querySelector('#definition');
    if (defEl) defEl.onchange = () => savePrefsFn();

    const slEl = document.querySelector('#sample-limit');
    if (slEl) slEl.oninput = () => debouncedSavePrefsFn();

    ['#level', '#count', '#num_blanks', '#focus'].forEach(sel => {
      const el = document.querySelector(sel);
      if (el) el.onchange = () => savePrefsFn();
    });

    const languageEl = document.querySelector('#language');
    if (languageEl) {
      languageEl.onchange = async () => {
        const result = await Bridge.sendAsync('set_learn_lang', { lang: languageEl.value });
        const learnLang = result && result.learn_lang ? result.learn_lang : languageEl.value;
        if (state.userPrefs) {
          state.userPrefs.learn_lang = learnLang;
          state.userPrefs.language = learnLang;
        }
        savePrefsFn();
      };
    }

    const topicEl = document.querySelector('#topic');
    if (topicEl) topicEl.oninput = () => debouncedSavePrefsFn();

    const sampleBtn = document.querySelector('#sample');
    if (sampleBtn) sampleBtn.onclick = sample;

    const resetBtn = document.querySelector('#reset-samples');
    if (resetBtn) {
      resetBtn.onclick = () => {
        if (state.seen?.clear) state.seen.clear();
        state.pairs = [];
        savePrefsFn();
        preview();
      };
    }
  }

  window.HubSource = {
    source,
    buildLanguageOptionsHtml,
    options,
    drawDecks,
    loadModels,
    loadFields,
    request,
    preview,
    sample,
    bindSource
  };

  window.source = source;
  window.buildLanguageOptionsHtml = buildLanguageOptionsHtml;
  window.loadModels = loadModels;
  window.loadFields = loadFields;
  window.drawDecks = drawDecks;
  window.options = options;
  window.preview = preview;
  window.sample = sample;
  window.bindSource = bindSource;
})();
