/**
 * Shared UI helpers and components for game renderers.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  function formatSentenceWithBlank(sentenceText, chosenWord, isGraded, isCorrect, correctWord) {
    if (!sentenceText) return '';
    const pattern = /______+|___+|\[BLANK\]|\(\.\.\.\)|____+/gi;
    const hasMatch = pattern.test(sentenceText);

    let replacement = '';
    if (isGraded) {
      if (isCorrect) {
        replacement = `<span class="blank-pill correct" style="display:inline-flex; align-items:center; gap:4px; padding:2px 10px; border-radius:12px; background:rgba(34,197,94,0.15); color:#16a34a; font-weight:700;">✓ ${esc(correctWord || chosenWord)}</span>`;
      } else {
        const wrongText = chosenWord ? `<span style="text-decoration:line-through; opacity:0.8;">${esc(chosenWord)}</span> ` : '';
        replacement = `<span class="blank-pill wrong" style="display:inline-flex; align-items:center; gap:4px; padding:2px 10px; border-radius:12px; background:rgba(239,68,68,0.15); color:#dc2626; font-weight:700;">${wrongText}✓ ${esc(correctWord)}</span>`;
      }
    } else if (chosenWord) {
      replacement = `<span class="blank-pill active" style="display:inline-block; padding:2px 10px; border-radius:12px; background:rgba(59,130,246,0.15); color:#2563eb; font-weight:700; border:1px solid rgba(59,130,246,0.3);">${esc(chosenWord)}</span>`;
    } else {
      replacement = `<span class="blank-pill empty" style="display:inline-block; padding:2px 14px; border-radius:12px; background:var(--color-surface-tint); color:var(--text-secondary); font-weight:700; border:1.5px dashed var(--color-warn);">______</span>`;
    }

    if (hasMatch) {
      pattern.lastIndex = 0;
      return sentenceText.replace(pattern, replacement);
    }
    return `${sentenceText} ${replacement}`;
  }

  function buildOptionDetailsHtml(q, chosen) {
    const optTrans = q.options_translations || [];
    const details = q.options_details || [];

    const items = q.options.map((opt, idx) => {
      let word = typeof opt === 'object' ? opt.word : opt;
      let isAns = typeof opt === 'object' ? opt.is_correct : (idx === q.correct_index);
      let reason = typeof opt === 'object' ? opt.reason : (details[idx]?.reason || (isAns ? (q.explanation_short || t('feedback.correct_context_fallback', 'Từ phù hợp ngữ cảnh câu.')) : t('feedback.distractor_fallback', 'Phương án gây nhiễu.')));
      let tr = typeof opt === 'object' ? '' : (details[idx]?.translation || optTrans[idx] || '');

      const isUserChoice = idx === chosen;
      const letter = String.fromCharCode(65 + idx);

      let badgeBg = isAns ? 'var(--color-success-bg)' : (isUserChoice ? 'var(--color-error-bg)' : 'var(--bg)');
      let badgeColor = isAns ? 'var(--success)' : (isUserChoice ? 'var(--error)' : 'var(--text-secondary)');
      let badgeLabel = isAns ? t('feedback.badge_correct', '✓ Đáp án đúng') : (isUserChoice ? t('feedback.badge_chosen', '✕ Bạn chọn') : t('feedback.badge_distractor', 'Từ gây nhiễu'));
      let borderColor = isAns ? 'var(--success)' : (isUserChoice ? 'var(--error)' : 'var(--border)');

      return `
        <div style="padding:10px 12px; border-left:4px solid ${borderColor}; background:var(--bg); border-radius:4px; margin-bottom:8px; text-align:left;">
          <div class="flex-row-between--wrap gap-2 mb-1">
            <span class="text-base"><b>${letter}. ${esc(word)}</b> ${tr ? `<span style="color:var(--text-secondary); font-size:13px;">— ${esc(tr)}</span>` : ''}</span>
            <span style="font-size:11px; padding:2px 8px; border-radius:10px; font-weight:600; background:${badgeBg}; color:${badgeColor}; border:1px solid ${borderColor};">${esc(badgeLabel)}</span>
          </div>
          <div style="font-size:13px; color:var(--text); line-height:1.4;">
            <b>${esc(t('feedback.reason_label_short', 'Lý do'))}:</b> ${esc(reason)}
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="mt-3 text-left">
        <b class="text-base">📊 ${esc(t('feedback.options_analysis_title', 'Phân tích chi tiết các lựa chọn'))}:</b>
        <div class="mt-2">
          ${items}
        </div>
      </div>
    `;
  }

  function renderExplanationBox(text, title) {
    if (!text || typeof text !== 'string') return '';
    const trimmed = text.trim();
    if (!trimmed || trimmed === 'null' || trimmed === 'undefined') return '';
    const displayTitle = title || t('app.explanation_title', '💡 Giải thích từ AI');
    return `<div class="explanation-card"><h4>${esc(displayTitle)}</h4><div class="explanation-content">${esc(trimmed)}</div></div>`;
  }

  window.formatSentenceWithBlank = formatSentenceWithBlank;
  window.buildOptionDetailsHtml = buildOptionDetailsHtml;
  window.renderExplanationBox = renderExplanationBox;
})();
