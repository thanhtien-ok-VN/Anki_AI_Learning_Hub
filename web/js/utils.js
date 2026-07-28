const Utils = {
    __: {},

    async initI18n() {
        for (let i = 0; i < 100; i++) {
            const res = await Bridge.sendAsync('get_ui_strings').catch(() => null);
            if (res && res.strings && Object.keys(res.strings).length > 0) {
                this.__ = res.strings;
                break;
            }
            await new Promise(r => setTimeout(r, 200));
        }
        this.renderI18n();
    },

    t(key, fallback = '', ...args) {
        let text = this.__[key];
        let params = args;
        let defaultText = fallback;

        if (typeof fallback !== 'string') {
            params = [fallback, ...args];
            defaultText = key;
        }

        text = text || defaultText || key;

        if (params.length > 0) {
            if (typeof params[0] === 'object' && params[0] !== null && !Array.isArray(params[0])) {
                const obj = params[0];
                Object.keys(obj).forEach(k => {
                    text = text.replace(new RegExp('\\{' + k + '\\}', 'g'), obj[k]);
                });
            } else {
                params.forEach((val, idx) => {
                    text = text.replace(new RegExp('\\{' + idx + '\\}', 'g'), val ?? '');
                });
            }
        }
        return text;
    },

    renderI18n() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = this.t(key);
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = text;
            } else {
                el.textContent = text;
            }
        });
    },

    shuffle(arr) {
        const a = [...arr];
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    },

    toast(msg, duration = 2500) {
        const el = document.createElement('div');
        el.className = 'toast';
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), duration);
    },

    getParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    },

    goTo(page) {
        // Legacy game pages delegate to the SPA router when it is present.
        // This deliberately avoids a document navigation inside AnkiWebView.
        const route = String(page).replace(/\.html$/, '');
        if (window.App && typeof window.App.navigate === 'function') {
            window.App.navigate(route === 'index' ? 'home' : route);
        }
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    debounce(fn, delay = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    },

    formatTime(seconds) {
        const m = String(Math.floor(seconds / 60)).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');
        return `${m}:${s}`;
    },

    loadConfig(gamemode) {
        try {
            const data = localStorage.getItem(`aihub_config_${gamemode}`);
            return data ? JSON.parse(data) : {};
        } catch {
            return {};
        }
    },

    saveConfig(gamemode, config) {
        localStorage.setItem(`aihub_config_${gamemode}`, JSON.stringify(config));
    },

    showLoading(show = true) {
        const el = document.getElementById('loading');
        if (el) el.style.display = show ? 'block' : 'none';
    },

    showGameContent(show = true) {
        const el = document.getElementById('game-content');
        if (el) el.style.display = show ? 'block' : 'none';
    },

    enableButton(id, enabled = true) {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = !enabled;
    },
};

window.Utils = Utils;
window.t = Utils.t.bind(Utils);
