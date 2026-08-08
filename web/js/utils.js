const Utils = {
    __: {},

    async initI18n() {
        for (let i = 0; i < 3; i++) {
            const res = await Bridge.sendAsync('get_ui_strings', {}, 1500).catch(() => null);
            if (res && res.strings && Object.keys(res.strings).length > 0) {
                this.__ = res.strings;
                this.currentLang = res.lang || 'en';
                break;
            }
            await new Promise(r => setTimeout(r, 100));
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

    getParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    },

    goTo(page) {
        const route = String(page).replace(/\.html$/, '');
        if (window.App && typeof window.App.navigate === 'function') {
            window.App.navigate(route === 'index' ? 'home' : route);
        }
    }
};

window.Utils = Utils;
window.t = Utils.t.bind(Utils);
