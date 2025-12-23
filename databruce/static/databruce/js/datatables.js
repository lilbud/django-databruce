DataTable.type('num', 'className', 'dt-center');
DataTable.type('string', 'className', 'dt-left text-wrap');
DateTime.defaults.minDate = new Date('1965-01-01 00:00:00');
DateTime.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';
DataTable.defaults.column.orderSequence = ['asc', 'desc'];

$.extend(true, DataTable.defaults, {
  searching: true,
  fixedHeader: true,
  info: true,
  scrollX: false,
  //scrollY: '60vh',
  scrollCollapse: true,
  // responsive: {
  //   details: {
  //     target: 'tr',
  //     type: 'column',
  //     display: $.fn.dataTable.Responsive.display.childRowImmediate,
  //     renderer: function (api, rowIdx, columns) {
  //       let data = columns.map((col, i) => {
  //         var title = col.title.replaceAll(':', '') + ':';

  //         return col.hidden && (col.data || col.data === false) ? `<div class="row res-child py-1 text-sm"><div class="col-4 text-end fw-bold">${title}</div><div class="col text-wrap align-bottom">${col.data}</div></div>` : '';
  //       }).join('');
  //       return data ? $('<table />').append(data) : false;
  //     },
  //   },
  // },
  responsive: {
    details: false,
  },
  autoWidth: false,
  pageLength: 100,
  lengthMenu: [25, 50, 100],
  language: {
    searchBuilder: {
      button: '&nbspFilter',
      className: 'test',
      title: '',
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
    $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
  });
});

function getDatatableLayout({ columns = true, category = false }) {
  var layout = {
    topEnd: {
      features: [
        {
          buttons: [
            {
              extend: 'collection',
              text: 'All',
              name: 'category-select',
              id: "dropdown-btn",
              className: 'btn btn-sm btn-primary category-btn my-2',
              buttons: []
            }
          ],
        },
        {
          search: {
            processing: true,
          }
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
      ]
    },
    bottomEnd: {
      paging: {
        numbers: 3
      }
    }
  };

  var searchbuilder = {
    //extend: 'searchBuilder',
    text: ' Filter',
    className: "btn-sm btn-primary bi bi-search my-2 d-lg-inline search",
    config: {
      liveSearch: false,
      columns: columns,
    },
    attr: {
      id: 'sbButton',
      'data-bs-toggle': 'modal',
      'data-bs-target': '#sbModal',
    },
    init: function() {
      console.log(this);
    },
    action: function (e, dt, node, config, cb) {
      new DataTable.SearchBuilder(dt, {
        liveSearch: false,
        columns: columns,
        depthLimit: 1,
      });

      dt.searchBuilder.container().prependTo('#modal-body');
    }
  };

  if (columns) {
    layout.topEnd.features.push({ 'buttons': [searchbuilder] });
  }

  if (!category) {
    layout.topEnd.features.splice(0, 1);
  };

  return layout;
};

function dtCategorySelect({ layout, column_idx, values }) {
  var div = document.createElement('div');
  $(div).addClass('me-2 my-auto text-sm align-middle');
  $(div).attr('id', 'dropdown-label');
  $(div).text('Category:');

  var button = {
    text: 'All',
    className: 'category-btn',
    action: function (e, dt, node, config) {
      dt.column(column_idx).search('.*', { regex: true }).draw();
      node.parents('.btn-group').find('.dropdown-toggle').text('All');
    },
  };

  layout.topEnd.features[0].buttons[0].buttons = [button];

  for (let i in values) {
    var button = {
      text: values[i].label,
      className: 'category-btn',
      action: function (e, dt, node, config) {
        dt.column(column_idx).search(values[i].value, { regex: true }).draw();
        node.parents('.btn-group').find('.dropdown-toggle').text(values[i].label);
      },
    };

    layout.topEnd.features[0].buttons[0].buttons.push(button);
  };

  $(document).ready(function () {
    $(div).insertBefore($('.category-btn').parent('.btn-group'));

    $('#dropdown-label').siblings('.btn-group').removeClass();
  });
}

// below are some common table column definitions
// tables like songs/events don't change from page to page
song_table_columns = [
  { 'data': 'count', 'name': 'count', 'width': '1rem', 'className': 'min-tablet-l' },
  {
    'data': 'song',
    'name': 'song__name',
    'width': '15rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display') {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  { 'data': 'song.category', 'name': 'song__category','width': '15rem', 'className': 'min-tablet-l' },
]

event_table_columns = [
  {
    'data': 'date',
    'name': 'id',
    'width': '8rem',
    'type': 'text',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/events/' + data.id + '">' + data.display + '</a>';
      }
    },
  },
  {
    'data': 'setlist',
    'name': 'setlist',
    'width': '1rem',
    'className': 'text-center',
    'render': function (data, type, row, meta) {
      if (type === 'display' && (row.setlist || row.setlist === false)) {
        return row.setlist || row.setlist === false ? `<i class="bi bi-file-earmark-check d-none d-md-block" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Has Setlist"></i><div class="d-inline d-md-none">${row.setlist}</div>` : `<div class="d-inline d-md-none">${row.setlist}</div>`
      }
    },
  },
  {
    'data': 'artist',
    'name': 'artist__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/bands/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'venue',
    'name': 'venue__name, venue__detail',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/venues/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'venue.city',
    'name': 'venue__city__name, venue__state__abbrev, venue__country__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/cities/' + data.id + '">' + data.display + '</a>';
      };
    },
  },
  {
    'data': 'tour',
    'name': 'tour__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/tours/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  { 'data': 'title', 'name': 'title', 'width': '15rem' },
  { 'data': 'public', 'name': 'public' },
]

setlist_slots = [
  {
    'data': 'event.date',
    'name': 'event__id, event__early_late',
    'width': '6rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display') {
        return '<a href="/events/' + data.id + '">' + data.display + '</a>';
      }
    },
  },
  {
    'data': 'event.venue',
    'name': 'event__venue__name, event__venue__detail',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display') {
        return '<a href="/venues/' + data.id + '">' + data.formatted + '</a>';
      }
    },
  },
  {
    'data': 'show_opener',
    'name': 'show_opener__id, show_opener__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 's1_closer',
    'name': 's1_closer__id, s1_closer__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 's2_opener',
    'name': 's2_opener__id, s2_opener__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'main_closer',
    'name': 'main_closer__id, main_closer__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'encore_opener',
    'name': 'encore_opener__id, encore_opener__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'show_closer',
    'name': 'show_closer__id, show_closer__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
]