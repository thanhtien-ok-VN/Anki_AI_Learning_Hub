/**
 * Taboo game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  function renderTaboo(x){
    const d = document.querySelector('#play');
    if (!x?.rounds?.length) {
      if (d) d.innerHTML = '<div class="empty-state"><p>Không có dữ liệu bài tập.</p></div>';
      return;
    }
    const state = window.HubState || {};
    const renderExpBox = window.renderExplanationBox;

    if (!state.tabooOrder || !state.tabooOrder.length || state.tabooOrder.length !== x.rounds.length) {
      state.tabooOrder = Array.from({ length: x.rounds.length }, (_, i) => i);
      for (let i = state.tabooOrder.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [state.tabooOrder[i], state.tabooOrder[j]] = [state.tabooOrder[j], state.tabooOrder[i]];
      }
      state.tabooCursor = 0;
    }

    const currentRoundIdx = state.tabooOrder[state.tabooCursor];
    const q = x.rounds[currentRoundIdx];
    const langCode = (state.userPrefs && (state.userPrefs.learn_lang || state.userPrefs.language)) || 'en';
    const langLabel = (typeof Utils !== 'undefined' && typeof Utils.getLanguageName === 'function')
      ? Utils.getLanguageName(langCode)
      : langCode;
    const secretWord = q.target_word || '';
    const forbidden = q.taboo_words || [];
    const clueText = q.clue || '';

    d.innerHTML = `
      <div class="question-card taboo-card fade-in">
        <div style="font-size: 13.5px; color: var(--text-secondary); margin-bottom: 12px; font-weight:600;">${esc(t('taboo.round_counter', 'Lượt chơi {0} / {1}', state.tabooCursor + 1, x.rounds.length))}</div>
        <div class="secret-word">???</div>
        <div class="forbidden">${forbidden.map(w => '<span>🚫 ' + esc(w) + '</span>').join('')}</div>
        <div class="description">${esc(clueText)}</div>
        <textarea id="answer" placeholder="${esc(t('placeholder.taboo', 'Nhập từ bạn đoán bằng {0}...', langLabel))}"></textarea>
        <div class="flex gap-3 mt-3">
          <button class="btn primary" id="grade">${esc(t('app.grade', 'Chấm điểm'))}</button>
          <button class="btn btn-outline" id="hint-taboo" class="btn-hint">${esc(t('hint.hint_btn', '💡 Gợi ý'))}</button>
        </div>
        <div class="hint-text-box" id="hint-text-taboo" style="text-align: left !important; width: 100% !important; box-sizing: border-box !important;"></div>
        <div id="feedback"></div>

        <div class="taboo-guide-callout" style="margin-top: 24px; padding: 12px; background:var(--color-surface-tint); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 13px; line-height: 1.4; color: var(--text-secondary);">
          ${t('taboo.guide_title', '💡 HƯỚNG DẪN ĐOÁN TỪ (01 LẦN GỬI):')}
          <ul class="mt-1 ml-2 list-none">
            <li>Nhập nhiều từ hoặc cụm từ đoán cách nhau bằng dấu phẩy.</li>
            <li>Chỉ cần 1 trong các từ bạn nhập là đáp án đúng hoặc đồng nghĩa, bạn sẽ thắng.</li>
            <li>Ví dụ: <code>hobby, habit, custom, routine</code>.</li>
            <li><i>Chú ý: Tuyệt đối tránh sử dụng các từ cấm ở trên!</i></li>
          </ul>
        </div>
      </div>
    `;

    const hintBtn = document.querySelector('#hint-taboo');
    if (hintBtn) {
      hintBtn.onclick = () => {
        if (state.hintedQuestions) state.hintedQuestions.add(currentRoundIdx);
        const textEl = document.querySelector('#hint-text-taboo');
        if (window.HintSystem) {
          window.HintSystem.requestHint('taboo', q, currentRoundIdx, textEl, hintBtn);
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
          const guessInput = document.querySelector('#answer')?.value.trim() || '';
          const guessList = guessInput.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
          const correctWord = secretWord.trim().toLowerCase();
          const localMatch = guessList.includes(correctWord);

          let r;
          if (localMatch) {
            const wasHinted = state.hintedQuestions && state.hintedQuestions.has(currentRoundIdx);
            r = {
              correct: !wasHinted,
              score: wasHinted ? 0.0 : 10.0,
              explanation: wasHinted ? t('feedback.hinted_explanation', 'Bạn đã dùng gợi ý xem đáp án.') : t('taboo.correct_guess_explanation', 'Chính xác! Bạn đã đoán đúng từ mục tiêu.'),
              guess_feedback: guessList.map(g => ({
                guess: g,
                accepted: g === correctWord,
                reason: g === correctWord ? (wasHinted ? t('taboo.correct_but_hinted', 'Correct, but you viewed the answer hint.') : t('taboo.exact_target_match', 'Correct! Matches target word exactly.')) : t('taboo.not_target', 'Not the target word.')
              }))
            };
          } else {
            const levelEl = document.querySelector('#level');
            r = await Bridge.sendAsync('ai_grade', {
              gamemode: 'taboo',
              level: levelEl ? levelEl.value : 'intermediate',
              user_answer: guessInput,
              target_word: secretWord,
              meaning: q.meaning || '',
              taboo_words: forbidden.join(', '),
              sample_acceptable_phrases: (q.sample_acceptable_phrases || []).join(', '),
              sample_forbidden_phrases: (q.sample_forbidden_phrases || []).join(', ')
            }, { signal });
          }

          if (signal?.aborted) return;
          if (state.currentHistoryItem) {
            state.currentHistoryItem.answers = { user_answer: guessInput };
            state.currentHistoryItem.score = typeof r.score !== 'undefined' ? r.score : (r.correct ? 10 : 0);
            if (window.HubPersistence && window.HubPersistence.saveHistory) {
              window.HubPersistence.saveHistory(state);
            } else if (typeof window.saveHistory === 'function') {
              window.saveHistory();
            }
          }
          if (!r.correct) {
            if (typeof window.addWeakWord === 'function') {
              window.addWeakWord(secretWord);
            }
          }

          const ansInput = document.querySelector('#answer');
          const grdBtn = document.querySelector('#grade');
          if (ansInput) ansInput.disabled = true;
          if (grdBtn) grdBtn.disabled = true;
          if (hintBtn) {
            hintBtn.disabled = true;
            hintBtn.style.opacity = '0.5';
          }

          const fb = document.querySelector('#feedback');
          if (!fb) return;

          let html = '<div class="feedback ' + (r.correct ? 'good' : 'bad') + '"><b>' + t('taboo.result_title', '📊 KẾT QUẢ CHẤM ĐIỂM') + '</b><hr>';
          html += `<p style="font-size: 15px;"><b>${r.correct ? esc(t('taboo.correct', '🎯 CHÍNH XÁC')) : esc(t('taboo.incorrect', '❌ CHƯA CHÍNH XÁC'))}</b></p>`;
          html += `<p>📥 <b>${esc(t('taboo.your_guesses', 'Danh sách từ bạn đã nhập'))}:</b> ${guessList.map(g => `<code>${esc(g)}</code>`).join(', ') || esc(t('taboo.not_entered', 'Chưa nhập'))}</p>`;
          html += `<p>🔑 <b>${esc(t('feedback.expected_answer', 'Đáp án đúng'))}:</b> <span style="color:var(--success); font-weight:700;">${esc(secretWord.toUpperCase())}</span> ${q.phonetic ? `<code style="font-size:13.5px; color:var(--text-secondary); margin-left:6px;">${esc(q.phonetic)}</code>` : ''}</p>`;
          if (q.meaning) {
            html += `<p>🌐 <b>${esc(t('taboo.definition_label', 'Dịch nghĩa'))}:</b> ${esc(q.meaning)}</p>`;
          }

          const aiAnalysisText = r.ai_analysis || r.explanation || r.feedback || '';
          if (aiAnalysisText && renderExpBox) {
            html += renderExpBox(aiAnalysisText, t('taboo.ai_analysis_label', 'PHÂN TÍCH TỪ AI'));
          }

          const feedbackList = r.guess_feedback || [];
          if (!feedbackList.length) {
            if (r.accepted_phrases && r.accepted_phrases.length) {
              r.accepted_phrases.forEach(item => feedbackList.push({ guess: item.phrase, accepted: true, reason: item.explanation || item.explanation_vi || item.reason }));
            }
            if (r.rejected_phrases && r.rejected_phrases.length) {
              r.rejected_phrases.forEach(item => feedbackList.push({ guess: item.phrase, accepted: false, reason: item.reason || item.reason_vi || item.explanation }));
            }
            if (!feedbackList.length) {
              guessList.forEach(g => {
                const isCorrect = g === correctWord;
                feedbackList.push({
                  guess: g,
                  accepted: isCorrect,
                  reason: isCorrect ? t('taboo.matched_target', 'Matches target word.') : (forbidden.includes(g.toUpperCase()) ? t('taboo.taboo_violation', 'Taboo word violation!') : t('taboo.no_match', 'No match or not a synonym.'))
                });
              });
            }
          }

          const acceptedGuesses = feedbackList.filter(item => item.accepted);
          const rejectedGuesses = feedbackList.filter(item => !item.accepted);

          if (acceptedGuesses.length) {
            html += '<hr><p><b>✅ ' + esc(t('taboo.accepted_words', 'CÁC TỪ ĐƯỢC CHẤP NHẬN')) + ':</b></p><ul>';
            acceptedGuesses.forEach(item => {
              html += `<li><code>${esc(item.guess)}</code> ➔ <i>${esc(item.reason || item.reason_vi || '')}</i></li>`;
            });
            html += '</ul>';
          }

          if (rejectedGuesses.length) {
            html += '<hr><p><b>❌ ' + esc(t('taboo.rejected_words', 'CÁC TỪ KHÔNG ĐƯỢC CHẤP NHẬN')) + ':</b></p><ul>';
            rejectedGuesses.forEach(item => {
              html += `<li><code>${esc(item.guess)}</code> ➔ <span style="color:var(--error);">${esc(item.reason || item.reason_vi || '')}</span></li>`;
            });
            html += '</ul>';
          }

          const hasNext = state.tabooCursor < state.tabooOrder.length - 1;
          let btnHtml = '';
          if (hasNext) {
            btnHtml = `<button class="btn primary" id="next-taboo">➡️ Câu tiếp</button>`;
          } else {
            btnHtml = `<button class="btn primary" id="new-taboo-batch">⚡ Tạo bài mới</button>`;
          }
          btnHtml += ` <button class="btn btn-outline" id="retry-taboo-round" style="margin-left: 8px;">🔄 Làm lại câu này</button>`;

          html += `<div style="margin-top:16px;">${btnHtml}</div></div>`;
          fb.innerHTML = html;

          if (hasNext) {
            const nextBtn = document.querySelector('#next-taboo');
            if (nextBtn) {
              nextBtn.onclick = () => {
                state.tabooCursor++;
                renderTaboo(x);
              };
            }
          } else {
            const newBatchBtn = document.querySelector('#new-taboo-batch');
            if (newBatchBtn) {
              newBatchBtn.onclick = () => {
                state.answers = {};
                if (typeof window.generate === 'function') window.generate(state.route);
              };
            }
          }

          const retryBtn = document.querySelector('#retry-taboo-round');
          if (retryBtn) {
            retryBtn.onclick = () => {
              if (state.hintedQuestions) state.hintedQuestions.delete(currentRoundIdx);
              renderTaboo(x);
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

  window.renderTaboo = renderTaboo;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('taboo', { render: renderTaboo });
  }
})();
