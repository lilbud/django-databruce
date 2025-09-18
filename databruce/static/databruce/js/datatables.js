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
            depthLimit: 2,
          }
        }],
      }]
  },
  topStart: {
    buttons: [
      {
        extend: 'pageLength',
        className: 'btn-sm mb-1 mr-2',
      },
      {
        extend: 'colvis',
        columns: 'th:nth-child(n+2)',
        className: 'btn-sm mb-1 mr-2',
      }
    ]
  },
  bottomEnd: {
    paging: {
      numbers: 3
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
  lengthMenu: [25, 50, 100],
  language: {
    searchBuilder: {
      button: '&nbspFilter'
    }
  },
  order: [],
  drawCallback: function (settings) {
    $('[data-bs-toggle="tooltip"]').tooltip();
  },
});

// needed to fix pages with multiple tables behind tabs
$(document).ready(function () {
  $('a[data-bs-toggle="tab"], button[data-bs-toggle="pill"]').on('shown.bs.tab', function (e) {
    $($.fn.dataTable.tables(true)).DataTable()
      .columns.adjust()
      .responsive.recalc();
  });
})