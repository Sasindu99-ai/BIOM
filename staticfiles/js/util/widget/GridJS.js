export default class GridJS {
    gridJSElement = null;
    gridJS = null;
    headers = [];
    data = []
    footers = [];
    options = {
        sort: false,
        resizable: false,
        search: false,
        pagination: false,
        className: {
            table: "table"
        }
    }

    async init(id) {
        this.gridJSElement = document.getElementById(id);
        if (this.gridJSElement != null) {
            this.gridJS = new gridjs.Grid({
                className: this.options['className'],
                sort: this.options['sort'],
                resizable: this.options['resizable'],
                search: this.options['search'],
                pagination: this.options['pagination'],
                columns: this.headers,
                data: this.data
            });
            this.gridJS.render(this.gridJSElement);
            return this.gridJS;
        }
        return null;
    }

    constructor(id=null, headers=[], data=[], footers=[], options={}) {
        if (typeof gridjs == "undefined") {
            console.warn('Warning - Failed to load grid table.');
            return;
        }

        if (id !== null) {
            for (let i=0; i < headers.length; i++) {
                if (headers[i].hasOwnProperty("formatter")) {
                    if (typeof headers[i].formatter === "string" && headers[i].formatter.includes('{cell}')) {
                        let formatter = headers[i].formatter;
                        headers[i].formatter = (cell) => gridjs.html(formatter.replace('{cell}', `${cell}`))
                    }
                }
            }
            this.headers = headers;
            this.data = data;
            for (let i=0; i < footers.length; i++) {
                if (footers[i].hasOwnProperty("formatter")) {
                    if (typeof footers[i].formatter === "string" && footers[i].formatter.includes('{cell}')) {
                        let formatter = headers[i].formatter;
                        footers[i].formatter = (cell) => gridjs.html(formatter.replace('{cell}', `${cell}`))
                    }
                }
            }
            this.footers = footers;
            Object.keys(options).forEach(key => {
                this.options[key] = options[key];
            })
            return this.init(id)
        }
    }
}
