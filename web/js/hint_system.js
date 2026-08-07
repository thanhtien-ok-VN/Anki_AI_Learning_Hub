/**
 * Multilingual 3-Tier Hint System for Anki AI Learning Hub
 * Handles 3 hint levels across 8 gamemodes without hardcoded strings.
 */
(function(window) {
  'use strict';

  const HintSystem = {
    hintLevels: {}, // Tracks hint levels per question index: { qIdx: level }

    reset: function() {
      this.hintLevels = {};
    },

    requestHint: async function(gamemode, questionData, qIdx, textEl, hintBtn) {
      if (!textEl) return;

      if (!this.hintLevels[qIdx]) {
        this.hintLevels[qIdx] = 0;
      }
      this.hintLevels[qIdx] += 1;
      const currentLevel = this.hintLevels[qIdx];

      try {
        // Call backend Bridge for hint data if available
        let hintData = null;
        if (window.Bridge && typeof window.Bridge.sendAsync === 'function') {
          try {
            hintData = await window.Bridge.sendAsync('get_hint', {
              gamemode: gamemode,
              question_data: questionData,
              hint_level: currentLevel
            });
          } catch (_) {}
        }

        // Render multi-level hint HTML
        let titleText = '';
        let hintBodyHtml = '';

        if (hintData && hintData.content) {
          titleText = hintData.hint_title || window.t('hint.hint_btn', '💡 Gợi ý');
          hintBodyHtml = window.esc(hintData.content);
        } else {
          // Client-side Fallback 3-Tier Rendering
          const secretWord = (questionData.target_word || questionData.answer || questionData.expected_answer || questionData.correct_sentence || '').trim();
          const meaningText = (questionData.meaning || questionData.full_translation || '').trim();
          const grammarText = (questionData.grammar_note || questionData.grammar_rule || '').trim();

          if (currentLevel === 1) {
            titleText = window.t('hint.level_1', 'Cấp 1: Cấu trúc & Ngữ pháp');
            if (grammarText) {
              hintBodyHtml = `📌 <b>${window.esc(window.t('hint.grammar_structure', 'Quy tắc ngữ pháp: {0}', grammarText))}</b>`;
            } else if (secretWord) {
              hintBodyHtml = `📏 <b>${window.esc(window.t('hint.word_length', 'Độ dài từ: {0} ký tự', secretWord.length))}</b>`;
            } else {
              hintBodyHtml = `💡 <b>${window.esc(window.t('hint.structure_tip', 'Hãy chú ý đến cấu trúc ngữ pháp và ngữ cảnh câu.'))}</b>`;
            }
          } else if (currentLevel === 2) {
            titleText = window.t('hint.level_2', 'Cấp 2: Ký tự đầu & Nghĩa');
            const hintsArr = [];
            if (secretWord) {
              hintsArr.push(`🔤 <b>${window.esc(window.t('hint.starts_with', 'Chữ cái đầu: {0}', secretWord.charAt(0).toUpperCase()))}</b>`);
            }
            if (meaningText) {
              hintsArr.push(`📖 <b>${window.esc(window.t('hint.meaning_label', 'Nghĩa: {0}', meaningText))}</b>`);
            }
            hintBodyHtml = hintsArr.join('<br>');
          } else {
            titleText = window.t('hint.level_3', 'Cấp 3: Đáp án chuẩn (0 điểm)');
            hintBodyHtml = `🎯 <b>${window.esc(window.t('feedback.answer_label_short', 'Đáp án'))}:</b> <code style="font-size:15px; font-weight:700;">${window.esc(secretWord)}</code>`;
            if (hintBtn) {
              hintBtn.disabled = true;
              hintBtn.style.opacity = '0.5';
            }
          }
        }

        textEl.style.display = 'block';
        textEl.style.textAlign = 'left';
        textEl.style.width = '100%';
        textEl.style.boxSizing = 'border-box';

        textEl.innerHTML = `
          <div class="hint-container" style="text-align: left !important;">
            <div style="font-size: 12.5px; font-weight: 700; color: var(--color-warn-dark, #b58105); margin-bottom: 4px;">
              ${window.esc(titleText)}
            </div>
            <div style="font-size: 13.5px; color: var(--text-primary); line-height: 1.5;">
              ${hintBodyHtml}
            </div>
          </div>
        `;

        // Log event
        if (window.Bridge && typeof window.Bridge.sendAsync === 'function') {
          window.Bridge.sendAsync('log_event', {
            phase: 'HINT',
            message: `User requested level ${currentLevel} hint for ${gamemode} q_idx=${qIdx}`
          }).catch(() => {});
        }
      } catch (err) {
        console.error('Error rendering hint:', err);
      }
    }
  };

  window.HintSystem = HintSystem;
})(window);
