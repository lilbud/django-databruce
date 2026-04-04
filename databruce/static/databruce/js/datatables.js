DataTable.type('num', 'className', 'dt-center');
DataTable.type('string', 'className', 'dt-left text-wrap');
DateTime.defaults.minDate = new Date('1965-01-01 00:00:00');
DateTime.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';
DataTable.defaults.column.columnControl = ['order', ['orderAsc', 'orderDesc', 'orderClear', 'orderAddAsc', 'orderAddDesc']];

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
  scrollX: true,
  scrollCollapse: true,
  serverSide: true,
  processing: true,
  responsive: {
    details: false
  },
  autoWidth: false,
  paging: true,
  searching: true,
  info: true,
  ordering: {
    indicators: false,
    handler: true
  },
  scrollX: true,
  pageLength: 100,
  lengthMenu: [25, 50, 100],
  language: {
    searchBuilder: {
      button: '&nbspFilter',
      className: 'test',
      title: '',
    }
  },
  search: {
    regex: true
  },
  order: [],
  drawCallback: function (settings) {
    $('[data-bs-toggle="tooltip"]').tooltip();
  },
});

// needed to fix pages with multiple tables behind tabs
$(document).ready(function () {
  $('a[data-bs-toggle="tab"], button[data-bs-toggle="pill"], a[data-bs-toggle="pill"]').on('shown.bs.tab', function (e) {
    $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
  });
});

const slugify = (str) => {
  return str
    .toLowerCase() // Convert to lowercase
    .trim() // Trim leading/trailing whitespace
    .replace(/[^\w\s-]/g, '') // Remove all non-word chars (except spaces and hyphens)
    .replace(/[\s_-]+/g, '-') // Replace all spaces, underscores, and multiple hyphens with a single hyphen
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
};

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
            regex: true
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
    className: 'button-page-length dt-button-active-a',
    action: function (e, dt, node, config) {
      dt.column(column_idx).search('.*', { regex: true }).draw();
      node.parents('.btn-group').find('.dropdown-toggle').text('All');
      node.parents('.dropdown-menu').find('.dt-button').each(function () {
        $(this).removeClass('dt-button-active-a');
      });
      node.toggleClass('dt-button-active-a');
    },
  };

  layout.topEnd.features[0].buttons[0].buttons = [all_button];

  values.forEach(element => {
    var button = {
      text: element.label,
      className: 'button-page-length',
      action: function (e, dt, node, config) {
        dt.column(column_idx).search(element.value, { regex: true }).draw();
        node.parents('.btn-group').find('.dropdown-toggle').text(element.label);

        node.parents('.dropdown-menu').find('.dt-button').each(function () {
          $(this).removeClass('dt-button-active-a');
        });
        node.toggleClass('dt-button-active-a');
      },
    };

    layout.topEnd.features[0].buttons[0].buttons.push(button);
  });

  $(document).ready(function () {
    $(div).insertBefore($('#dropdown-btn'));
  })
}

function renderLink(url, data, text) {
  return `<a href="${url}${data}">${text}</a>`
}

song_table_defs = [
  { targets: '_all', className: 'text-wrap text-xs' },
  { targets: [0], width: '1rem' },
]

// below are some common table column definitions
// tables like songs/events don't change from page to page
song_table_columns = [
  {
    'data': 'count',
    'name': 'count',
    'width': '1rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      return data
    },
  },
  {
    'data': 'song',
    'name': 'song__sort_song_name',
    'width': '15rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return renderLink('/songs/', data.uuid, data.name);
      }
    },
  },
  { 'data': 'song.category', 'name': 'song__category', 'width': '15rem', 'className': '' },
  {
    'data': 'first_event',
    'name': 'first_event',
    'width': '10rem',
    'type': 'text',
    'className': 'all',
    'render': function (data, type, row, meta) {
      return renderLink('/events/', data.event_id, data.date.display_day);
    },
  },
  {
    'data': 'last_event',
    'name': 'last_event',
    'width': '10rem',
    'type': 'text',
    'className': 'all',
    'render': function (data, type, row, meta) {
      return renderLink('/events/', data.event_id, data.date.display_day);
    },
  },
]

event_table_defs = [
  { targets: [1], orderable: false, className: 'text-center text-xs', width: '1rem', searchable: false, columnControl: [] },
  { targets: [0], className: 'text-nowrap' },
  { targets: [-1], visible: false },
]

event_table_columns = [
  {
    'data': 'date',
    'name': 'event_id',
    'type': 'text',
    'className': 'all text-nowrap',
    'render': function (data, type, row, meta) {
      return renderLink('/events/', row.event_id, data.display_day);
    },
  },
  {
    'data': 'has_setlist',
    'name': 'has_setlist',
    'width': '1rem',
    'className': 'text-center text-sm',
    'orderable': false,
    'searchable': false,
    'render': function (data, type, row, meta) {
      return data ? `<i class="bi bi-file-earmark-check d-none d-md-block" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Has Setlist"></i><div class="d-inline d-md-none">${row.has_setlist}</div>` : `<div class="d-inline d-md-none">${row.has_setlist}</div>`
    },
  },
  {
    'data': 'artist',
    'name': 'artist__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      return renderLink('/bands/', data.uuid, data.name);
    },
  },
  {
    'data': 'venue',
    'name': 'venue__name, venue__detail',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      return renderLink('/venues/', data.uuid, data.name);
    },
  },
  {
    'data': 'venue.city',
    'name': 'venue__city__name, venue__city__state__abbrev, venue__city__state__name, venue__city__country__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      return renderLink('/cities/', data.uuid, data.formatted);
    },
  },
  {
    'data': 'tour',
    'name': 'tour__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      return renderLink('/tours/', data.uuid, data.name);
    },
  },
  {
    'data': 'title',
    'name': 'title',
    'width': '15rem',
    'render': function (data, type, row, meta) {
      if (row.event_status) {
        if (data) {
          return `<span class="text-danger fw-semibold">[${row.type.name}] ${data}</span>`
        }
        return `<span class="text-danger fw-semibold">[${row.type.name}]</span>`
      }

      return data;
    },
  },
  { 'data': 'public', 'name': 'public', 'visible': false, 'orderable': false },
]

setlist_slots = [
  {
    'data': 'event',
    'name': 'event__event_id, event__early_late',
    'width': '10rem',
    'className': 'all text-nowrap',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/events/' + data.event_id + '">' + data.date.display_day + '</a>';
      }
    },
  },
  {
    'data': 'show_opener',
    'name': 'show_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.uuid + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 's1_closer',
    'name': 's1_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.uuid + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 's2_opener',
    'name': 's2_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.uuid + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'main_closer',
    'name': 'main_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.uuid + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'encore_opener',
    'name': 'encore_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.uuid + '">' + data.name + '</a>';
      }
    },
  },
  {
    'data': 'show_closer',
    'name': 'show_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return '<a href="/songs/' + data.uuid + '">' + data.name + '</a>';
      }
    },
  },
]