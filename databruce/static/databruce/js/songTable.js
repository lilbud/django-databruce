song_table_defs = [
  { targets: '_all', className: 'text-wrap text-xs' },
]

song_table_columns = [
  {
    'data': 'count',
    'name': 'count',
    'width': '1rem',
    'type': 'num',
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
        return `<a href="/songs/${data.slug}">${data.name}</a>`
      }
    },
  },
  { 'data': 'song.category', 'name': 'song__category', 'width': '15rem', 'className': '' },
  {
    'data': 'first_event',
    'name': 'first_event',
    'width': '10rem',
    'type': 'date',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return eventDateFormat(data);
      }
    },
  },
  {
    'data': 'last_event',
    'name': 'last_event',
    'width': '10rem',
    'type': 'date',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return eventDateFormat(data);
      }
    },
  },
  { 'data': 'song__original', 'name': 'song__original', 'visible': false, 'orderable': false },
]

function songTable(url, height, tableID) {
  let searchTimeout;

  if (!tableID) {
    tableID = '#songTable';
  }

  if (!height) {
    height = 'auto';
  }

  var table = new DataTable(tableID, {
    ajax: {
      'url': url,
    },
    layout: {
      topStart: {
        customOrder: {
          selectId: '#songTableOrder'
        }
      }
    },
    pageLength: 100,
    responsive: {
      details: false,
    },
    order: [[0, 'desc']],
    columns: song_table_columns,
    initComplete: function (settings, json) {
      let api = this.api();
      var info = api.page.info();
      console.log($('#song-count-badge'))
      $('#song-count-badge').text(info.recordsTotal);

      const input = $('.song-controls .page-input');
      const prevBtn = $('.song-controls .btn-prev');
      const nextBtn = $('.song-controls .btn-next');
      const totalSpan = $('.song-controls .total-pages');

      // Initial button states
      input.val(info.page + 1);
      prevBtn.attr('disabled', info.page === 0);
      nextBtn.attr('disabled', info.page >= info.pages - 1);

      $('#songTableInfo').text(`Showing ${info.start + 1} to ${info.end} of ${info.recordsTotal} entries`);

      api.on('draw', () => {
        const pageInfo = api.page.info();

        input.val(pageInfo.page + 1);
        input.attr('max', pageInfo.pages);

        totalSpan.text(`of ${pageInfo.pages || 1}`);

        // Handle button states
        prevBtn.attr('disabled', pageInfo.page === 0);
        nextBtn.attr('disabled', pageInfo.page >= pageInfo.pages - 1);

        // FIX: Swapped out 'info' for 'pageInfo' so it updates dynamically
        $('songTableInfo').text(`Showing ${pageInfo.start + 1} to ${pageInfo.end} of ${pageInfo.recordsTotal} entries`);
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

  tableSearch(table, 'songSearch');

  $('#categoryFilter').on('change', function () {
    var selectedValue = this.value;
    table.order([[0, 'desc'], [1, 'asc']]).column(5).search(selectedValue ? selectedValue : '', true, false).draw();
  });
}