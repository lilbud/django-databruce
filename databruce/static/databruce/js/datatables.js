var layout = {
  topEnd: {
    features: [
      { div: { id: "dropdown-container", className: "mr-6 d-none d-lg-inline" } },
      {
        search: true
      },
    ],
  },
  topStart: {
    buttons: [
      {
        extend: 'pageLength',
        className: 'btn btn-sm mb-1 mr-2 btn-primary ',
      },
      {
        extend: 'colvis',
        columns: 'th:nth-child(n+2)', //starts at second column
        className: 'btn btn-sm mb-1 mr-2 btn-primary ',
      },
    ],
  },
  bottomEnd: {
    paging: {
      numbers: 3
    }
  }
};

DataTable.type('num', 'className', 'dt-center');
DataTable.type('num-fmt', 'className', 'dt-center');
DateTime.defaults.minDate = new Date('1965-01-01 00:00:00');
DateTime.defaults.maxDate = new Date();
DataTable.datetime('YYYYMMDD');

$.extend(true, DataTable.defaults, {
  searching: true,
  fixedHeader: true,
  responsive: {
    details: {
      display: $.fn.dataTable.Responsive.display.childRowImmediate,
    }
  },
  info: true,
  scrollX: true,
  // scrollY: '50vh',
  // scrollCollapse: true,
  pageLength: 50,
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
});

function getDatatableLayout(columns) {
  if (columns) {
    layout.topEnd.features[1]['buttons'] = [];

    var searchbuilder = {
      extend: 'searchBuilder',
      action: function (e, dt, node, config) {
        this.popover(config._searchBuilder.getNode(), {
          collectionLayout: 'sbpopover'
        })
      },
      className: "btn-sm btn-primary bi bi-search mb-1 mr-2 d-none d-lg-inline search",
      config: {
        depthLimit: 2,
        columns: columns,
      },
    };

    layout.topEnd.features[1].buttons[0] = searchbuilder;
  };

  return layout;
};