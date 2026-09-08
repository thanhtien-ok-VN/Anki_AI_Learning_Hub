/**
 * Sentence Transformation game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  const normalizeText = text => {
    if (!text) return "";
    return String(text)
      .trim()
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[.,!?;:]$/, '')
      .replace(/\s+/g, ' ');
  };
  const norm = normalizeText;

  function renderSentenceTransform(x){
    const d = document.querySelector('#play');
    if (!x?.questions?.length) {
      if (d) d.innerHTML = '<div class="empty-state"><p>Không có câu hỏi.</p></div>';
      return;
    }
    const state = window.HubState || {};
    const q = x.questions[0];
    const originalText = q.original || q.original_sentence || '';
    const instructionText = q.prompt || q.instruction || '';
    const expectedText = q.expected_answer || '';
    const normExpected = q.normalized_answer || norm(expectedText);

    d.innerHTML = '<div class="question-card"><p class="q-text"><b>' + esc(t('feedback.requirement', 'Yêu cầu:')) + '</b> ' + esc(instructionText) + '</p><p class="q-text"><b>' + esc(t('feedback.original_sentence', 'Câu gốc:')) + '</b> ' + esc(originalText) + '</p><textarea id="answer" placeholder="' + esc(t('placeholder.sentence_transform', 'Nhập câu trả lời...')) + '"></textarea><div class="flex gap-3 mt-3"><button class="btn primary" id="grade">' + esc(t('app.grade', 'Chấm điểm')) + '</button><button class="btn btn-outline" id="hint-transform" class="btn-hint">' + esc(t('hint.hint_btn', '💡 Gợi ý')) + '</button></div><div class="hint-text-box" id="hint-text-transform" style="text-align: left !important; width: 100% !important; box-sizing: border-box !important;"></div><div id="feedback"></div></div>';

    const hintBtn = document.querySelector('#hint-transform');
    if (hintBtn) {
      hintBtn.onclick = () => {
        if (state.hintedQuestions) state.hintedQuestions.add(0);
        const textEl = document.querySelector('#hint-text-transform');
        if (window.HintSystem) {
          window.HintSystem.requestHint('sentence_transform', q, 0, textEl, hintBtn);
        }
      };
    }

    const gradeBtn = document.querySelector('#grade');
    if (gradeBtn) {
      gradeBtn.onclick = async () => {
        const getSignal = window.getSignal || (() => null);
        const setBusy = window.setBusy || (() => {});
        const showBridgeFailure = window.showBridgeFailure || console.error;
        const signal = getSignal();

        try {
          setBusy(true, t('app.grading', 'Đang chấm điểm…'));

          const ansVal = document.querySelector('#answer')?.value || '';
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

          let r;
          const wasHinted = state.hintedQuestions && state.hintedQuestions.has(0);
          if (isCorrect) {
            r = { correct: !wasHinted, score: wasHinted ? 0.0 : 10.0, explanation: wasHinted ? t('feedback.hinted_explanation', 'Bạn đã dùng gợi ý xem đáp án.') : t('feedback.exact_match_explanation', 'Chính xác! Câu trả lời của bạn trùng khớp với đáp án chuẩn.') };
          } else {
            const levelEl = document.querySelector('#level');
            r = await Bridge.sendAsync('ai_grade', {
              gamemode: 'sentence_transform',
              level: levelEl ? levelEl.value : 'intermediate',
              user_answer: ansVal,
              expected: expectedText,
              expected_answer: expectedText,
              instruction: instructionText,
              prompt: instructionText,
              original: originalText,
              hint_level: wasHinted ? 1 : 0
            }, { signal });
          }

          if (signal?.aborted) return;
          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { user_answer: ansVal };
            state.currentHistoryItem.score = typeof r.score !== 'undefined' ? r.score : (r.correct ? 10 : 0);
            if (window.HubPersistence && window.HubPersistence.saveHistory) {
              window.HubPersistence.saveHistory(state);
            } else if (typeof window.saveHistory === 'function') {
              window.saveHistory();
            }
          }
          if (!r.correct && state.pairs && state.pairs[0]) {
            if (typeof window.addWeakWord === 'function') {
              window.addWeakWord(state.pairs[0].term);
            }
          }
          const fb = document.querySelector('#feedback');
          if (!fb) return;

          let html = '<div class="feedback ' + (r.correct ? 'good' : 'bad') + '"><b>' + (r.correct ? '🎉 ' + esc(t('feedback.exact', 'Chính xác!')) : '❌ ' + esc(t('feedback.needs_improvement', 'Cần cải thiện'))) + '</b>';

          // 1. ĐÁNH GIÁ CHUNG
          if (typeof r.score !== 'undefined') {
            let lv = r.level;
            if (lv === 'Pass') lv = t('feedback.grade_pass', 'Đạt');
            else if (lv === 'Needs improvement') lv = t('feedback.grade_improve', 'Cần cải thiện');
            else if (!lv) lv = r.correct ? t('feedback.grade_pass', 'Đạt') : t('feedback.grade_improve', 'Cần cải thiện');

            html += `<div class="overall-grade" style="margin-top:10px; padding:10px; background:var(--color-surface-tint); border-radius:6px; border-left:4px solid ${r.correct?'var(--success)':'var(--error)'}">
              <p style="margin: 0;">📊 <b>${esc(t('feedback.overall_grade', 'ĐÁNH GIÁ CHUNG'))}:</b> ${esc(t('feedback.score_label', 'Điểm số'))}: <span style="font-size:16px; font-weight:700; color:${r.correct?'var(--success)':'var(--error)'}">${r.score}/10</span> (${esc(lv)})</p>
            </div>`;
          }

          html += `<p style="margin-top:10px;">• <b>${esc(t('feedback.your_answer', 'Câu trả lời của bạn'))}:</b> <span style="color:${r.correct?'var(--success)':'var(--error)'}; font-weight:600;">${esc(ansVal)}</span></p>`;
          if (!r.correct) {
            html += `<p>• <b>${esc(t('feedback.expected_answer', 'Đáp án chuẩn'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(expectedText)}</span></p>`;
          }

          // 2. PHÂN TÍCH LỖI CHI TIẾT
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
          } else if (r.specific_error || r.why_wrong || r.how_to_fix || r.why_fix) {
            html += `<hr><p><b>🔍 ${esc(t('feedback.detailed_error_analysis', 'Phân tích chi tiết lỗi sai'))}:</b></p>
            <div class="error-item error-item-block">
              <p style="margin:2px 0;">🔴 <b>${esc(t('feedback.error_label', 'Lỗi'))}:</b> ${esc(r.specific_error || t('feedback.grammar_vocab_error', 'Lỗi cấu trúc/Từ vựng'))}</p>
              <p style="margin:2px 0; padding-left:14px; font-size:13px;">❌ <b>${esc(t('feedback.wrong_label', 'Lỗi sai'))}:</b> <span style="color:var(--error);">${esc(ansVal)}</span> ➔ <b>${esc(t('feedback.reason_label', 'Vì sao sai'))}:</b> <i>${esc(r.why_wrong || t('feedback.grammar_structure_error', 'Chưa biến đổi đúng cấu trúc ngữ pháp yêu cầu'))}</i></p>
              <p style="margin:2px 0; padding-left:14px; font-size:13px;">💡 <b>${esc(t('feedback.suggestion_label', 'Cách sửa'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(r.how_to_fix || expectedText)}</span> ➔ <b>${esc(t('feedback.fix_label', 'Vì sao sửa'))}:</b> <i>${esc(r.why_fix || t('feedback.rule_fix_error', 'Đảm bảo đúng quy tắc biến đổi câu'))}</i></p>
            </div>`;
          } else if (r.explanation || r.feedback) {
            html += `<p>${esc(r.explanation || r.feedback)}</p>`;
          }

          // 3. ĐÁP ÁN GỢI Ý
          if (r.suggested_answers) {
            html += '<hr><p><b>✅ ' + esc(t('feedback.suggested_answers_title', 'ĐÁP ÁN GỢI Ý:')) + '</b></p>';
            if (r.suggested_answers.common) {
              html += `<p style="margin:4px 0;">• <b>${esc(t('feedback.common_translation', 'Thông thường (Common)'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(r.suggested_answers.common)}</span></p>`;
            }
            if (r.suggested_answers.advanced) {
              html += `<p style="margin:4px 0;">• <b>${esc(t('feedback.advanced_translation', 'Nâng cao (Advanced)'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(r.suggested_answers.advanced)}</span></p>`;
            }
          }

          // 4. QUY TẮC NGỮ PHÁP & ACCEPTABLE VARIATIONS
          const grammar = q.grammar_rule || r.grammar_rule;
          if (grammar) {
            html += '<hr><p><b>📌 ' + esc(t('feedback.grammar_rule', 'Quy tắc ngữ pháp')) + ':</b> ' + esc(grammar) + '</p>';
          }

          const variations = q.acceptable_variations || r.acceptable_variations;
          if (variations && variations.length) {
            html += '<p>✅ <b>' + esc(t('feedback.acceptable_variations', 'Các biến thể đúng khác')) + ':</b></p><ul>';
            variations.forEach(v => {
              const txt = typeof v === 'object' ? v.text : v;
              const note = typeof v === 'object' ? v.note : '';
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

  window.renderSentenceTransform = renderSentenceTransform;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('sentence_transform', { render: renderSentenceTransform });
  }
})();
