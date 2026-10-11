class Api {
    model;
    modal;

    constructor(API_URL) {
        import(`${window.STATICS}js/common/Model.js?v=2`).then((module) => {
            const ModelClass = module.default || module.Model || window.Model;
            if (typeof ModelClass === 'function') {
                this.model = new ModelClass(API_URL);
                this.modal = new ModelClass(ROOTPATH);
            }
        }).catch(err => {
            console.warn('Could not load Model:', err);
        });
    }

    load(action)
    {
        let data = {
            "load": "true"
        };
        return this.modal.callAPP(action, data);
    }

    subscribe(id) {
        let form = document.getElementById(id);
        let data = form.fromJSON();
        let result =  this.model.callAPI("general/subscribe", data);
        console.log(result);
    }

    loadCabHires(start, count, searchText) {
        // if (start % count !== 0) {
        //     return;
        // }

        return this.model.callAPI("api/v1/cab-hire/filter", data);
    }
}

window.API = new Api(ROOTPATH + "api/");
