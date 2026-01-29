
export default class Steps {
    id;
    options = {
    };
    validate = {
    };

    init(id) {
        this.id = id;

        this.element = $(`#${this.id}`);
        this.form = this.element.show();

        this.element.steps(this.options);
        this.form.validate(this.validate);

        return this.element;
    }

    constructor(id=null, options=null, validate=null) {
        if (!$().steps) {
            console.warn('Warning - steps.min.js is not loaded.');
            return;
        }
        if (!$().validate) {
            console.warn('Warning - validate.min.js is not loaded.');
            return;
        }

        if (options !== null) {
            this.options = options;
        }
        if (validate !== null) {
            this.validate = validate;
        }

        if (id !== null) {
            return this.init(id);
        }
    }
}