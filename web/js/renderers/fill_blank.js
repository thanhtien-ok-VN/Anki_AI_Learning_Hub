/**
 * FillBlank game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  function renderFillBlank(x) {
    const d = document.querySelector('#play');
    if (!x?.questions?.length) {
      if (d) d.innerHTML = '<div class="empty-state"><p>Không có câu hỏi.</p></div>';
      return;
    }
    const state = window.HubState || {};
    const isGraded = !!state.isGraded;
    const formatSentence = window.formatSentenceWithBlank;
    const buildDetails = window.buildOptionDetailsHtml;
    const renderExpBox = window.renderExplanationBox;

    let totalPoints = 0;
    let correctCount = 0;

    x.questions.forEach((q, i) => {
      let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
      if (correctIdx === -1) correctIdx = q.correct_index;
      const chosen = state.answers?.[i];
      const isCorrect = chosen === correctIdx;
      const hLevel = window.HintSystem?.hintLevels?.[i] || q._hint_level || 0;

      let p = 0.0;
      if (isCorrect) {
        correctCount++;
        if (hLevel === 0) p = 1.0;
        else if (hLevel === 1) p = 0.75;
        else if (hLevel === 2) p = 0.50;
        else p = 0.0;
      }
      q._calculated_points = p;
      q._hint_level = hLevel;
      if (isGraded) totalPoints += p;
    });

    const cardsHtml = x.questions.map((q, i) => {
      const chosen = state.answers?.[i];
      const rawSentence = q.sentence_with_blank || q.sentence || '';
      const correctOpt = q.options.find(o => typeof o === 'object' ? o.is_correct : false);
      const correctWord = q.target_word || (correctOpt ? correctOpt.word : '');
      const chosenOpt = (chosen !== undefined && q.options && q.options[chosen]);
      const chosenWord = chosenOpt ? (typeof chosenOpt === 'object' ? chosenOpt.word : chosenOpt) : '';

      const sentenceHtml = formatSentence
        ? formatSentence(rawSentence, chosenWord, isGraded, (chosen === q.correct_index || (correctOpt && q.options.indexOf(correctOpt) === chosen)), correctWord)
        : rawSentence;

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

        let hintNotice = '';
        const hLevel = q._hint_level || 0;
        if (hLevel === 1) {
          hintNotice = `<div style="font-size:13px; font-weight:600; color:#ca8a04; margin-bottom:8px;">💡 Đã dùng Gợi ý Cấp 1 (-25% điểm) ➔ Đạt ${q._calculated_points ?? 0.75}/1.0 điểm</div>`;
        } else if (hLevel === 2) {
          hintNotice = `<div style="font-size:13px; font-weight:600; color:#ca8a04; margin-bottom:8px;">💡 Đã dùng Gợi ý Cấp 2 (-50% điểm) ➔ Đạt ${q._calculated_points ?? 0.5}/1.0 điểm</div>`;
        } else if (hLevel >= 3) {
          hintNotice = `<div style="font-size:13px; font-weight:600; color:#dc2626; margin-bottom:8px;">💡 Đã dùng Gợi ý Cấp 3 (Hiện đáp án) ➔ 0.0/1.0 điểm</div>`;
        }

        feedbackHtml = `
          <div class="feedback ${isCorrect ? 'good' : 'bad'}" style="margin-top:16px; padding:16px; border-radius:8px;">
            <div style="font-weight:700; font-size:16px; margin-bottom:8px; color:${isCorrect ? 'var(--success)' : 'var(--error)'};">
              ${isCorrect ? esc(t('feedback.exact', 'Chính xác! ✓')) : esc(t('feedback.incorrect_fill_blank', 'Chưa đúng ✕'))}
            </div>

            ${hintNotice}

            <div class="mb-3">
              <b>🌐 ${esc(t('feedback.full_sentence_translation', 'Dịch câu hoàn chỉnh'))}:</b>
              <div style="margin-top:4px; padding:10px 12px; background:var(--color-surface-tint); border-radius:6px; font-size:13.5px; line-height:1.5;">
                ${esc(q.full_translation || q.sentence_translation || q.full_sentence_translation || t('feedback.no_translation', 'Không có bản dịch'))}
              </div>
            </div>

            ${renderExpBox ? renderExpBox(q.explanation || q.explanation_short, t('feedback.reason_choice', 'Lý do chọn')) : ''}

            ${q.grammar_note && renderExpBox ? renderExpBox(q.grammar_note, t('feedback.grammar_rule', 'Ghi chú ngữ pháp')) : ''}

            ${buildDetails ? buildDetails(q, chosen) : ''}
          </div>
        `;
      }

      return `
        <div class="question-card" id="qcard-${i}">
          <div class="q-number">Câu ${i + 1}/${x.questions.length}</div>
          <div class="q-text" id="qtext-${i}" style="font-size:16px; font-weight:600; margin-bottom:12px;">${sentenceHtml}</div>
          <div class="options-grid" id="choices-${i}">
            ${optsHtml}
          </div>
          ${!isGraded ? `
            <div style="margin-top: 10px; text-align: right;">
              <button class="btn btn-outline hint-btn" data-hint-q="${i}" style="padding: 4px 10px; font-size: 12.5px; border-color:var(--color-warn); color:var(--color-warn-dark);">
                💡 Gợi ý
              </button>
              <div class="hint-text-box" id="hint-text-${i}" style="text-align: left !important; width: 100% !important; box-sizing: border-box !important;"></div>
            </div>
          ` : ''}
          <div id="feedback-${i}">${feedbackHtml}</div>
        </div>
      `;
    }).join('');

    const submitHtml = isGraded ? `
      <div id="fill-overall-feedback">
        <div class="feedback ${totalPoints > 0 ? 'good' : 'bad'} text-center mt-5">
          <h3 class="mb-2">Kết quả: ${totalPoints % 1 === 0 ? totalPoints.toFixed(0) : totalPoints.toFixed(2)}/${x.questions.length} điểm (${correctCount}/${x.questions.length} câu đúng)</h3>
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
          if (!state.answers) state.answers = {};
          state.answers[qIdx] = cIdx;
          const choices = document.querySelectorAll(`#choices-${qIdx} [data-choice]`);
          choices.forEach(btn => btn.classList.remove('selected'));
          b.classList.add('selected');

          // Dynamically fill the selected word into the blank pill in the question sentence
          const q = x.questions[qIdx];
          const rawSentence = q.sentence_with_blank || q.sentence || '';
          const chosenOpt = q.options[cIdx];
          const chosenWord = typeof chosenOpt === 'object' ? chosenOpt.word : chosenOpt;
          const qTextEl = document.querySelector(`#qtext-${qIdx}`);
          if (qTextEl && formatSentence) {
            qTextEl.innerHTML = formatSentence(rawSentence, chosenWord, false, false, '');
          }
        };
      });

      d.querySelectorAll('[data-hint-q]').forEach(btn => {
        btn.onclick = () => {
          const qIdx = +btn.dataset.hintQ;
          if (state.hintedQuestions) state.hintedQuestions.add(qIdx);
          const q = x.questions[qIdx];
          const textEl = document.querySelector(`#hint-text-${qIdx}`);
          if (window.HintSystem) {
            window.HintSystem.requestHint('fill_blank', q, qIdx, textEl, btn);
          }
        };
      });

      const gradeBtn = document.querySelector('#grade-fill-blank');
      if (gradeBtn) {
        gradeBtn.onclick = () => {
          state.isGraded = true;
          let finalScore = 0;
          x.questions.forEach((q, i) => {
            let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
            if (correctIdx === -1) correctIdx = q.correct_index;
            const isCorrect = state.answers[i] === correctIdx;
            const hLevel = window.HintSystem?.hintLevels?.[i] || 0;
            let p = 0.0;
            if (isCorrect) {
              if (hLevel === 0) p = 1.0;
              else if (hLevel === 1) p = 0.75;
              else if (hLevel === 2) p = 0.50;
              else p = 0.0;
            } else {
              const correctOpt = q.options[correctIdx];
              const termWord = typeof correctOpt === 'object' ? correctOpt.word : correctOpt;
              if (typeof window.addWeakWord === 'function') {
                window.addWeakWord(termWord);
              }
            }
            finalScore += p;
          });

          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { ...state.answers };
            state.currentHistoryItem.score = finalScore;
            state.currentHistoryItem.correct_count = correctCount;
            state.currentHistoryItem.hint_levels = { ...(window.HintSystem?.hintLevels || {}) };
          }
          if (window.HubPersistence && window.HubPersistence.saveHistory) {
            window.HubPersistence.saveHistory(state);
          } else if (typeof window.saveHistory === 'function') {
            window.saveHistory();
          }

          renderFillBlank(x);
        };
      }
    }
  }

  window.renderFillBlank = renderFillBlank;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('fill_blank', { render: renderFillBlank });
  }
})();
