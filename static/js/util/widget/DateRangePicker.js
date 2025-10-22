export default class DateRangePicker {
    id;
    options = {
        parentEl: 'main'
    };
    startDate = null;
    endDate = null;
    picker = null;
    callback = (start, end) => {
        this.startDate = start;
        this.endDate = end;
    };

    init(id) {
        this.id = id;

        this.picker = $(`#${this.id}`).daterangepicker(
            this.options,
            this.callback
        );

        return this;
    }

    constructor(id=null, options=null, callback=null) {
        if (!$().daterangepicker) {
            console.warn('Warning - daterangepicker.js is not loaded.');
            return;
        }

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