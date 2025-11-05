export default class DatePicker {
    id;
    options = {
        parentEl: 'main'
    };
    date = new Date();
    callback = (date) => {
        this.date = date;
    };

    init(id) {
        this.id = id;

        this.element = document.getElementById(this.id);
        this.picker = new Datepicker(
            this.element,
            this.options
        );
        this.element.addEventListener('changeDate', (e) => {
            this.callback(e.detail.date);
        });

        return this;
    }

    constructor(id=null, options=null, callback=null) {
        if (options !== null) {
            this.options = options;
        }
        if (callback !== null) {
            this.callback = callback;
        }

        if (id !== null) {
            return this.init(id);
        }
    }
}