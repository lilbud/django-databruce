event_table_columns = [
  {
    'data': 'date',
    'name': 'event_id',
    'type': 'text',
    'width': '6rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      if (row.early_late) {
        date = `${data}<br>(${row.early_late})`
      } else {
        date = data
      }

      return `<a href="/events/${row.event_id}">${date}</a>`
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
      if (data) {
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
      if (data) {
        if (row.city) {
          return `<a href="/venues/${data.uuid}">${data.name}</a><br><small>${row.city}</small>`
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
      if (data) {
        if (row.leg) {
          return `<a href="/tours/${data.uuid}">${data.name}</a><br><small>${row.leg}</small>`
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
          return `<span class="text-danger fw-semibold">[${row.type[0]}] ${data}</span>`
        }
        return `<span class="text-danger fw-semibold">[${row.type[0]}]</span>`
      }

      return data;
    },
  },
  {
    'data': 'public',
    'name': 'public',
    'visible': false,
    'orderable': false,
    'render': function (data, type, row, meta) {
      if (data != null) {
        return data;
      }
    },
  },
]

function eventTable(url) {
  var table = new DataTable('#eventTable', {
    ajax: {
      'url': url,
    },
    columns: event_table_columns,
    columnDefs: [
      { 'target': '_all', columnControl: [], ordering: { indicators: false } },
    ],
    serverSide: true,
    processing: true,
    initComplete: function (settings, json) {
      var api = this.api();
      var info = api.page.info();
      $('#event-count-badge').text(info.recordsTotal);
    }
  });

  let dropdown = $('#columnOrder');

  // 3. Listen for dropdown changes to reorder the table
  dropdown.on('change', function () {
    let rawValue = $(this).val();

    // Don't trigger sorting if the default placeholder option is selected
    if (!rawValue) return;

    // Split the combined string value (e.g., "2-desc" becomes index 2, direction "desc")
    let parts = rawValue.split('-');
    let selectedColumnIndex = parseInt(parts[0], 10);
    let direction = parts[1];

    console.log(selectedColumnIndex, direction)

    // Apply ordering rule and refresh interface layout
    table.order([selectedColumnIndex, direction]).draw();
  });

  $(window).on('resize', function () {
    table.columns.adjust();
  });

  tableSearch(table, 'search');

  $('#PublicityFilter').on('change', function () {
    var selectedValue = this.value;
    table.order([[0, 'asc']]).column(6).search(selectedValue ? selectedValue : '', true, false).draw();
  });
}