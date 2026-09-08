/**
 * Word Unscramble game renderer.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  let unscrambleDragState = null;

  function renderUnscrambleAll(x) {
    const d = document.querySelector('#play');
    if (!x?.questions?.length) {
      if (d) d.innerHTML = '<div class="empty-state"><p>Không có câu hỏi.</p></div>';
      return;
    }
    const state = window.HubState || {};
    const isGraded = !!state.isGraded;
    const gameId = state.route;

    let score = 0;
    if (isGraded) {
      x.questions.forEach((q, i) => {
        const feedbackObj = state.answers?.[`feedback_${i}`];
        if (feedbackObj && feedbackObj.correct) score++;
      });
    }

    const cardsHtml = x.questions.map((q, i) => {
      const chosen = state.answers?.[i] || [];
      const isCorrect = isGraded && state.answers?.[`feedback_${i}`]?.correct;
      const feedbackObj = isGraded ? state.answers?.[`feedback_${i}`] : null;
      const isUnanswered = isGraded && (!feedbackObj || feedbackObj.unanswered);

      let cardClass = 'question-card unscramble-card fade-in';
      if (isGraded) {
        if (isUnanswered) cardClass += ' unanswered-card';
        else cardClass += isCorrect ? ' correct-card' : ' wrong-card';
      }

      // Prompt
      const shuffled = Array.isArray(q.shuffled_words) ? q.shuffled_words : (Array.isArray(q.words) ? q.words : []);
      const rawPromptText = `<b>${esc(t('unscramble.prompt', 'Đề bài'))}:</b> ${shuffled.join(' / ')}`;

      let sentenceDisplayHtml = '';
      if (isGraded) {
        if (isCorrect) {
          sentenceDisplayHtml = `
            <div class="unscramble-correct-box" style="margin-top:12px; padding:14px 16px; border:2px solid var(--success); border-radius:8px; background:rgba(46, 204, 113, 0.02);">
              <div style="font-size:12px; font-weight:700; color:white; background:var(--success); padding:3px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">${t('unscramble.correct_mark', '🟢 ĐÚNG')}</div>
              <p style="margin:4px 0 8px; font-size:15px; font-weight:600; color:var(--success);">🎉 ${esc(feedbackObj.praise || 'Chính xác! Lựa chọn trật tự từ hoàn hảo.')}</p>
              <div style="font-size:18px; font-weight:700; color:var(--success); margin:8px 0;">
                ✓ ${esc(q.correct_sentence)}
              </div>
              ${feedbackObj.highlight ? `
                <p style="margin:8px 0 0; font-size:13.5px; color:var(--text-secondary); line-height:1.4;">
                  💡 <b>${esc(t('unscramble.highlight', 'Điểm sáng'))}:</b> ${esc(feedbackObj.highlight)}
                </p>
              ` : ''}
            </div>
          `;
        } else if (isUnanswered) {
          sentenceDisplayHtml = `
            <div class="unscramble-unanswered-box" style="margin-top:12px; padding:14px 16px; border:2px solid var(--border); border-radius:8px; background:var(--color-surface-tint);">
              <div style="font-size:12px; font-weight:700; color:white; background:var(--text-secondary); padding:3px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">${t('unscramble.not_answered', '⚪ CHƯA TRẢ LỜI')}</div>
              <div style="font-size:18px; font-weight:700; color:var(--primary); margin:8px 0;">
                ✅ ${esc(q.correct_sentence)}
              </div>
              ${q.meaning ? `<p style="margin:6px 0; font-size:14px;">📖 <b>${esc(t('taboo.definition_label', 'Dịch nghĩa'))}:</b> ${esc(q.meaning)}</p>` : ''}
              ${q.core_structure ? `<p style="margin:6px 0; font-size:13.5px; color:var(--text-secondary);">💡 <b>${esc(t('unscramble.core_structure', 'Cấu trúc chính'))}:</b> <code>${esc(q.core_structure)}</code></p>` : ''}
            </div>
          `;
        } else {
          sentenceDisplayHtml = `
            <div class="unscramble-wrong-box" style="margin-top:12px; padding:14px 16px; border:2px solid var(--error); border-radius:8px; background:var(--color-error-bg);">
              <div style="font-size:12px; font-weight:700; color:white; background:var(--error); padding:3px 8px; border-radius:4px; display:inline-block; margin-bottom:8px;">${t('unscramble.wrong_mark', '🔴 SAI')}</div>
              <p style="margin:4px 0 8px; font-size:14px; font-weight:600; color:var(--error);">⚠️ ${esc(t('unscramble.wrong_position', 'Vị trí sai'))}: ${esc(feedbackObj.error_position || t('unscramble.word_order_incorrect', 'Trật tự các từ chưa đúng.'))}</p>

              <div class="unscramble-compare" style="margin:10px 0; padding:10px; border-left:3px solid var(--error); background:var(--color-error-bg); border-radius:4px;">
                <p style="margin:2px 0; font-size:13.5px;">❌ <b>${esc(t('feedback.your_answer', 'Câu của bạn'))}:</b> <span style="color:var(--error); font-weight:600;">${esc(chosen.join(' '))}</span></p>
                <p style="margin:2px 0; font-size:13.5px;">✅ <b>${esc(t('feedback.expected_answer', 'Đáp án đúng'))}:</b> <span style="color:var(--success); font-weight:600;">${esc(q.correct_sentence)}</span></p>
              </div>

              ${feedbackObj.rule ? `
                <p style="margin:8px 0 0; font-size:13.5px; color:var(--text-secondary); line-height:1.4;">
                  💡 <b>${esc(t('unscramble.explanation_label', 'Giải thích'))}:</b> ${esc(feedbackObj.rule)}
                </p>
              ` : ''}
            </div>
          `;
        }
      } else {
        sentenceDisplayHtml = `
          <div class="unscramble-sentence-box" id="sentence-box-${i}" style="min-height:58px; padding:12px 16px; border:2px dashed var(--border); border-radius:8px; display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:12px; background:rgba(0,0,0,0.01); transition:all 0.2s;">
            <span class="text-secondary italic">${esc(t('unscramble.drag_instruction', 'Bấm hoặc kéo các từ bên dưới vào đây...'))}</span>
          </div>
        `;
      }

      let chipsHtml = '';
      if (!isGraded) {
        chipsHtml = `
          <div class="drag-container" id="chips-container-${i}" style="margin-top:14px; display:flex; flex-wrap:wrap; gap:8px; padding:12px 0; min-height:48px; border-radius:8px; transition:all 0.2s;"></div>
        `;
      }

      return `
        <div class="${cardClass}" style="margin-bottom:24px; padding:16px; border:1px solid var(--border); border-radius:8px; background:var(--card-bg);">
          <p style="font-size:14.5px; color:var(--text-secondary); margin-bottom:10px; line-height:1.4;">${rawPromptText}</p>
          ${sentenceDisplayHtml}
          ${chipsHtml}
        </div>
      `;
    }).join('');

    let submitBtnHtml = '';
    if (isGraded) {
      submitBtnHtml = `
        <div class="result-summary-bar" style="margin-top:24px; padding:16px; background:var(--card-bg); border:1px solid var(--border); border-radius:8px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:16px; font-weight:700;">
            📊 Kết quả bài làm: <span style="font-size:20px; color:${score===x.questions.length?'var(--success)':'var(--primary)'}">${score}/${x.questions.length}</span> câu chính xác.
          </div>
          <button class="btn" id="story-new-btn">Tạo bài mới</button>
        </div>
      `;
    } else {
      submitBtnHtml = `
        <div class="text-right mt-5">
          <button class="btn" id="grade-unscramble" style="padding:10px 24px; font-weight:700;">Nộp bài & Chấm điểm</button>
        </div>
      `;
    }

    d.innerHTML = cardsHtml + submitBtnHtml;

    x.questions.forEach((q, i) => {
      if (!isGraded) {
        updateUnscrambleCardDOM(i, q);
      }
    });

    function updateUnscrambleCardDOM(qIdx, question) {
      const chosenBox = d.querySelector(`#sentence-box-${qIdx}`);
      const chipsBox = d.querySelector(`#chips-container-${qIdx}`);
      if (!chosenBox || !chipsBox) return;

      const chosen = state.answers?.[qIdx] || [];
      const shuffledArr = Array.isArray(question.shuffled_words) ? question.shuffled_words : (Array.isArray(question.words) ? question.words : []);
      const remainingWords = shuffledArr.filter((w, j) => {
        const timesInShuffled = shuffledArr.slice(0, j + 1).filter(x => x === w).length;
        const timesInChosen = chosen.filter(x => x === w).length;
        return timesInChosen < timesInShuffled;
      });

      if (chosen.length) {
        chosenBox.innerHTML = chosen.map((w, wIdx) =>
          `<button class="drag-word" draggable="true" data-back-idx="${wIdx}" style="padding:6px 12px; background:var(--primary); color:white; border:none; border-radius:4px; font-size:14px; font-weight:600; cursor:pointer; box-shadow:0 2px 4px rgba(0,0,0,0.08); transition:all 0.2s;">${esc(w)}</button>`
        ).join('');

        chosenBox.querySelectorAll('[data-back-idx]').forEach(btn => {
          btn.onclick = () => {
            const wIdx = +btn.dataset.backIdx;
            state.answers[qIdx].splice(wIdx, 1);
            updateUnscrambleCardDOM(qIdx, question);
          };
          btn.ondragstart = (e) => {
            unscrambleDragState = { qIdx, word: btn.textContent, type: 'chosen', index: +btn.dataset.backIdx };
            e.dataTransfer.effectAllowed = 'move';
          };
        });
      } else {
        chosenBox.innerHTML = '<span class="text-secondary italic">Bấm hoặc kéo các từ bên dưới vào đây...</span>';
      }

      chipsBox.innerHTML = remainingWords.map((w) =>
        `<button class="drag-word" draggable="true" data-word="${esc(w)}" style="padding:6px 12px; background:var(--card-bg); border:1px solid var(--border); border-radius:4px; font-size:14px; cursor:pointer; box-shadow:0 1px 3px rgba(0,0,0,0.05); transition:all 0.2s;">${esc(w)}</button>`
      ).join('');

      chipsBox.querySelectorAll('[data-word]').forEach(btn => {
        btn.onclick = () => {
          const word = btn.dataset.word;
          if (!state.answers) state.answers = {};
          if (!state.answers[qIdx]) state.answers[qIdx] = [];
          state.answers[qIdx].push(word);
          updateUnscrambleCardDOM(qIdx, question);
        };
        btn.ondragstart = (e) => {
          unscrambleDragState = { qIdx, word: btn.dataset.word, type: 'chip' };
          e.dataTransfer.effectAllowed = 'copy';
        };
      });

      chosenBox.ondragover = (e) => {
        if (unscrambleDragState && unscrambleDragState.qIdx === qIdx) {
          e.preventDefault();
          chosenBox.style.border = '2px dashed var(--primary)';
          chosenBox.style.background = 'rgba(54, 162, 235, 0.03)';
        }
      };
      chosenBox.ondragleave = () => {
        chosenBox.style.border = '2px dashed var(--border)';
        chosenBox.style.background = 'rgba(0,0,0,0.01)';
      };
      chosenBox.ondrop = (e) => {
        e.preventDefault();
        chosenBox.style.border = '2px dashed var(--border)';
        chosenBox.style.background = 'rgba(0,0,0,0.01)';
        if (!unscrambleDragState || unscrambleDragState.qIdx !== qIdx) return;

        if (unscrambleDragState.type === 'chip') {
          if (!state.answers) state.answers = {};
          if (!state.answers[qIdx]) state.answers[qIdx] = [];
          state.answers[qIdx].push(unscrambleDragState.word);
        } else if (unscrambleDragState.type === 'chosen') {
          const chosenArr = state.answers[qIdx] || [];
          const movedWord = chosenArr.splice(unscrambleDragState.index, 1)[0];

          const targetBtn = e.target.closest('[data-back-idx]');
          if (targetBtn) {
            const targetIdx = +targetBtn.dataset.backIdx;
            chosenArr.splice(targetIdx, 0, movedWord);
          } else {
            chosenArr.push(movedWord);
          }
        }
        updateUnscrambleCardDOM(qIdx, question);
        unscrambleDragState = null;
      };

      chipsBox.ondragover = (e) => {
        if (unscrambleDragState && unscrambleDragState.qIdx === qIdx && unscrambleDragState.type === 'chosen') {
          e.preventDefault();
          chipsBox.style.background = 'rgba(0,0,0,0.04)';
        }
      };
      chipsBox.ondragleave = () => {
        chipsBox.style.background = 'transparent';
      };
      chipsBox.ondrop = (e) => {
        e.preventDefault();
        chipsBox.style.background = 'transparent';
        if (!unscrambleDragState || unscrambleDragState.qIdx !== qIdx) return;

        if (unscrambleDragState.type === 'chosen') {
          state.answers[qIdx].splice(unscrambleDragState.index, 1);
          updateUnscrambleCardDOM(qIdx, question);
        }
        unscrambleDragState = null;
      };
    }

    if (!isGraded) {
      const gradeBtn = document.querySelector('#grade-unscramble');
      if (gradeBtn) {
        gradeBtn.onclick = async () => {
          const setBusy = window.setBusy || (() => {});
          const showBridgeFailure = window.showBridgeFailure || console.error;
          const getSignal = window.getSignal || (() => null);

          try {
            setBusy(true, t('unscramble.grading', 'Đang chấm bài bằng AI...'));
            const signal = getSignal();

            const levelEl = document.querySelector('#level');
            const levelVal = levelEl ? levelEl.value : 'intermediate';

            for (let i = 0; i < x.questions.length; i++) {
              if (signal?.aborted || !document.querySelector('#play')) return;
              const q = x.questions[i];
              const userAns = (state.answers?.[i] || []).join(' ');

              if (!userAns.trim()) {
                state.answers[`feedback_${i}`] = {
                  correct: false,
                  unanswered: true
                };
                continue;
              }

              const feedback = await Bridge.sendAsync('ai_grade', {
                gamemode: 'unscramble',
                level: levelVal,
                user_answer: userAns,
                expected: q.correct_sentence,
                correct_sentence: q.correct_sentence
              }, { signal });

              if (signal?.aborted || !document.querySelector('#play')) return;
              state.answers[`feedback_${i}`] = feedback;
            }

            state.isGraded = true;
            setBusy(false);

            let finalScore = 0;
            x.questions.forEach((q, i) => {
              if (state.answers[`feedback_${i}`]?.correct) finalScore++;
            });

            if (state.currentHistoryItem) {
              state.currentHistoryItem.answers = { ...state.answers };
              state.currentHistoryItem.score = finalScore;
            }
            if (window.HubPersistence && window.HubPersistence.saveHistory) {
              window.HubPersistence.saveHistory(state);
            } else if (typeof window.saveHistory === 'function') {
              window.saveHistory();
            }

            renderUnscrambleAll(x);
          } catch (e) {
            setBusy(false);
            showBridgeFailure(e);
          }
        };
      }
    } else {
      const newBtn = document.querySelector('#story-new-btn');
      if (newBtn) {
        newBtn.onclick = () => {
          if (typeof window.generate === 'function') window.generate(gameId);
        };
      }
    }
  }

  window.renderUnscrambleAll = renderUnscrambleAll;
  if (typeof window.GameRegistry !== 'undefined' && window.GameRegistry.register) {
    window.GameRegistry.register('unscramble', { render: renderUnscrambleAll });
  }
})();
