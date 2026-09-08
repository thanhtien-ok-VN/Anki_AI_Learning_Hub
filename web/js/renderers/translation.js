/**
 * Translation game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  function renderTranslation(x){
    const d = document.querySelector('#play');
    if (!x || (!x.source_sentence && (!x.sentences || !x.sentences.length))) {
      if (d) d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu bài tập.</p></div>';
      return;
    }
    const state = window.HubState || {};
    const isNewSchema = !!x.source_sentence;
    const sourceText = isNewSchema ? x.source_sentence : (x.sentences && x.sentences[0] ? x.sentences[0].source_text : '');
    const targetText = isNewSchema ? x.reference_translation : (x.sentences && x.sentences[0] ? x.sentences[0].target_text : '');
    const alternativeTranslations = isNewSchema ? x.alternative_translations : [];

    d.innerHTML = '<div class="question-card"><p class="q-text">'+esc(sourceText)+'</p><textarea id="answer" placeholder="'+esc(t('placeholder.translation', 'Nhập bản dịch…'))+'"></textarea><button class="btn" id="grade">'+esc(t('app.grade', 'Chấm điểm'))+'</button><div id="feedback"></div></div>';

    const gradeBtn = document.querySelector('#grade');
    if (gradeBtn) {
      gradeBtn.onclick = async () => {
        const getSignal = window.getSignal || (() => null);
        const setBusy = window.setBusy || (() => {});
        const showBridgeFailure = window.showBridgeFailure || console.error;
        const signal = getSignal();

        try {
          setBusy(true, t('app.grading', 'Đang chấm điểm…'));
          const levelEl = document.querySelector('#level');
          const ansEl = document.querySelector('#answer');
          const ansVal = ansEl ? ansEl.value : '';

          let r = await Bridge.sendAsync('ai_grade', {
            gamemode: 'translation',
            level: levelEl ? levelEl.value : 'intermediate',
            user_answer: ansVal,
            expected: targetText,
            reference_translation: targetText,
            source_text: sourceText,
            source_sentence: sourceText
          }, { signal });

          if (signal?.aborted) return;
          const fb = document.querySelector('#feedback');
          if (!fb) return;

          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { user_answer: ansVal };
            state.currentHistoryItem.score = typeof r.score !== 'undefined' ? r.score : (r.correct ? 10 : 0);
            if (window.HubPersistence && window.HubPersistence.saveHistory) {
              window.HubPersistence.saveHistory(state);
            } else if (typeof window.saveHistory === 'function') {
              window.saveHistory();
            }
          }

          let html = '<div class="feedback ' + (r.correct ? 'good' : 'bad') + '"><b>' + (r.correct ? esc(t('feedback.exact', 'Chính xác!')) : esc(t('feedback.needs_improvement', 'Cần cải thiện'))) + '</b>';

          if (typeof r.score !== 'undefined') {
            const lv = r.level || (r.correct ? t('feedback.grade_pass', 'Đạt') : t('feedback.grade_improve', 'Cần cải thiện'));
            html += `<div class="overall-grade" style="margin-top:10px; padding:10px; background:var(--color-surface-tint); border-radius:6px; border-left:4px solid ${r.correct?'var(--success)':'var(--error)'}">
              <p style="margin: 0;">📊 <b>${esc(t('feedback.overall_grade', 'ĐÁNH GIÁ CHUNG'))}:</b> ${esc(t('feedback.score_label', 'Điểm số'))}: <span style="font-size:16px; font-weight:700; color:${r.correct?'var(--success)':'var(--error)'}">${r.score}/10</span> (${esc(lv)})</p>
            </div>`;
          }

          if (r.errors && r.errors.length) {
            html += '<hr><p><b>🔍 ' + esc(t('feedback.detailed_error_analysis', 'PHÂN TÍCH LỖI:')) + '</b></p>';
            r.errors.forEach(err => {
              if (typeof err === 'object' && err.name) {
                html += `<div class="error-item error-item-block">
                  <p style="margin:2px 0;">🔴 <b>${esc(t('feedback.error_label', 'Lỗi'))}:</b> ${esc(err.name)}</p>
                  <p style="margin:2px 0; padding-left:14px; font-size:13px;">❌ <b>${esc(t('feedback.wrong_label', 'Lỗi sai'))}:</b> <span style="color:var(--error);">${esc(err.wrong)}</span> ➔ <b>${esc(t('feedback.reason_label', 'Vì sao sai'))}:</b> <i>${esc(err.reason)}</i></p>
                  <p style="margin:2px 0; padding-left:14px; font-size:13px;">💡 <b>${esc(t('feedback.suggestion_label', 'Gợi ý sửa'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(err.suggestion)}</span> ➔ <b>${esc(t('feedback.fix_label', 'Vì sao sửa'))}:</b> <i>${esc(err.why)}</i></p>
                </div>`;
              } else {
                html += `<p>• ${esc(err)}</p>`;
              }
            });
          } else if (r.explanation || r.feedback) {
            html += `<p>${esc(r.explanation || r.feedback)}</p>`;
          }

          if (r.suggested_answers) {
            html += '<hr><p><b>✅ ' + esc(t('feedback.suggested_answers_title', 'ĐÁP ÁN GỢI Ý:')) + '</b></p>';
            if (r.suggested_answers.common) {
              html += `<p style="margin:4px 0;">• <b>${esc(t('feedback.common_translation', 'Thông thường (Common)'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(r.suggested_answers.common)}</span></p>`;
            }
            if (r.suggested_answers.advanced) {
              html += `<p style="margin:4px 0;">• <b>${esc(t('feedback.advanced_translation', 'Nâng cao (Advanced)'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(r.suggested_answers.advanced)}</span></p>`;
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

          html += '<button class="btn" id="retry-trans">' + esc(t('app.retry', 'Làm lại')) + '</button></div>';
          fb.innerHTML = html;

          const retryBtn = document.querySelector('#retry-trans');
          if (retryBtn) {
            retryBtn.onclick = () => {
              state.answers = {};
              if (typeof window.play === 'function') window.play(state.route);
            };
          }
        } catch(e) {
          if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') return;
          showBridgeFailure(e);
        } finally {
          if (!signal?.aborted) setBusy(false);
        }
      };
    }
  }

  window.renderTranslation = renderTranslation;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('translation', { render: renderTranslation });
  }
})();
