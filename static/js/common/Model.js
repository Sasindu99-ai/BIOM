export default class Model {
    constructor(API_URL) {
        this.API_URL = API_URL;
    }

    callAPI(action, data) {
        return $.ajax({
            url: this.API_URL + encodeURI(action),
            type: 'POST',
            dataType: 'json',
            data: data,
            timeout: 5000
        });
    }

    callAPP(action, data) {
        return $.ajax({
            url: this.API_URL + encodeURI(action),
            type: 'POST',
            dataType: 'html',
            data: data,
            timeout: 5000
        });
    }
}