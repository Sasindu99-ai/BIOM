/** @format */

export default class Update {
    controller;

    constructor(API_URL) {
        this.import(`${window.STATICS}js/controller/UserController.js`).then(UserController => {
            this.controller = new UserController.default(API_URL);
        });
        window.update = this;
    }

    async import(js, version=1)
    {
        return await import(js + "?v=" + version);
    }

    example() {
        this.controller.example(this.onExample);
    }

    onExample(api_report) {
        console.log("[EXAMPLE]", api_report);
    }
}
