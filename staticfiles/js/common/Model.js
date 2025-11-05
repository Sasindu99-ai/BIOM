class Model {
    constructor(API_URL, csrfToken=null) {
        this.API_URL = API_URL;
        this.csrfToken = csrfToken;
    }

    // helper to normalize payloads
    _buildBody(data) {
        if (!data) return '';
        // if passed a string (pre-encoded)
        if (typeof data === 'string') return data;
        // if passed { payload: '...' }
        if (typeof data === 'object' && data.payload && typeof data.payload === 'string') {
            return data.payload;
        }
        // if plain object -> convert to urlencoded using global UTIL if available
        if (typeof data === 'object') {
            if (window.UTIL && typeof window.UTIL.objectToQueryString === 'function') {
                return window.UTIL.objectToQueryString(data);
            } else {
                // fallback: simple URLSearchParams
                return new URLSearchParams(data).toString();
            }
        }
        return '';
    }

    async callAPI(action, data) {
        const url = this.API_URL + encodeURI(action || '');
        const body = this._buildBody(data);
        let headers = {
          'Content-Type': 'application/json',
        };
        if (this.csrfToken) {
            headers['X-CSRF-Token'] = this.csrfToken;
        }

        const res = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: body
        });

        if (!res.ok) {
            // try to parse json error, otherwise throw text
            let errBody;
            try { errBody = await res.json(); } catch (e) { errBody = await res.text(); }
            const err = new Error('Network response was not ok');
            err.status = res.status;
            err.body = errBody;
            throw err;
        }

        // parse JSON (will throw if invalid)
        return await res.json();
    }

    async callAPP(action, data) {
        const url = this.API_URL + encodeURI(action || '');
        const body = this._buildBody(data);
        let headers = {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'Accept': 'application/json'
        };
        if (this.csrfToken) {
            headers['X-CSRF-Token'] = this.csrfToken;
        }

        const res = await fetch(url, {
            method: 'POST',
            headers: headers,
            credentials: 'same-origin',
            body: body
        });

        if (!res.ok) {
            let errBody;
            try { errBody = await res.text(); } catch (e) { errBody = ''; }
            const err = new Error('Network response was not ok');
            err.status = res.status;
            err.body = errBody;
            throw err;
        }

        return await res.text();
    }
}

window.Model = Model;
