event_table_columns = [
  {
    'data': 'date',
    'name': 'event_id',
    'type': 'text',
    'width': '6rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      const date = new Date(data);
      const dayText = date.toLocaleDateString('en-US', { weekday: 'long' });
      var dateItem;

      if (row.early_late) {
        dateItem = `<span class="text-primary">${data}</span><br><small>${row.early_late} • ${dayText}</small>`
      } else {
        dateItem = `${data}<br><small>${dayText}</small>`
      }

      return `<a href="/events/${row.event_id}">${dateItem}</a>`
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
      return data ? `<i class="bi bi-check-lg"></i>` : ''
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
    'className': 'min-desktop',
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

      const input = $('.page-input');
      const prevBtn = $('.btn-prev');
      const nextBtn = $('.btn-next');
      const totalSpan = $('.total-pages');

      // Initial button states
      input.val(info.page + 1);
      prevBtn.attr('disabled', info.page === 0);
      nextBtn.attr('disabled', info.page >= info.pages - 1);

      $('.eventTable_info').text(`Showing ${info.start + 1} to ${info.end} of ${info.recordsTotal} entries`);

      api.on('draw', () => {
        const pageInfo = api.page.info();

        input.val(pageInfo.page + 1);
        input.attr('max', pageInfo.pages);

        totalSpan.text(`of ${pageInfo.pages || 1}`);

        // Handle button states
        prevBtn.attr('disabled', pageInfo.page === 0);
        nextBtn.attr('disabled', pageInfo.page >= pageInfo.pages - 1);

        // FIX: Swapped out 'info' for 'pageInfo' so it updates dynamically
        $('.eventTable_info').text(`Showing ${pageInfo.start + 1} to ${pageInfo.end} of ${pageInfo.recordsTotal} entries`);
      });

      totalSpan.text(`of ${info.pages || 1}`);

      nextBtn.on('click', function () {
        table.page('next').draw(false);
      });

      prevBtn.on('click', function () {
        table.page('previous').draw(false);
      });

      input.on('change', function () {
        let val = parseInt(this.value, 10) - 1;
        const max = api.page.info().pages - 1;
        if (val < 0) val = 0;
        if (val > max) val = max;

        input.attr('value', val);

        api.page(val).draw('page');
      });
    }
  });

  let dropdown = $('.column-order');

  table.on('xhr.dt', function (e, settings, json) {
    if (!json || !json.data) return;

    // Re-render your card layout using the current page's results
    renderCards(json.data);
  });

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
  tableSearch(table, 'cardSearch');

  $('.publicity-filter').on('change', function () {
    var selectedValue = this.value;
    table.order([[0, 'asc']]).column(6).search(selectedValue ? selectedValue : '', true, false).draw();
  });
}