/**
 * Manifest Client & Dynamic Form Generator.
 * Consumes GameModeManifests from backend to dynamically generate Hub cards and Config panels.
 */
window.ManifestClient = (() => {
  let manifests = [
    { id: 'fill_blank', icon: '✍️', title_key: 'fill_blank.title', default_title: 'Fill in the Blank', desc_key: 'fill_blank.desc', default_desc: 'Choose the correct word to complete the sentence', min_items: 1, max_items: 10, default_items: 5, requires_anki_cards: false, custom_controls: [] },
    { id: 'cloze', icon: '📖', title_key: 'cloze.title', default_title: 'Cloze', desc_key: 'cloze.desc', default_desc: 'Fill in the missing words in the passage', min_items: 1, max_items: 1, default_items: 1, requires_anki_cards: false, custom_controls: [
      { id: 'num_blanks', type: 'select', label_key: 'controls.num_blanks', default_label: 'Số blank', default_value: 5, options: [5,6,7,8,9,10].map(v => ({ value: v, label: String(v) })) }
    ]},
    { id: 'translation', icon: '🌐', title_key: 'translation.title', default_title: 'Translation', desc_key: 'translation.desc', default_desc: 'Translate sentences and get AI grading', min_items: 1, max_items: 1, default_items: 1, requires_anki_cards: false, custom_controls: [] },
    { id: 'unscramble', icon: '🧩', title_key: 'unscramble.title', default_title: 'Word Unscramble', desc_key: 'unscramble.desc', default_desc: 'Arrange scrambled words into correct sentences', min_items: 1, max_items: 10, default_items: 5, requires_anki_cards: false, custom_controls: [] },
    { id: 'matching', icon: '🔗', title_key: 'matching.title', default_title: 'Word Matching', desc_key: 'matching.desc', default_desc: 'Match vocabulary terms with their definitions (Offline)', min_items: 5, max_items: 50, default_items: 10, requires_anki_cards: true, custom_controls: [] },
    { id: 'story', icon: '📚', title_key: 'story.title', default_title: 'Story', desc_key: 'story.desc', default_desc: 'Read AI-generated stories and answer comprehension questions', min_items: 3, max_items: 10, default_items: 5, requires_anki_cards: false, custom_controls: [] },
    { id: 'sentence_transform', icon: '🔄', title_key: 'sentence_transform.title', default_title: 'Sentence Transform', desc_key: 'sentence_transform.desc', default_desc: 'Rewrite sentences according to grammatical rules', min_items: 1, max_items: 1, default_items: 1, requires_anki_cards: false, custom_controls: [
      { id: 'focus', type: 'select', label_key: 'controls.form_type', default_label: 'Dạng', default_value: 'voice', options: [
        { value: 'voice', label: 'Voice (Câu bị động)' },
        { value: 'conditional', label: 'Conditional (Câu điều kiện)' },
        { value: 'reported', label: 'Reported (Câu tường thuật)' },
        { value: 'comparative', label: 'Comparative (So sánh)' }
      ]}
    ]},
    { id: 'taboo', icon: '🚫', title_key: 'taboo.title', default_title: 'Taboo', desc_key: 'taboo.desc', default_desc: 'Guess the secret word without using forbidden taboo words', min_items: 1, max_items: 10, default_items: 5, requires_anki_cards: false, custom_controls: [] }
  ];

  async function loadManifests() {
    if (typeof window.Bridge !== 'undefined' && window.Bridge.sendAsync) {
      try {
        const res = await window.Bridge.sendAsync('get_gamemodes', {});
        if (res && res.data && Array.isArray(res.data.gamemodes) && res.data.gamemodes.length > 0) {
          manifests = res.data.gamemodes;
        }
      } catch (e) {
        console.warn('Could not load manifests from backend, using default fallback', e);
      }
    }
    return manifests;
  }

  function getManifest(id) {
    return manifests.find(m => m.id === id) || {
      id, icon: '🎮', title_key: id + '.title', default_title: id,
      desc_key: id + '.desc', default_desc: '', min_items: 1, max_items: 10, default_items: 5,
      requires_anki_cards: false, custom_controls: []
    };
  }

  function getAllManifests() {
    return manifests;
  }

  function renderControlsHtml(id, helpers) {
    const m = getManifest(id);
    const esc = helpers.esc || (s => s);
    const t = helpers.t || ((k, d) => d || k);
    const buildLanguageOptionsHtml = helpers.buildLanguageOptionsHtml || (() => '<option value="en">English</option>');

    let extraHtml = '';
    if (m.custom_controls && m.custom_controls.length > 0) {
      m.custom_controls.forEach(ctrl => {
        if (ctrl.type === 'select' && ctrl.options) {
          const opts = ctrl.options.map(opt => {
            const val = typeof opt === 'object' ? opt.value : opt;
            const label = typeof opt === 'object' ? (opt.label || opt.value) : opt;
            const selected = String(val) === String(ctrl.default_value) ? 'selected' : '';
            return `<option value="${esc(val)}" ${selected}>${esc(label)}</option>`;
          }).join('');
          extraHtml += `<label>${esc(t(ctrl.label_key, ctrl.default_label))}<select id="${esc(ctrl.id)}">${opts}</select></label>`;
        }
      });
    }

    const min = m.min_items || 1;
    const max = m.max_items || 10;
    const hideCount = (min === max && min === 1);
    const countLabel = m.requires_anki_cards ? t('controls.pair_count', 'Số cặp từ') : t('controls.question_count', 'Số câu');

    let countSelect = '';
    if (!hideCount) {
      const opts = Array.from({ length: max - min + 1 }, (_, i) => {
        const val = i + min;
        const selected = (val === 10 || (max < 10 && val === min)) ? 'selected' : '';
        return `<option ${selected}>${val}</option>`;
      }).join('');
      countSelect = `<label>${esc(countLabel)}<select id="count">${opts}</select></label>`;
    }

    if (m.requires_anki_cards) {
      return `<section class="config-panel"><div class="selector-grid">${countSelect}</div><div class="flex items-center flex-wrap gap-3 mt-3"><button class="btn primary" id="generate">${esc(t('controls.generate', 'Tạo bài'))}</button></div></section>`;
    }

    return `<section class="config-panel"><div class="selector-grid"><label>${esc(t('app.language', 'Ngôn ngữ học'))}<select id="language">${buildLanguageOptionsHtml()}</select></label><label>${esc(t('app.level', 'Trình độ'))}<select id="level"><option value="beginner">${esc(t('controls.level_beginner', 'A1 - Sơ cấp (Beginner)'))}</option><option value="elementary">${esc(t('controls.level_elementary', 'A2 - Sơ trung cấp (Elementary)'))}</option><option value="intermediate" selected>${esc(t('controls.level_intermediate', 'B1 - Trung cấp (Intermediate)'))}</option><option value="upper_intermediate">${esc(t('controls.level_upper_intermediate', 'B2 - Trung cấp nâng cao (Upper-intermediate)'))}</option><option value="advanced">${esc(t('controls.level_advanced', 'C1–C2 - Nâng cao (Advanced)'))}</option></select></label>${countSelect}${extraHtml}<label>${esc(t('app.topic', 'Chủ đề'))}<input id="topic" placeholder="${esc(t('app.topic_placeholder', 'Nhập mô tả chủ đề (VD: daily_life)'))}" value="daily_life"></label></div><div class="flex items-center flex-wrap gap-3 mt-3"><button class="btn primary" id="generate">${esc(t('controls.generate', 'Tạo bài'))}</button></div></section>`;
  }

  return {
    loadManifests,
    getManifest,
    getAllManifests,
    renderControlsHtml,
  };
})();
