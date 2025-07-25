var layout = {
    topEnd: {
        features: [
            { div: { id: "dropdown-container", className: "mr-6 d-none d-lg-inline" } },
            {
                search: true,
                buttons: [{
                    extend: 'searchBuilder',
                    action: function (e, dt, node, config) {
                        this.popover(config._searchBuilder.getNode(), {
                            collectionLayout: 'sbpopover'
                        })
                    },
                    className: "btn-sm bi bi-search mb-1 mr-2 d-none d-lg-inline search",
                    config: {
                        depthLimit: 4,
                    }
                }],
            }]
    },
    topStart: 'pageLength',
    bottomEnd: {
        paging: {
            numbers: 3
        }
    },
    bottomStart: {
        info: {
            text: 'Showing _START_-_END_ of _TOTAL_'
        }
    }
};

$.extend(true, DataTable.defaults, {
    searching: true,
    fixedHeader: true,
    responsive: {
        details: {
            display: $.fn.dataTable.Responsive.display.childRowImmediate,
        }
    },
    info: true,
    pageLength: 25,
    lengthMenu: [25, 50, 100, { label: 'All', value: -1 }],
    language: {
        searchBuilder: {
            button: '&nbspFilter'
        }
    },
    drawCallback: function (settings) {
        $('[data-bs-toggle="tooltip"]').tooltip();
    },
});