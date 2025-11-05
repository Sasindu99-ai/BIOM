export default class AutoComplete {
    inputElement = null;
    errorElement = null;
    data = {};
    history = [];
    filteredHistory = [];
    autoCompleteWidget = null;

    async init(id, src=[], highlight=true, engine=true, minCharMatch=1,
               delay=null, disable=false, focus=false, maxCount=null,
               noResults=true, recent=false, recentCount=2,
               load=false, startsWith=false, multiple=false) {
        this.inputElement = document.getElementById(id);
        this.errorElement = document.getElementById(id + "-error");
        parent = this;
        this.autoCompleteWidget = new autoComplete({
            selector: `#${id}`,
            data: {
                src: (load) ? await this.loadSrc(src) : src,
                filter: (list) => {
                    if (startsWith) {
                        return list.filter((item) => {
                            const inputValue = parent.inputElement.value.toLowerCase();
                            const itemValue = item.value.toLowerCase();

                            if (itemValue.startsWith(inputValue)) {
                                return item.value;
                            }
                        });
                    } else {
                        return  list;
                    }
                }
            },
            resultItem: {
                highlight: highlight
            },
            resultsList: {
                element: (list, data) => {
                    if (disable) {
                        return;
                    }

                    if (noResults && data.matches.length === 0) {
                        list.innerHTML += '<li class="pe-none py-1"><div class="my-1">Found <strong>0</strong> matching results for <strong>"'+data.query+'"</strong></div></li>'
                    } else {
                        let recentSearch = [];
                        for (let i=parent.history.length-1; i>=0; i--) {
                            recentSearch.push(parent.history[i]);
                        }
                        const historyLength = recentSearch.length;

                        let info = null;
                        if (recent && historyLength>0) {
                            if (maxCount) {
                                info = document.createElement('li');
                                info.classList.add('pe-none', 'border-bottom', 'pt-0', 'pb-2', 'mb-2');
                                if (data.results.length > 0) {
                                    info.innerHTML = `<div class="my-1">Displaying <strong>${data.results.length}</strong> out of <strong>${data.matches.length}</strong> results</div>`;
                                }
                                if (maxCount > 0) list.innerHTML = info.outerHTML + list.innerHTML;
                            }
                            const historyBlock = document.createElement("li");
                            historyBlock.classList.add('pe-none', 'pt-0', 'pb-2', 'mb-2');
                            historyBlock.innerHTML = '<div class="fw-semibold">Recent Searches</div>';
                             parent.filteredHistory = data.matches.filter((item) => {
                                if (recentSearch.includes(item.value)) {
                                    return item
                                }
                            })
                            if (parent.filteredHistory.length > 0 ) list.innerHTML = "<hr>" + list.innerHTML;
                            parent.filteredHistory.slice(0, parent.filteredHistory.length<recentCount?parent.filteredHistory.length:recentCount).forEach((item) => {
                                console.log(item);
                                list.innerHTML = "<li value='" + item.match + "'>" + item.match + "</li>" + list.innerHTML;
                            });
                            if (parent.filteredHistory.length > 0) list.innerHTML = historyBlock.outerHTML + list.innerHTML;

                        } else {
                            if (maxCount) {
                                const info = document.createElement('li');
                                info.classList.add('pe-none', 'border-bottom', 'pt-0', 'pb-2', 'mb-2');
                                if (data.results.length > 0) {
                                    info.innerHTML = `<div class="my-1">Displaying <strong>${data.results.length}</strong> out of <strong>${data.matches.length}</strong> results</div>`;
                                }
                                list.prepend(info);
                            } else if (!noResults) {
                                let txt = "";
                                for (let i = 0; i < data.matches.length; i++) {
                                    txt += "<li value='" + data.matches[i].match + "'>" + data.matches[i].match + "</li>";
                                }
                                list.innerHTML += txt;
                            }
                        }
                    }
                },
                noResults: noResults,
                maxResults: maxCount??(noResults?15:null),
                tabSelect: (maxCount!=null || noResults)
            },
            query: (query) => {
                if (multiple) {
                    const querySplit = query.split(",");
                    const lastQuery = querySplit.length - 1;
                    return querySplit[lastQuery].trim();
                }

                return query;
            },
            threshold: minCharMatch,
            debounce: delay,
            searchEngine: (engine) ? "loose" : "strict",
            events: {
                input: {
                    selection: function (event) {
                        try {
                            let selectedOne = event.detail.selection.index;
                            let minuses = 0;
                            if (recent && parent.filteredHistory.length > 0) minuses += 1 + parent.filteredHistory.length;
                            if (maxCount) minuses += 1;
                            if (!disable) {
                                const input = parent.inputElement;
                                const query = input.value.split(",").map(item => item.trim());

                                if (recent) {
                                    if ((selectedOne === 1 || selectedOne === 2) && (selectedOne-1 < parent.filteredHistory.length)) {
                                        parent.history.push(parent.filteredHistory[selectedOne-1].value);
                                        parent.inputElement.value = parent.filteredHistory[selectedOne-1].value;
                                        if (!multiple) return;
                                    } else {
                                        parent.history.push(event.detail.matches[selectedOne - minuses].value);
                                        parent.inputElement.value = event.detail.matches[selectedOne - minuses].value;
                                        if (!multiple) return;
                                    }
                                } else {
                                    parent.inputElement.value = event.detail.matches[selectedOne-minuses].value;
                                    if (!multiple) return;
                                }
                                if (multiple) {
                                    query.pop();
                                    query.push(input.value);
                                    input.value = query.join(", ") + ", ";
                                }
                            }
                        } catch (e) {
                            console.error(e);
                        }
                    },
                    focus() {
                        if (focus) {
                            const inputValue = parent.inputElement.value;
                            if (inputValue.length) parent.autoCompleteWidget.start();
                        }
                    }
                }
            }
        })
    }

    async loadSrc(src){
        // try {
        //     const source = await fetch(src);
        //     return await source.json();
        // }
        // catch (error) {
        //     return error;
        // }
        return src();
    }

    constructor(id=null) {
        if (id != null) {
            let validate = JSON.parse(document.getElementById(id).getAttribute("validate").replaceAll("'", "\""));
            this.init(id, validate.data, validate["highlight"]??true, validate["engine"]??true,
                validate["minCharMatch"]??1, validate["delay"]??null, validate["disable"]??false,
                validate["focus"]??false, validate["maxCount"]??null, validate["noResults"]??true,
                validate["recent"]??false, validate["recentCount"]??2, validate["load"]??false,
                validate["startsWith"]??false, validate["multiple"]??false);
        }
    }
}
