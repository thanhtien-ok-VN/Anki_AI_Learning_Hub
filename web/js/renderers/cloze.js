/**
 * Cloze game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  function renderCloze(x) {
    const d = document.querySelector('#play');
    if (!x?.blanks?.length) {
      if (d) d.innerHTML = `<div class="empty-state"><p>${esc(t('cloze.no_data', 'Không có dữ liệu điền từ.'))}</p></div>`;
      return;
    }
    const state = window.HubState || {};
    const isGraded = !!state.isGraded;

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
        <div class="word-bank-title">${esc(t('cloze.word_bank_title', 'Danh sách từ để chọn ({0} từ)', sortedWords.length))}</div>
        <div class="word-bank-chips">
          ${sortedWords.map(w => `<span class="word-chip-static">${esc(w)}</span>`).join('')}
        </div>
      </div>
    `;

    // Process paragraph with clean single-pass inline selects
    let rawText = isNewSchema ? (x.paragraph || '') : (x.paragraph_with_blanks || '');
    let safeText = esc(rawText);
    let blankIdx = 0;
    const placeholderRegex = /(\[BLANK_\d+\]|\[\d+\])/gi;

    let processedParagraph = safeText.replace(placeholderRegex, (match) => {
      if (blankIdx >= x.blanks.length) return match;
      const i = blankIdx++;
      const b = x.blanks[i];
      const chosen = state.answers?.[i];

      let selectClass = 'cloze-select';
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

    let score = 0;
    if (isGraded) {
      x.blanks.forEach((b, i) => {
        if (state.answers?.[i] === b.correct_index) score++;
      });
    }

    let feedbackHtml = '';
    if (isGraded) {
      const explanations = x.blanks.map((b, i) => {
        const correctOpt = b.options[b.correct_index];
        const chosenOpt = state.answers?.[i] !== undefined ? b.options[state.answers[i]] : t('cloze.not_selected', 'Chưa chọn');
        const isOk = state.answers?.[i] === b.correct_index;
        const vnMeaning = (b.meaning || b.meaning_in_vietnamese) ? ` (${b.meaning || b.meaning_in_vietnamese})` : '';

        return `
          <div style="margin-bottom: 10px; font-size: 14px; text-align: left !important;">
            <b>[${i + 1}]</b> <span style="color: ${isOk ? 'var(--success)' : 'var(--error)'}; font-weight:600;">${isOk ? esc(t('feedback.badge_correct_short', '✓ Đúng')) : esc(t('feedback.badge_wrong_short', '✕ Sai'))}</span>
            — ${esc(t('feedback.answer_label_short', 'Đáp án'))}: <b style="color: var(--success);">${esc(correctOpt)}</b>${esc(vnMeaning)}
            ${!isOk ? `<span style="color: var(--text-secondary);">(${esc(t('feedback.you_chose', 'Bạn chọn'))}: ${esc(chosenOpt)})</span>` : ''}
            <div style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">
              💡 ${esc(t('feedback.explanation_label', 'Giải thích'))}: ${esc(b.explanation || b.explanation_short || '')}
            </div>
          </div>
        `;
      }).join('');

      const transHtml = (x.story_translation || x.paragraph_translation || x.sentence_meaning)
        ? `<div style="margin-top:12px; padding-top:10px; border-top:1px dashed var(--border); font-size:14px; text-align: left !important;">
             <b>🌐 ${esc(t('cloze.paragraph_translation', 'Dịch đoạn văn'))}:</b> ${esc(x.story_translation || x.paragraph_translation || x.sentence_meaning)}
             ${x.full_solution_text ? `<br><b>📖 ${esc(t('cloze.completed_paragraph', 'Đoạn văn hoàn chỉnh'))}:</b> ${esc(x.full_solution_text)}` : ''}
           </div>`
        : '';

      feedbackHtml = `
        <div class="feedback ${score === x.blanks.length ? 'good' : 'bad'}" style="margin-top:20px;">
          <h3 style="margin-bottom:12px; text-align:center;">${esc(t('feedback.grading_result', 'Kết quả: {0}/{1} câu đúng', score, x.blanks.length))}</h3>
          ${explanations}
          ${transHtml}
        </div>
      `;
    }

    const submitBtnHtml = isGraded ? '' : `
      <div class="text-center mt-5">
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
      d.querySelectorAll('select.cloze-select').forEach(sel => {
        sel.onchange = () => {
          const bIdx = +sel.dataset.blank;
          const val = sel.value;
          if (!state.answers) state.answers = {};
          state.answers[bIdx] = val !== '' ? +val : undefined;
        };
      });

      const gradeBtn = document.querySelector('#grade-cloze');
      if (gradeBtn) {
        gradeBtn.onclick = () => {
          state.isGraded = true;
          let s = 0;
          x.blanks.forEach((b, i) => {
            if (state.answers?.[i] === b.correct_index) s++;
          });

          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { ...state.answers };
            state.currentHistoryItem.score = s;
          }
          if (window.HubPersistence && window.HubPersistence.saveHistory) {
            window.HubPersistence.saveHistory(state);
          } else if (typeof window.saveHistory === 'function') {
            window.saveHistory();
          }

          renderCloze(x);
        };
      }
    }
  }

  window.renderCloze = renderCloze;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('cloze', { render: renderCloze });
  }
})();
