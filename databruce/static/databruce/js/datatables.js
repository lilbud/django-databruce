var layout = {
  topEnd: {
    features: [
      { div: { id: "dropdown-container", className: "mx-auto my-2" } },
      {
        search: true
      },
    ],
  },
  topStart: {
    buttons: [
      {
        extend: 'pageLength',
        className: 'btn btn-sm btn-primary',
      },
      {
        extend: 'colvis',
        columns: 'th:nth-child(n+2)', //starts at second column
        className: 'btn btn-sm btn-primary',
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
        renderer: function ( api, rowIdx, columns ) {
            var data = $.map( columns, function ( col, i ) {
                if (col.hidden && col.data != '') {
                    // selectively add a trailing colon if there isn't one
                    if (col.title.includes(":")) {
                      var title = col.title
                    } else {
                      var title = `${col.title}:`
                    };

                    return '<tr class="res-child" data-dt-row="'+col.rowIndex+'" data-dt-column="'+col.columnIndex+'">'+
                        '<td class="text-nowrap fw-bold" style="width: 3rem;">'+title+'</td>'+
                        '<td class="text-wrap">'+col.data+'</td>'+
                    '</tr>';
                }
            } ).join('');
 
            return data ?
                $('<table/>').append( data ) :
                false;
        }
    }
  },
  info: true,
  scrollX: true,
  pageLength: 50,
  lengthMenu: [25, 50, 100],
  language: {
    searchBuilder: {
      button: '&nbspFilter',
      className: 'test',
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
      className: "btn-sm btn-primary bi bi-search my-2 d-lg-inline search",
      config: {
        depthLimit: 1,
        columns: columns,
        liveSearch: false,
      },
    };

    layout.topEnd.features[1].buttons[0] = searchbuilder;
  };

  return layout;
};