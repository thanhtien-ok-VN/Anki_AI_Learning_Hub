/**
 * Story Comprehension game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

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

  function renderStory(x) {
    const d = document.querySelector('#play');
    if (!d) return;
    if (!x || !x.story) {
      d.innerHTML = `<div class="empty-state"><p>${esc(t('story.no_data', 'Không có dữ liệu bài đọc.'))}</p></div>`;
      return;
    }

    const state = window.HubState || {};
    const isGraded = !!state.isGraded;
    const gameId = state.route;
    const renderExpBox = window.renderExplanationBox;

    const isNewSchema = !!x.questions;
    const questions = isNewSchema ? (x.questions || []) : (x.comprehension_questions || []);

    let score = 0;
    if (isGraded && questions.length) {
      questions.forEach((q, i) => {
        let correctIdx = q.options.findIndex(o => typeof o === 'object' ? o.is_correct : false);
        if (correctIdx === -1) correctIdx = q.correct_index;
        if (state.answers?.[i] === correctIdx) score++;
      });
    }

    const targetWords = questions
      .filter(q => q.type === 'vocabulary' && q.target_word)
      .map(q => q.target_word);

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
          <span class="story-passage-title">📖 ${title ? esc(title) : t('story.reading_passage', 'Bài đọc hiểu (Reading Passage)')}</span>
          <span class="story-passage-badge">${esc(t('story.questions_count', '{0} câu hỏi', questions.length))}</span>
        </div>
        <div class="story-passage-content" style="font-size:15px; line-height:1.6;">
          ${highlightWords(content, targetWords).replace(/\n\n/g, '<br><br>')}
        </div>
        ${fullTranslation ? `
          <details style="margin-top:12px; border-top:1px dashed var(--border); padding-top:10px;">
            <summary class="cursor-pointer font-semibold text-primary">${t('story.view_translation', '🌐 Xem bản dịch')}</summary>
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
            <p style="margin:0;">${t('story.no_questions_generated', '<b>⚠️ Không thể tạo câu hỏi tự động:</b> Rất tiếc, hệ thống không thể khởi tạo bộ câu hỏi đọc hiểu cho bài này. Vui lòng đọc nội dung trên hoặc bấm <b>\"Tạo bài\"</b> để tạo bài đọc mới.')}</p>
          </div>
        </div>
      `;
      return;
    }

    // Questions list
    const questionsHtml = questions.map((q, i) => {
      const chosen = state.answers?.[i];

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
              <b>${esc(t('story.evidence_quote', 'Dẫn chứng trong bài đọc'))}:</b>
              <div class="story-quote-text">"${esc(quoteText)}"</div>
            </div>
          </div>
        ` : '';

        const explanationSection = renderExpBox ? renderExpBox(q.explanation, t('feedback.explanation_label', 'Giải thích đáp án')) : '';

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
          qStatusBadge = `<span class="q-badge unselected">${esc(t('story.not_done', 'Chưa làm'))}</span>`;
        } else if (chosen === correctIdx) {
          qStatusBadge = `<span class="q-badge correct">${esc(t('feedback.badge_correct_short', '✓ Đúng'))}</span>`;
        } else {
          qStatusBadge = `<span class="q-badge wrong">${esc(t('feedback.badge_wrong_short', '✕ Sai'))}</span>`;
        }
      }

      const typeBadge = q.type ? `<span class="q-type-badge">${esc(q.type)}</span>` : '';

      return `
        <div class="story-question-card ${isGraded ? (chosen === correctIdx ? 'correct-border' : 'wrong-border') : ''}">
          <div class="story-q-header">
            <span class="story-q-number">${esc(t('story.question_counter', 'Câu {0}/{1}', i + 1, questions.length))} ${typeBadge}</span>
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

    let footerHtml = '';
    if (isGraded) {
      const accuracyPct = Math.round((score / questions.length) * 100);
      footerHtml = `
        <div class="story-result-summary fade-in">
          <div class="story-score-title">${t('story.result_title', '🎉 Kết quả bài đọc hiểu')}</div>
          <div class="story-score-main">${esc(t('story.score_summary', '{0} / {1} câu đúng ({2}%)', score, questions.length, accuracyPct))}</div>
          ${x.discussion_prompt ? `
            <div style="margin-top: 14px; text-align: left; padding: 14px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px;">
              <b>💬 ${esc(t('story.discussion_prompt', 'Gợi ý thảo luận/nói'))}:</b>
              <p style="margin: 6px 0 0 0; font-style: italic; font-size:14px; line-height:1.5;">${esc(x.discussion_prompt)}</p>
            </div>
          ` : ''}
          <div class="story-actions">
            <button class="btn primary" id="story-retry-btn">${esc(t('story.retry_btn', '🔄 Làm lại bài này'))}</button>
            <button class="btn btn-outline" id="story-new-btn">${esc(t('story.new_btn', '⚡ Tạo bài đọc mới'))}</button>
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

          if (!state.answers) state.answers = {};
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
            if (state.answers?.[i] === correctIdx) currentScore++;
          });

          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { ...state.answers };
            state.currentHistoryItem.score = currentScore;
          }
          if (window.HubPersistence && window.HubPersistence.saveHistory) {
            window.HubPersistence.saveHistory(state);
          } else if (typeof window.saveHistory === 'function') {
            window.saveHistory();
          }

          renderStory(x);
        };
      }
    } else {
      const retryBtn = document.querySelector('#story-retry-btn');
      if (retryBtn) {
        retryBtn.onclick = () => {
          state.answers = {};
          state.isGraded = false;
          if (typeof window.play === 'function') window.play(gameId);
        };
      }

      const newBtn = document.querySelector('#story-new-btn');
      if (newBtn) {
        newBtn.onclick = () => {
          if (typeof window.generate === 'function') window.generate(gameId);
        };
      }
    }
  }

  window.renderStory = renderStory;
  window.highlightWords = highlightWords;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('story', { render: renderStory });
  }
})();
