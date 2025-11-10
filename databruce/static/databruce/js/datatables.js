var layout = {
  topEnd: {
    features: [
      { div: { 
          id: "dropdown-label",
          className: "mx-auto my-2 text-sm",
          text: 'Category:',   
        },
        buttons: [
          { extend: 'collection',
            text: 'All',
            name: 'category-select',
            id: "dropdown-btn",
            className: 'btn btn-sm btn-primary category-btn',
            buttons: []
          }
        ],
      },
      {
        search: true,
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
      }
    ]
  },
  bottomEnd: {
    paging: {
      numbers: 3
    }
  }
};

DataTable.type('num', 'className', 'dt-center');
DataTable.type('string', 'className', 'dt-left text-nowrap');
DateTime.defaults.minDate = new Date('1965-01-01 00:00:00');
DateTime.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';

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
  scrollX: false,
  scrollY: false,
  autoWidth: false,
  pageLength: 100,
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

function getDatatableLayout(columns, category) {
  if (columns) {
    var searchbuilder = {
      extend: 'searchBuilder',
      className: "btn-sm btn-primary bi bi-search my-2 d-lg-inline search",
      config: {
        depthLimit: 1,
        columns: columns,
        liveSearch: false,
      },
    };

    layout.topEnd.features.push({'buttons': [searchbuilder]});
  };

  if (!category) {
    layout.topEnd.features.splice(0, 1);
  };

  return layout;
};

function dtCategorySelect(layout, column_idx, values) {
  for (let i in values) {
      var button = {
        text: values[i].label,
        className: 'category-btn',
        action: function (e, dt, node, config) {
          dt.column(column_idx).search(values[i].value, {regex: true}).draw();
          node.parents('.btn-group').find('.dropdown-toggle').text(values[i].label);
        },
      };

      layout.topEnd.features[0].buttons[0].buttons.push(button);
  };
}