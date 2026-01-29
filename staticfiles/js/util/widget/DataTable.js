export default class DataTable1 {
    id;
    table;
    lastRowCount = null;
    options = {
        autoWidth: false,
        order: [],
        columnDefs: [],
        aoColumns: null,
        scrollX: true,
        fixedHeader: true,
        dom: '<"datatable-header"fl><"datatable-scroll"t><"datatable-footer"ip>',
        pagingType: "simple_numbers",
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        language: {
            search: '<span class="me-3">Filter:</span> <div class="form-control-feedback form-control-feedback-end flex-fill">_INPUT_<div class="form-control-feedback-icon"><i class="ph-magnifying-glass opacity-50"></i></div></div>',
            searchPlaceholder: 'Type to filter...',
            lengthMenu: '<span class="me-3">Show:</span> _MENU_',
            paginate: {
                'first': 'First',
                'last': 'Last',
                'next': document.dir === "rtl" ? '&larr;' : '&rarr;',
                'previous': document.dir === "rtl" ? '&rarr;' : '&larr;'
            }
        },
        stateSave: false,
        scrollY: null,
        buttons: {
            className: "",
            dom: {
                button: {
                    className: 'btn btn-light',
                }
            },
            buttons: []
        },
        responsive: {
            details: {
                type: 'column',
                target: -1
            }
        },
        initComplete: function () {},
        drawCallback: (settings) => {
            this.tableEvents(this.table, settings.nTable.id);
        }
    }
    modifiers = {
        highlight: false
    }

    init(id) {
        this.id = id
        this.table = $(`#${this.id}`).DataTable(this.options);

        let Table = this.table;
        if (scrollY != null) {
            $('.sidebar-control').on('click', function () {
                Table.columns.adjust().draw();
            });
        }

        if (this.modifiers.highlight) {
            let lastIdx = null;
            $(`#${this.id} tbody`).on('mouseover', 'td', function() {
                const colIdx = Table.cell(this).index().column;
                if (colIdx !== lastIdx) {
                    $(Table.cells().nodes()).removeClass('active');
                    $(Table.column(colIdx).nodes()).addClass('active');
                }
            }).on('mouseleave', function() {
                $(Table.cells().nodes()).removeClass('active');
            });
        }

        return this.table;
    }

    updateTableOptions(options, root) {
        Object.keys(options).forEach(key => {
            root[key] = (typeof options[key] === "object" && Object.getPrototypeOf(options[key]).constructor.name !== "Array") ? this.updateTableOptions(options[key], root[key]) : options[key];
        });
        return root;
    }

    constructor(id = null, options = {}, modifier = {}) {
        if (!$().DataTable) {
            console.warn('Warning - Failed to load data table.');
            return;
        }

        if (id != null) {
            this.options = this.updateTableOptions(options, this.options);
            this.modifiers = this.updateTableOptions(modifier, this.modifiers);

            return this.init(id)
        }
    }

    tableEvents(table, id) {
        try {
            if (typeof table.lastRowCount !== "undefined" && table.lastRowCount !== null && table.lastRowCount !== table.page.info().length) {
                if (typeof loadMore !== "undefined" && !loading) {
                    loadMore(id, true);
                    return;
                }
            }
        } catch (e) {}

        $('.paginate_button.page-item.next').removeClass('disabled');
        $('.paginate_button.next').on('click', () => {
            if (typeof loadMore !== "undefined") loadMore(id);
        });
    }

    static refreshTable(table, where="top", page=null) {
        table.lastRowCount = table.page.info().length;

        if (page == null && table.page.info().page > 0) {
            page = table.page.info().page;
        }

        if (where === "top") {
            table.order([0, "desc"])
        }
        if (page != null) {
            table.page(page).draw("page");
        } else {
            table.draw();
        }
    }

}

function initDataTable() {
    $.extend($.fn.dataTable.defaults, {
        autoWidth: false,
        columnDefs: [],
        dom: '<"datatable-header"fl><"datatable-scroll"t><"datatable-footer"ip>',
        language: {
            search: '<span class="me-3">Filter:</span> <div class="form-control-feedback form-control-feedback-end flex-fill">_INPUT_<div class="form-control-feedback-icon"><i class="ph-magnifying-glass opacity-50"></i></div></div>',
            searchPlaceholder: 'Type to filter...',
            lengthMenu: '<span class="me-3">Show:</span> _MENU_',
            paginate: {
                'first': 'First',
                'last': 'Last',
                'next': document.dir === "rtl" ? '&larr;' : '&rarr;',
                'previous': document.dir === "rtl" ? '&rarr;' : '&larr;'
            }
        }
    });
}

// thread(initDataTable, 100);