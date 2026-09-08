/**
 * Home page & API tester module.
 */
(() => {
  const esc = s => (typeof window.esc === 'function' ? window.esc(s) : String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const t = (key, fallback, ...args) => (typeof window.t === 'function' ? window.t(key, fallback, ...args) : (fallback || key));

  function getGameDesc(id) {
    const m = {
      fill_blank: t('desc.fill_blank', 'Điền từ vào chỗ trống trong câu'),
      cloze: t('desc.cloze', 'Điền từ vào đoạn văn có chỗ trống'),
      translation: t('desc.translation', 'Dịch câu từ tiếng Việt sang ngoại ngữ'),
      unscramble: t('desc.unscramble', 'Sắp xếp từ thành câu hoàn chỉnh'),
      matching: t('desc.matching', 'Nối từ với định nghĩa tương ứng'),
      story: t('desc.story', 'Đọc truyện và trả lời câu hỏi'),
      sentence_transform: t('desc.sentence_transform', 'Biến đổi câu theo yêu cầu ngữ pháp'),
      taboo: t('desc.taboo', 'Đoán từ qua mô tả (không dùng từ cấm)')
    };
    return m[id] || t('desc.default', 'Luyện tập tương tác');
  }

  function home() {
    const games = window.HubGames || [
      ['fill_blank', '✏️', 'Điền từ'],
      ['cloze', '📝', 'Cloze'],
      ['translation', '🌐', 'Dịch câu'],
      ['unscramble', '🔤', 'Sắp xếp từ'],
      ['matching', '🔗', 'Nối từ'],
      ['story', '📖', 'Đọc truyện'],
      ['sentence_transform', '🔄', 'Biến đổi câu'],
      ['taboo', '🤫', 'Taboo']
    ];

    const manifestList = (typeof window.ManifestClient !== 'undefined' && window.ManifestClient.getAllManifests)
      ? window.ManifestClient.getAllManifests()
      : games.map(g => ({ id: g[0], icon: g[1], default_title: g[2] }));

    const shell = window.shell || (body => {
      const el = document.querySelector('#app');
      if (el) el.innerHTML = body;
    });

    shell('<main class="container"><div class="header pt-header"><h1>' + esc(t('app.title', 'AI Learning Hub')) + '</h1><p>' + esc(t('app.home_subtitle', 'Chọn một game để học từ bộ thẻ Anki')) + '</p><div class="api-check"><button class="btn btn-outline" id="test-keys">' + esc(t('app.test_api', 'Kiểm tra API')) + '</button><span id="api-result" aria-live="polite"></span></div></div><div class="game-grid">' + manifestList.map(g => '<button class="game-card" data-game="' + g.id + '"><div class="icon">' + g.icon + '</div><h3>' + esc(t(g.id + '.title', g.default_title || g.id)) + '</h3><p>' + esc(getGameDesc(g.id)) + '</p></button>').join('') + '</div></main>');

    if (typeof window.bindCommon === 'function') window.bindCommon();
    document.querySelectorAll('[data-game]').forEach(e => {
      e.onclick = () => {
        if (typeof window.nav === 'function') window.nav(e.dataset.game);
      };
    });
    const testKeysBtn = document.querySelector('#test-keys');
    if (testKeysBtn) testKeysBtn.onclick = testKeys;
  }

  async function testKeys() {
    const button = document.querySelector('#test-keys');
    const out = document.querySelector('#api-result');
    if (typeof window.abortActiveRequests === 'function') window.abortActiveRequests();
    const getSignal = window.getSignal || (() => null);
    const setBusy = window.setBusy || (() => {});
    const showBridgeFailure = window.showBridgeFailure || console.error;
    const signal = getSignal();

    try {
      if (button) {
        button.innerHTML = '<span class="button-spinner"></span> ' + esc(t('app.testing_api', 'Đang kiểm tra…'));
        button.disabled = true;
      }
      setBusy(true, t('app.testing_api_status', 'Đang kiểm tra API…'));
      const data = await Bridge.sendAsync('test_all_keys', {}, { signal });
      if (signal?.aborted || data?.cancelled) {
        if (out) {
          out.innerHTML = `<span class="badge-status-warn" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:16px; background:rgba(234,179,8,0.12); color:#ca8a04; font-weight:600; font-size:13px; margin-top:8px;">⚠️ ${esc(t('app.action_cancelled', 'Đã hủy kiểm tra API'))}</span>`;
        }
        return;
      }
      const results = data.results || [];
      const okCount = results.filter(item => item.ok).length;
      const totalCount = results.length;
      const rateLimited = results.some(item => item.error_code === 'E_RATE_LIMIT');
      if (out) {
        if (okCount > 0) {
          out.innerHTML = `<span class="badge-status-ok" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:16px; background:rgba(34,197,94,0.12); color:#16a34a; font-weight:600; font-size:13px; margin-top:8px;">🟢 ${okCount}/${totalCount} API Key hoạt động (OK)</span>`;
        } else if (rateLimited) {
          out.innerHTML = `<span class="badge-status-warn" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:16px; background:rgba(234,179,8,0.12); color:#ca8a04; font-weight:600; font-size:13px; margin-top:8px;">🟡 API bận/vượt quá giới hạn (429) - Vui lòng đợi 30s</span>`;
        } else if (totalCount > 0) {
          out.innerHTML = `<span class="badge-status-err" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:16px; background:rgba(239,68,68,0.12); color:#dc2626; font-weight:600; font-size:13px; margin-top:8px;">🔴 0/${totalCount} API Key hoạt động</span>`;
        } else {
          out.innerHTML = `<span class="badge-status-warn" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:16px; background:rgba(234,179,8,0.12); color:#ca8a04; font-weight:600; font-size:13px; margin-top:8px;">⚠️ Chưa cấu hình API Key</span>`;
        }
      }
    } catch(e) {
      if (e.name === 'AbortError' || e.error_code === 'E_ABORTED') {
        if (out) {
          out.innerHTML = `<span class="badge-status-warn" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:16px; background:rgba(234,179,8,0.12); color:#ca8a04; font-weight:600; font-size:13px; margin-top:8px;">⚠️ ${esc(t('app.action_cancelled', 'Đã hủy kiểm tra API'))}</span>`;
        }
        return;
      }
      showBridgeFailure(e);
    } finally {
      if (button) {
        button.innerHTML = esc(t('app.test_api', 'Kiểm tra API'));
        button.disabled = false;
      }
      setBusy(false);
    }
  }

  window.HubHome = {
    home,
    getGameDesc,
    testKeys
  };

  window.home = home;
  window.getGameDesc = getGameDesc;
  window.testKeys = testKeys;
})();
