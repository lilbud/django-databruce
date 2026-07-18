DataTable.type('num', 'className', 'dt-center');
// DataTable.type('string', 'className', 'dt-left');
DateTime.defaults.minDate = new Date('1965-01-01 00:00:00');
DateTime.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';
DataTable.defaults.column.columnControl = [['orderAsc', 'orderDesc', 'orderClear', 'orderAddAsc', 'orderAddDesc']];

set_names = [
  "Show",
  "Set 1",
  "Set 2",
  "Encore",
  "Pre-Show",
  "Post-Show",
]

DataTable.feature.register('customInputPaging', function (settings) {
  const api = new DataTable.Api(settings);

  // Create UI container elements
  const container = document.createElement('div');
  container.className = 'd-inline-flex align-items-center justify-content-center gap-2 m-0';
  container.id = 'paging-container';
  container.innerHTML = `
        <button class="btn btn-sm border-0 btn-prev" aria-label="Previous page"><i class="bi bi-chevron-left"></i></button>
        <input type="text" class="form-control form-control-sm text-center page-input m-0" min="1" value="1" style="width: 30px; height: calc(1.5em + 0.5rem + 2px);">
        <span class="total-pages align-middle">of 1</span>
        <button class="btn btn-sm border-0 btn-next" aria-label="Next page"><i class="bi bi-chevron-right"></i></button>
    `;

  const input = container.querySelector('.page-input');
  const prevBtn = container.querySelector('.btn-prev');
  const nextBtn = container.querySelector('.btn-next');
  const totalSpan = container.querySelector('.total-pages');

  // Update UI whenever the table redraws / changes pages
  api.on('draw', () => {
    const pageInfo = api.page.info();
    input.value = pageInfo.page + 1;
    input.max = pageInfo.pages;
    totalSpan.textContent = `of ${pageInfo.pages || 1}`;

    // Handle button states
    prevBtn.disabled = pageInfo.page === 0;
    nextBtn.disabled = pageInfo.page >= pageInfo.pages - 1;
  });

  // Jump to page typed into input box
  input.addEventListener('change', () => {
    let val = parseInt(input.value, 10) - 1;
    const max = api.page.info().pages - 1;
    if (val < 0) val = 0;
    if (val > max) val = max;
    api.page(val).draw('page');
  });

  // Click navigation button events
  prevBtn.addEventListener('click', () => api.page('previous').draw('page'));
  nextBtn.addEventListener('click', () => api.page('next').draw('page'));

  return container;
});

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
  ordering: {
    indicators: false,
    handler: true
  },
  fixedHeader: {
    header: true,
  },
  pageLength: 50,
  lengthMenu: [25, 50, 100],
  language: {
    searchBuilder: {
      button: '&nbspFilter',
      className: 'test',
      title: '',
    },

    info: "_TOTAL_ records found",
    infoEmpty: "No records available",
    infoFiltered: "(filtered from _MAX_ total records)"

  },
  search: {
    regex: true
  },
  order: [],
  drawCallback: function (settings) {
    $('[data-bs-toggle="tooltip"]').tooltip();
  },
  layout: {
    topStart: null,
    bottomStart: null,
    topEnd: null,
    bottomEnd: null,
    top: ['customInputPaging', 'info'],
    bottom: ['customInputPaging', 'info'],
  },
});

// needed to fix pages with multiple tables behind tabs
$(document).ready(function () {
  $('a[data-bs-toggle="tab"], button[data-bs-toggle="pill"], a[data-bs-toggle="pill"]').on('shown.bs.tab', function (e) {
    $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
  });
});

const slugify = (str = '') => {
  return str
    .toLowerCase() // Convert to lowercase
    .trim() // Trim leading/trailing whitespace
    .replace(/[^a-z0-9]+/g, '-') // Replace all spaces, underscores, and multiple hyphens with a single hyphen
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
};

const escapeHtml = (str) => {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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
              fade: 100,
              name: 'category-select',
              attr: {
                id: 'dropdown-btn',
              },
              className: 'btn btn-sm btn-primary category-btn w-auto',
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
          className: 'btn btn-sm btn-primary w-auto',
          fade: 100,
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

      var container = dt.searchBuilder.container();
      container.appendTo('#modal-body');
    }
  };

  try {
    if (columns) {
      layout.topEnd.features.push({ 'buttons': [searchbuilder] });
    }

    if (!category) {
      layout.topEnd.features.splice(0, 1);
    };
  } catch ({ name, message }) {
    console.log(message);
  }

  return layout;
};

function renderLink(url, data, text) {
  return `<a href="${url}${data}">${text}</a>`
}

song_table_defs = [
  { targets: '_all', className: 'text-wrap text-xs' },
]

// below are some common table column definitions
// tables like songs/events don't change from page to page
song_table_columns = [
  {
    'data': 'count',
    'name': 'count',
    'width': '1rem',
    'className': 'all text-center',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return data
      }
    },
  },
  {
    'data': 'song',
    'name': 'song__sort_song_name',
    'width': '15rem',
    'className': 'all',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.uuid}">${data.name}</a>`
      }
    },
  },
  { 'data': 'song.category', 'name': 'song__category', 'width': '15rem', 'className': '' },
  {
    'data': 'first_event',
    'name': 'first_event',
    'width': '10rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return renderLink('/events/', data.event_id, data.date.display_day);
      }
    },
  },
  {
    'data': 'last_event',
    'name': 'last_event',
    'width': '10rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return renderLink('/events/', data.event_id, data.date.display_day);
      }
    },
  },
  { 'data': 'song__original', 'name': 'song__original', 'visible': false, 'orderable': false },
]

event_table_columns = [
  {
    'data': 'date',
    'name': 'event_id',
    'type': 'text',
    'width': '1rem',
    'className': 'text-nowrap',
    'render': function (data, type, row, meta) {
      return renderLink('/events/', row.event_id, data.display_day);
    },
  },
  {
    'data': 'has_setlist',
    'name': 'has_setlist',
    'width': '1rem',
    'className': 'text-center text-xs',
    'orderable': false,
    'searchable': false,
    'columnControl': [],
    'render': function (data, type, row, meta) {
      return data ? `<i class="bi bi-check-lg" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Has Setlist"></i>` : ''
    },
  },
  {
    'data': 'artist',
    'name': 'artist__name',
    'className': 'text-wrap',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/bands/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'venue',
    'name': 'venue__name, venue__detail, venue__city__name, venue__city__state__abbrev, venue__city__state__name, venue__city__country__name',
    'className': 'text-nowrap',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        if (row.city) {
          return `<a href="/venues/${data.uuid}">${data.name}</a><br><small>${row.city.formatted}</small>`
        }

        return `<a href="/venues/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'tour',
    'name': 'tour__name',
    'width': '10rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        if (row.leg) {
          return `<a href="/tours/${data.uuid}">${data.name}</a><br><small>${row.leg.name}</small>`
        }

        return `<a href="/tours/${data.uuid}">${data.name}</a>`
      }
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
    'name': 'event__event_id',
    'width': '8rem',
    'className': 'all text-nowrap',
    'searchable': false,
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
        return `<a href="/songs/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 's1_closer',
    'name': 's1_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 's2_opener',
    'name': 's2_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'main_closer',
    'name': 'main_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'encore_opener',
    'name': 'encore_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'show_closer',
    'name': 'show_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.uuid}">${data.name}</a>`
      }
    },
  },
]

function searchBuilder(table, columns) {
  new DataTable.SearchBuilder(table, {
    liveSearch: false,
    depthLimit: 1,
    columns: columns,
  });

  var container = table.searchBuilder.container();
  $('#modal-body').append(container);
}

function slotTable(url) {
  var slotTable = new DataTable('#slotTable', {
    scrollY: '60vh',
    fixedColumns: {
      start: 1
    },
    ajax: {
      'url': url,
    },
    columns: setlist_slots,
    initComplete: function () {
      slotTable.columns().every(function () {
        var columnData = this.data().join(''); // Combine all cell data into one string

        // Check if the combined string is empty
        if (columnData.length === 0) {
          // If empty, hide the column
          this.visible(false);
        }
      });
    }
  });

  searchBuilder(slotTable, [0, 1, 2, 3, 4, 5, 6]);
}