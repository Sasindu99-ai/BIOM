class Models
{
    static logout()
    {
        thread(() => {
            new UTIL.Toast().okCancel("You will have to login again to continue!", "Are you sure?", "warning", "Log Out", "Cancel", "btn btn-success", "btn btn-danger")
                .then(function(result) {
                    if(result.value) {
                        window.location.assign(ROOTPATH + "auth/logout");
                    } else if(result.dismiss === swal.DismissReason.cancel) {}
                });
        });
    }

    static launchApiModel(endpoint)
    {
        const
            containerClass = 'card',
            overlayClass = 'card-overlay',
            overlayAnimationClass = 'card-overlay-fadeout';

        // Elements
        const
            parentContainer = document.querySelector("#api-model .modal-dialog"),
            overlayElement = document.createElement('div'),
            overlayElementIcon = document.createElement('span'),
            childContainer = document.createElement('div'),
            scriptElement = document.createElement("script");;

        parentContainer.innerHTML = "<div class='modal-content'></div>";

        // Append overlay with icon
        overlayElement.classList.add(overlayClass);
        parentContainer.appendChild(overlayElement);
        overlayElementIcon.classList.add("spinner-border", "spinner-border-lg", 'spinner');
        overlayElement.appendChild(overlayElementIcon);

        function removeSpinner() {
            overlayElement.classList.add(overlayAnimationClass);
            ['animationend', 'animationcancel'].forEach(function(e) {
                overlayElement.addEventListener(e, function() {
                    overlayElement.remove();
                });
            });
        }

        window.API.load(endpoint)
            .done((api_report) => {
                childContainer.classList.add("modal-content");
                childContainer.innerHTML = api_report;
                let script = childContainer.querySelector("script");
                if (script != null) {
                    scriptElement.innerHTML = script.innerHTML;
                    childContainer.querySelector("script").remove();
                }
                parentContainer.appendChild(childContainer);
                if (script != null) {
                    parentContainer.appendChild(scriptElement);
                }
                removeSpinner();
            })
            .fail((jqXHR, textStatus, errorThrown) => {
                removeSpinner();
            });
    }

    static dismissModel(id)
    {
        let model = document.getElementById(id);
        if (model != null) {
            model.style.display = "none";
            if (model.classList.contains("show")) model.classList.remove("show");
            model.setAttribute("aria-modal", "false");
            if (model.hasAttribute("role")) model.removeAttribute("role")
        }
    }

    static dismissApiModel()
    {
        document.getElementById("cancel-api-model").click();
    }
}

window.MODELS = Models;