export default class AutoComplete
{
    inputElement = null;
    ulElement = null;
    errorElement = null;
    data = {};

    constructor(element)
    {
        this.inputElement = element.getElementsByTagName("input")[0];
        this.ulElement = element.getElementsByTagName("ul")[0];
        this.errorElement = element.getElementsByTagName("span")[0];

        this.inputElement.onclick = () => this.searchAndSelect();
        this.inputElement.oninput = () => this.searchAndSelect();
        this.inputElement.onmouseleave = () => this.validate();

        this.extractData();
    }

    extractData()
    {
        let dataElements = this.ulElement.getElementsByTagName("li");
        for (let i=0; i < dataElements.length; i++) {
            this.data[dataElements[i].innerText] = dataElements[i].getAttribute("value");
        }
    }

    searchAndSelect()
    {
        // get search text
        let text = this.inputElement.value.toLowerCase();
        const searchText = text.replace(/\+/g, "");

        // clear UL & Error
        this.ulElement.innerHTML = "";
        this.errorElement.innerText = "";

        let filteredOptions;
        if (searchText === "") {
            filteredOptions = Object.keys(this.data);
        } else {
            // filter data
            filteredOptions = Object.keys(this.data).filter(key => {
                return key.toLowerCase().includes(searchText);
            });
        }

        // show data list
        filteredOptions.forEach(key => {
            const option = document.createElement('li');
            option.textContent = key;
            option.dataset.code = this.data[key];
            option.onclick = () => this.handleOptionClick(option);
            this.ulElement.appendChild(option);
        });
        this.ulElement.style.display = filteredOptions.length > 0 ? 'block' : 'none';
    }

    handleOptionClick(option)
    {
        const selectedCode = option.dataset.code;
        const selectedKey = Object.keys(this.data).find(key => this.data[key] === selectedCode);
        this.inputElement.value = this.data[selectedKey];
        this.ulElement.style.display = 'none';
    }

    validate() {
        let value = this.inputElement.value;
        if (value.trim() === "") {
            this.errorElement.innerText = JSON.parse(this.inputElement.getAttribute("validate").replaceAll("'", "\""))['call'] + " is required";
            return;
        }
        if (!(value.trim() in Object.keys(this.data))) {
            this.errorElement.innerText = JSON.parse(this.inputElement.getAttribute("validate").replaceAll("'", "\""))['call'] + " is invalid";
        }
    }
}