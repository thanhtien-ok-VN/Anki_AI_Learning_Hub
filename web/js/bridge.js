/* Polyfill pycmd for web browser environments outside Anki Qt */
if (typeof window.pycmd !== 'function') {
    window.pycmd = function(rawMessage, callback, signal) {
        let msg;
        try {
            msg = typeof rawMessage === 'string' ? JSON.parse(rawMessage) : rawMessage;
        } catch (e) {
            callback({ success: false, data: {}, error_code: 'E_BRIDGE_PARSE', message: e.message });
            return;
        }
        fetch('/api/bridge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(msg),
            signal: signal || undefined
        })
        .then(res => res.json())
        .then(data => callback(data))
        .catch(err => {
            if (err && err.name === 'AbortError') {
                callback({ success: false, data: {}, error_code: 'E_ABORTED', message: 'Request aborted' });
            } else {
                callback({ success: false, data: {}, error_code: 'E_BRIDGE_NETWORK', message: err.message });
            }
        });
    };
}

/* A dependable pycmd client for an AnkiWebView served by the media server. */
const Bridge = {
    _ready: false,
    _sequence: 0,
    _queue: [],
    _pending: new Map(),

    _requestId() { return `aihub-${Date.now()}-${++this._sequence}`; },

    _normalise(raw) {
        if (typeof raw === 'string') {
            try { return JSON.parse(raw); } catch (_) { return { success: false, data: {}, error_code: 'E_BRIDGE_PARSE', message: raw }; }
        }
        return raw || { success: false, data: {}, error_code: 'E_EMPTY_RESPONSE', message: 'No response from Anki.' };
    },

    hostReady() {
        this._ready = typeof pycmd === 'function';
        if (this._ready) this._flush();
    },

    _waitForPycmd() {
        if (typeof pycmd === 'function') { this.hostReady(); return; }
        window.setTimeout(() => this._waitForPycmd(), 50);
    },

    _flush() {
        const queued = this._queue.splice(0);
        queued.forEach(item => this._dispatch(item));
    },

    _dispatch(item) {
        try {
            pycmd(JSON.stringify(item.message), raw => {
                const result = this._normalise(raw);
                if (result?.data?.pending) return;
                this._settle(item.id, result);
            }, item.signal);
        } catch (error) {
            this._settle(item.id, { success: false, data: {}, error_code: 'E_PYCMD', message: error.message });
        }
    },

    _settle(id, result) {
        const pending = this._pending.get(id);
        if (!pending) return;
        this._pending.delete(id);
        window.clearTimeout(pending.timeout);
        if (pending.abortHandler && pending.signal) {
            try { pending.signal.removeEventListener('abort', pending.abortHandler); } catch (_) {}
        }
        if (result?.success) {
            window.dispatchEvent(new CustomEvent('aihub:bridge-success'));
            pending.resolve(result.data);
        } else {
            const err = Object.assign(new Error(result?.message || 'Anki request failed'), result || {});
            if (result?.error_code === 'E_ABORTED') {
                err.name = 'AbortError';
            }
            pending.reject(err);
        }
    },

    complete(id, result) { this._settle(id, this._normalise(result)); },

    abortAll() {
        this._queue = [];
        for (const [id] of this._pending.entries()) {
            this._settle(id, { success: false, data: {}, error_code: 'E_ABORTED', message: 'Request aborted' });
        }
    },

    sendAsync(action, data = {}, opts = 90000) {
        let timeoutMs = 90000;
        let signal = null;

        if (typeof opts === 'number') {
            timeoutMs = opts;
        } else if (opts && typeof opts === 'object') {
            if (opts.timeoutMs !== undefined) timeoutMs = opts.timeoutMs;
            if (opts.signal !== undefined) signal = opts.signal;
        } else if (opts && typeof opts === 'string') {
            timeoutMs = parseInt(opts, 10) || 90000;
        }

        const id = this._requestId();
        return new Promise((resolve, reject) => {
            if (signal && signal.aborted) {
                const err = new Error('Request aborted');
                err.name = 'AbortError';
                err.error_code = 'E_ABORTED';
                return reject(err);
            }

            const timeout = window.setTimeout(() => this._settle(id, {
                success: false, data: {}, error_code: 'E_TIMEOUT', message: 'The Anki task took too long.'
            }), timeoutMs);

            let abortHandler = null;
            if (signal) {
                abortHandler = () => {
                    const qIdx = this._queue.findIndex(item => item.id === id);
                    if (qIdx !== -1) this._queue.splice(qIdx, 1);
                    this._settle(id, { success: false, data: {}, error_code: 'E_ABORTED', message: 'Request aborted' });
                };
                signal.addEventListener('abort', abortHandler, { once: true });
            }

            this._pending.set(id, { resolve, reject, timeout, signal, abortHandler });
            const item = { id, message: { action, data, request_id: id }, signal };
            if (this._ready && typeof pycmd === 'function') this._dispatch(item);
            else this._queue.push(item);
        });
    },

    send(action, data = {}, opts = 90000) { return this.sendAsync(action, data, opts).catch(error => console.warn('[Bridge]', error)); },

    updateStatus(text) {
        const loadingText = document.querySelector('#loading-text');
        if (loadingText && text) {
            loadingText.textContent = text;
        }
    },

    init() { this._waitForPycmd(); },
};

window.Bridge = Bridge;
Bridge.init();
