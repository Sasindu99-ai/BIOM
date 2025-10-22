export default class FileUploader
{
    previewZoomButtonClasses = {
        rotate: 'btn btn-light btn-icon btn-sm',
        toggleheader: 'btn btn-light btn-icon btn-header-toggle btn-sm',
        fullscreen: 'btn btn-light btn-icon btn-sm',
        borderless: 'btn btn-light btn-icon btn-sm',
        close: 'btn btn-light btn-icon btn-sm'
    };

    // Icons inside zoom modal classes
    previewZoomButtonIcons = {
        prev: document.dir === 'rtl' ? '<i class="ph-arrow-right"></i>' : '<i class="ph-arrow-left"></i>',
        next: document.dir === 'rtl' ? '<i class="ph-arrow-left"></i>' : '<i class="ph-arrow-right"></i>',
        rotate: '<i class="ph-arrow-clockwise"></i>',
        toggleheader: '<i class="ph-arrows-down-up"></i>',
        fullscreen: '<i class="ph-corners-out"></i>',
        borderless: '<i class="ph-frame-corners"></i>',
        close: '<i class="ph-x"></i>'
    };

    // File actions
    fileActionSettings = {
        zoomClass: '',
        zoomIcon: '<i class="ph-magnifying-glass-plus"></i>',
        dragClass: 'p-2',
        dragIcon: '<i class="ph-dots-six"></i>',
        removeClass: '',
        removeErrorClass: 'text-danger',
        removeIcon: '<i class="ph-trash"></i>',
        indicatorNew: '<i class="ph-file-plus text-success"></i>',
        indicatorSuccess: '<i class="ph-check file-icon-large text-success"></i>',
        indicatorError: '<i class="ph-x text-danger"></i>',
        indicatorLoading: '<i class="ph-spinner spinner text-muted"></i>'
    };

    id;
    fileInput;
    fileUploaded;
    options = {
        browseLabel: 'Browse',
        uploadUrl: ROOTPATH + "api/resources/upload/file?upload=true",
        uploadAsync: true,
        maxFileCount: 1,
        initialPreview: [],
        browseIcon: '<i class="ph-file-plus me-2"></i>',
        uploadIcon: '<i class="ph-file-arrow-up me-2"></i>',
        removeIcon: '<i class="ph-x fs-base me-2"></i>',
        fileActionSettings: {
            removeIcon: '<i class="ph-trash"></i>',
            removeClass: '',
            dragClass: 'p-2',
            dragIcon: '<i class="ph-dots-six"></i>',
            uploadIcon: '<i class="ph-upload-simple"></i>',
            uploadClass: '',
            zoomIcon: '<i class="ph-magnifying-glass-plus"></i>',
            zoomClass: '',
            indicatorNew: '<i class="ph-file-plus text-success"></i>',
            indicatorSuccess: '<i class="ph-check file-icon-large text-success"></i>',
            indicatorError: '<i class="ph-x text-danger"></i>',
            indicatorLoading: '<i class="ph-spinner spinner text-muted"></i>',
        },
        layoutTemplates: {
            icon: '<i class="ph-check"></i>'
        },
        uploadClass: 'btn btn-light',
        removeClass: 'btn btn-light',
        initialCaption: 'No file selected',
        previewZoomButtonClasses: this.previewZoomButtonClasses,
        previewZoomButtonIcons: this.previewZoomButtonIcons
    };

    init(id) {
        this.id = id;
        this.fileInput = $(`#${this.id}`).fileinput(this.options)
            .on('fileuploaded', (event, data, previewId, index) => {
                if (this.fileUploaded != null) this.fileUploaded(event, data, previewId, index);
            });
    }

    updateOptions(options, root) {
        Object.keys(options).forEach(key => {
            root[key] = (typeof options[key] === "object" && Object.getPrototypeOf(options[key]).constructor.name !== "Array") ? this.updateOptions(options[key], root[key]) : options[key];
        });
        return root;
    }

    constructor(id, options, fileUploaded) {
        if (!$().fileinput) {
            console.warn('Warning - Failed to load data table.');
            return;
        }

        if (id != null) {
            this.options = this.updateOptions(options, this.options);
            this.fileUploaded = fileUploaded;

            return this.init(id);
        }
    }
}