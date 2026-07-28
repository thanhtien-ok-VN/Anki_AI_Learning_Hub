/* Polyfill pycmd for web browser environments outside Anki Qt */
if (typeof window.pycmd !== 'function') {
    window.pycmd = function(rawMessage, callback) {
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
            body: JSON.stringify(msg)
        })
        .then(res => res.json())
        .then(data => callback(data))
        .catch(err => callback({ success: false, data: {}, error_code: 'E_BRIDGE_NETWORK', message: err.message }));
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
            });
        } catch (error) {
            this._settle(item.id, { success: false, data: {}, error_code: 'E_PYCMD', message: error.message });
        }
    },

    _settle(id, result) {
        const pending = this._pending.get(id);
        if (!pending) return;
        this._pending.delete(id);
        window.clearTimeout(pending.timeout);
        result?.success ? pending.resolve(result.data) : pending.reject(Object.assign(new Error(result?.message || 'Anki request failed'), result || {}));
    },

    complete(id, result) { this._settle(id, this._normalise(result)); },

    sendAsync(action, data = {}, timeoutMs = 90000) {
        const id = this._requestId();
        return new Promise((resolve, reject) => {
            const timeout = window.setTimeout(() => this._settle(id, {
                success: false, data: {}, error_code: 'E_TIMEOUT', message: 'The Anki task took too long.'
            }), timeoutMs);
            this._pending.set(id, { resolve, reject, timeout });
            const item = { id, message: { action, data, request_id: id } };
            if (this._ready && typeof pycmd === 'function') this._dispatch(item);
            else this._queue.push(item);
        });
    },

    send(action, data = {}) { return this.sendAsync(action, data).catch(error => console.warn('[Bridge]', error)); },

    init() { this._waitForPycmd(); },
};

window.Bridge = Bridge;
Bridge.init();
