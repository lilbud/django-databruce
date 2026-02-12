DataTable.type('num', 'className', 'dt-center');
DataTable.type('string', 'className', 'dt-left text-wrap');
DateTime.defaults.minDate = new Date('1965-01-01 00:00:00');
DateTime.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';
DataTable.defaults.column.orderSequence = ['desc', 'asc'];

set_names = [
  "Show",
  "Set 1",
  "Set 2",
  "Encore",
  "Pre-Show",
  "Post-Show",
]

$.extend(true, DataTable.defaults, {
  searching: true,
  fixedHeader: true,
  info: true,
  scrollX: false,
  scrollCollapse: true,
  responsive: {
    details: false
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
              attr: {
                id: 'dropdown-btn',
              },
              className: 'btn btn-sm btn-primary category-btn',
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
    action: function (e, dt, node, config, cb) {
      new DataTable.SearchBuilder(dt, {
        liveSearch: false,
        columns: columns,
        depthLimit: 1,
      });

      dt.searchBuilder.container().appendTo('#modal-body');
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

function dtCategorySelect({ layout, column_idx, values, label = false }) {
  var div = $('<label />')

  $(div).attr('for', 'dropdown-btn');
  $(div).text(`${label.replace(":", "")}:`);

  var all_button = {
    text: 'All',
    className: 'category-btn',
    action: function (e, dt, node, config) {
      dt.column(column_idx).search('.*', { regex: true }).draw();
      node.parents('.btn-group').find('.dropdown-toggle').text('All');
    },
  };

  layout.topEnd.features[0].buttons[0].buttons = [all_button];

  values.forEach(element => {
    var button = {
      text: element.label,
      className: 'category-btn',
      action: function (e, dt, node, config) {
        dt.column(column_idx).search(element.value, { regex: true }).draw();
        node.parents('.btn-group').find('.dropdown-toggle').text(element.label);
      },
    };

    layout.topEnd.features[0].buttons[0].buttons.push(button);
  });

  $(document).ready(function () {
    $(div).insertBefore($('#dropdown-btn'));
  })
}

function renderLink(url, data, text) {
  return '<a href="' + url + data + '">' + text + '</a>';
}

// below are some common table column definitions
// tables like songs/events don't change from page to page
song_table_columns = [
  {
    'data': 'count',
    'name': 'count',
    'width': '1rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (data) {
        return data
      }
    },
  },
  {
    'data': 'song',
    'name': 'song__name',
    // 'width': '15rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display') {
        return renderLink('/songs/', data.id, data.name);
      }
    },
  },
  { 'data': 'song.category', 'name': 'song__category', 'width': '15rem', 'className': 'min-tablet-l' },
]

event_table_columns = [
  {
    'data': 'date',
    'name': 'event_id',
    'width': '10rem',
    'type': 'text',
    'className': 'all',
    'render': function (data, type, row, meta) {
      return renderLink('/events/', row.event_id, data.display_day);
    },
  },
  {
    'data': 'has_setlist',
    'name': 'has_setlist',
    'width': '1rem',
    'className': 'min-tablet-l text-center text-sm',
    'orderable': false,
    'searchable': false,
    'render': function (data, type, row, meta) {
      return data ? `<i class="bi bi-file-earmark-check d-none d-md-block" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Has Setlist"></i><div class="d-inline d-md-none">${row.setlist}</div>` : `<div class="d-inline d-md-none">${row.setlist}</div>`
    },
  },
  {
    'data': 'artist',
    'name': 'artist__name',
    'width': '12rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      return renderLink('/bands/', data.id, data.name);
    },
  },
  {
    'data': 'venue',
    'name': 'venue__name, venue__detail',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      return renderLink('/venues/', data.id, data.name);
    },
  },
  {
    'data': 'venue',
    'name': 'venue__city__name, venue__city__state__abbrev, venue__city__country__name',
    'width': '12rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      return renderLink('/cities/', data.city.id, data.location);
    },
  },
  {
    'data': 'tour',
    'name': 'tour__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      return renderLink('/tours/', data.id, data.name);
    },
  },
  { 'data': 'title', 'name': 'title', 'width': '15rem', 'className': 'min-tablet-l', },
  { 'data': 'public', 'name': 'public', 'className': 'min-tablet-l', 'visible': false, 'orderable': false },
]

setlist_slots = [
  {
    'data': 'event',
    'name': 'event__id, event__early_late',
    'width': '9rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display') {
        return '<a href="/events/' + data.id + '">' + data.date.display_day + '</a>';
      }
    },
  },
  {
    'data': 'event.venue',
    'name': 'event__venue__name, event__venue__detail',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display') {
        return '<a href="/venues/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'show_opener',
    'name': 'show_opener__name',
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
    'name': 's1_closer__name',
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
    'name': 's2_opener__name',
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
    'name': 'main_closer__name',
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
    'name': 'encore_opener__name',
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
    'name': 'show_closer__name',
    'width': '12rem',
    'className': 'min-tablet-l',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.id + '">' + data.name + '</a>';
      }
    },
  },
]