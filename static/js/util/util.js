class Util {
    constructor(secretKey='secret-key')
    {
        this.secretKey = secretKey;
        document.addEventListener("DOMContentLoaded", function () {
            // UTIL.import(`${STATICS}js/util/vendor/forms/validation/validation.js`);
            UTIL.import(`${STATICS}js/util/validate.js`).then(validate => { window.VALIDATE = new validate.default(); });
            UTIL.initWidgets();
        });
    }

    async import(js, version=1)
    {
        return await import(js + "?v=" + version);
    }

    initWidgets()
    {
        this.import(`${STATICS}js/util/widget/AutoComplete.js`, 4).then(autoComplete => {
            this.AutoComplete = autoComplete.default;
            this.initAutoComplete();
        });
        this.import(`${STATICS}js/util/widget/AutoComplete2.js`, 4).then(autoComplete => {
            this.AutoComplete2 = autoComplete.default;
            this.initAutoComplete2();
        });
        this.import(`${STATICS}js/util/widget/GridJS.js`, 3).then(gridJS => {
            this.GridJS = gridJS.default;
        });
        this.import(`${STATICS}js/util/widget/DataTable.js`, 7).then(dataTable => {
            this.DataTable = dataTable.default;
        });
        this.import(`${STATICS}js/util/widget/DateRangePicker.js`, 1).then(dateRangePicker => {
            this.DateRangePicker = dateRangePicker.default;
        });
        this.import(`${STATICS}js/util/widget/DatePicker.js`, 1).then(datePicker => {
            this.DatePicker = datePicker.default;
        });
        this.import(`${STATICS}js/util/widget/Slider.js`, 4).then(slider => {
            this.Slider = slider.default;
            this.initSlider();
        });
        this.import(`${STATICS}js/util/widget/Toast.js`, 2).then(toast => {
            this.Toast = toast.default;
        })
        this.import(`${STATICS}js/util/widget/FileUploader.js`, 1).then(fileUploader => {
            this.FileUploader = fileUploader.default;
        })
        this.import(`${STATICS}js/util/widget/Steps.js`, 1).then(steps => {
            this.Steps = steps.default;
        });
        // this.import(`${STATICS}js/util/widget/NoUiSlider.js`, 1).then(noUiSlider => {
        //     this.NoUiSlider = noUiSlider.default;
        // });
        setTimeout(this.handleEvents, 100);
    }

    initAutoComplete()
    {
        let autoCompleteElements = document.getElementsByClassName("auto-complete");
        for (let i=0; i < autoCompleteElements.length; i++) {
            new this.AutoComplete(autoCompleteElements[i].getAttribute("id"));
        }
    }

    initAutoComplete2()
    {
        let autoCompleteElements = document.getElementsByClassName("auto-complete-2");
        for (let i=0; i < autoCompleteElements.length; i++) {
            new this.AutoComplete2(autoCompleteElements[i]);
        }
    }

    initSlider() {
        let sliderElements = document.getElementsByClassName("slider");
        for (let i=0; i < sliderElements.length; i++) {
            new this.Slider(sliderElements[i].getAttribute("id"));
        }
    }

    handleEvents()
    {
        document.addEventListener('click', function(event) {
            if (!event.target.matches('.auto-complete-input')) {
                let ulElements = document.getElementsByClassName("auto-complete-menu");

                for (let i=0; i < ulElements.length; i++) {
                    ulElements[i].style.display = "none";
                }
            }
        });
    }

    header(to)
    {
        if (!to.startsWith('https://') && !to.startsWith('http://')) {
            window.location.assign(ROOTPATH + to);
        } else {
            window.location.assign(to);
        }
    }

    formJson(data) {
        let jsonData = {};

        for (let [key, value] of data.entries()) {
            let keys = key.split(/[\[\]]+/).filter(part => part !== "");
            let lastKey = keys.pop();
            let currentLevel = jsonData;
            keys.forEach((k, index) => {
                if (!currentLevel[k]) {
                    if (keys[index + 1] && !isNaN(keys[index + 1])) {
                        currentLevel[k] = [];
                    } else {
                        currentLevel[k] = {};
                    }
                }
                currentLevel = currentLevel[k];
            });
            if (Array.isArray(currentLevel)) {
                currentLevel.push(value);
            } else if (lastKey === "") {
                if (!Array.isArray(currentLevel)) {
                    currentLevel = [];
                }
                currentLevel.push(value);
            } else {
                if (key.endsWith("[]")) {
                    if (!currentLevel[lastKey]) {
                        currentLevel[lastKey] = [];
                    }
                    currentLevel[lastKey].push(value);
                } else {
                    currentLevel[lastKey] = value;
                }
            }
        }
        return jsonData;
    }

    objectToQueryString(obj) {
        let params = new URLSearchParams();
        for (let key in obj) {
            if (obj.hasOwnProperty(key)) {
                if (typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
                    // Handle nested objects
                    for (let nestedKey in obj[key]) {
                        if (obj[key].hasOwnProperty(nestedKey)) {
                            params.append(`${key}[${nestedKey}]`, obj[key][nestedKey]);
                        }
                    }
                } else if (Array.isArray(obj[key])) {
                    // Handle arrays
                    obj[key].forEach((value, index) => {
                        params.append(`${key}[]`, value);
                    });
                } else {
                    // Handle other types
                    params.append(key, obj[key]);
                }
            }
        }
        return params.toString();
    }

    empty(value)
    {
        return typeof value === "undefined" || value === null || value.trim() === "";
    }

    encode(value) {
        return CryptoJS.AES.encrypt(value, this.secretKey).toString();
    }

    decode(value) {
        return CryptoJS.AES.decrypt(value, this.secretKey).toString(CryptoJS.enc.Utf8);
    }

    formatCurrency(amount, currency = 'LKR', locale = 'en-US') {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    parseData(rawData) {
        try {
            // rawData: String
            let decodedData = rawData.replace(/\\u0027/g, "'");
            decodedData = decodedData.replace(/\\u0022/g, '"');
            decodedData = decodedData
                .replace(/None/g, 'null')
                .replace(/True/g, 'true')
                .replace(/False/g, 'false');
            decodedData = decodedData.replace(/'([^']+)'/g, '"$1"');
            decodedData = decodeURIComponent(decodedData);
            return JSON.parse(decodedData);
        } catch (e) {
            console.error(e);
            return false;
        }
    }

    encodeData(jsonObject) {
        try {
            // Convert JSON to string
            let encodedData = JSON.stringify(jsonObject);

            // Reverse the transformations in parseData
            encodedData = encodedData.replace(/"/g, "\\u0022");  // Escape double quotes
            encodedData = encodedData.replace(/'/g, "\\u0027");  // Escape single quotes
            encodedData = encodedData
                .replace(/\bnull\b/g, "None")    // Convert null -> None
                .replace(/\btrue\b/g, "True")    // Convert true -> True
                .replace(/\bfalse\b/g, "False"); // Convert false -> False

            // Encode URI components
            return encodeURIComponent(encodedData);
        } catch (e) {
            console.error("Encoding Error:", e);
            return false;
        }
    }

    formatDate(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }

    formatDateTime(dateTimeString) {
        let parts = dateTimeString.split(/[\s,/:]+/);

        if (parts.length < 6) {
            console.error("Invalid date format:", dateTimeString);
            return "Invalid Date";
        }

        let [day, month, year, hour, minute, second] = parts.map(Number);

        // Create a Date object (ensure UTC conversion)
        let dateTime = new Date(Date.UTC(year, month - 1, day, hour, minute, second));

        if (isNaN(dateTime.getTime())) {
            console.error("Invalid Date after parsing:", dateTimeString);
            return "Invalid Date";
        }

        return dateTime.toLocaleString('en-US', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', second: '2-digit',
            hour12: true
        });
    }
}


let publicSecretKey = document.querySelector('meta[name="public-secret-key"]').content;
window.UTIL = new Util(publicSecretKey);
