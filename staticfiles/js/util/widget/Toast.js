export default class Toast {
    constructor() {
        this.swalInit = swal.mixin({
            buttonsStyling: false,
            customClass: {
                confirmButton: 'btn btn-primary',
                cancelButton: 'btn btn-light',
                denyButton: 'btn btn-light',
                input: 'form-control'
            }
        });
    }

    toast(message, icon="success", toast=true, position="top-end", showConfirmButton=false,
          timer= 1500, timerProgressBar= true) {
        // while (document.getElementsByClassName("swal2-container") > 0) {
        //     document.getElementsByClassName("swal2-container")[0].remove();
        // }
        return this.swalInit.fire({
            text: message,
            icon: icon,
            toast: toast,
            showConfirmButton: showConfirmButton,
            position: position,
            timer: timer,
            timerProgressBar: timerProgressBar
        });
        // if (timer != null) {
        //     setTimeout(() => {
        //         document.getElementsByClassName("swal2-container")[0].remove();
        //     }, timer);
        // }
    }

    ok(message, title="Success", icon="success", confirmButtonText="OK", confirmButtonClass="btn btn-primary") {
        return this.swalInit.fire({
            title: title,
            text: message,
            icon: icon,
            confirmButtonText: confirmButtonText,
            buttonsStyling: false,
            customClass: {
                confirmButton: confirmButtonClass
            }
        });
    }

    okCancel(message, title="Are you sure?", icon="warning", confirmButtonText="Yes, delete it!", cancelButtonText="No, cancel please!", confirmButtonClass="btn btn-success", cancelButtonClass="btn btn-danger") {
        return this.swalInit.fire({
            title: title,
            text: message,
            icon: icon,
            showCancelButton: true,
            confirmButtonText: confirmButtonText,
            cancelButtonText: cancelButtonText,
            buttonsStyling: false,
            customClass: {
                confirmButton: confirmButtonClass,
                cancelButton: cancelButtonClass
            }
        });
    }
}