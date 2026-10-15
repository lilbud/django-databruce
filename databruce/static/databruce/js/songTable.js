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
    'name': 'song__slug, song__name',
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
      return eventDateFormat(data);
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
      const songCountBadge = document.getElementById('song-count-badge');
      songCountBadge.textContent = info.recordsTotal;

      const input = document.querySelectorAll('.song-controls .page-input');
      const prevBtn = document.querySelectorAll('.song-controls .btn-prev');
      const nextBtn = document.querySelectorAll('.song-controls .btn-next');
      const totalSpan = document.querySelectorAll('.song-controls .total-pages');
      const tableInfo = document.getElementById('songTableInfo');

      // Initial button states
      // input.value = info.page + 1;
      input.forEach(el => {
        el.value = info.page + 1;

        el.addEventListener('change', function () {
          let val = parseInt(this.value, 10) - 1;
          const max = api.page.info().pages - 1;

          if (val < 0) val = 0;
          if (val > max) val = max;

          this.value = val;
          api.page(val).draw('page');
        })
      });

      prevBtn.forEach(el => {
        el.disabled = info.page === 0;

        el.addEventListener('click', function () {
          prevPage(table);
        });
      });

      nextBtn.forEach(el => {
        el.disabled = info.page >= info.pages - 1;

        el.addEventListener('click', function () {
          nextPage(table);
        });
      });

      tableInfo.textContent = `Showing ${info.start + 1} to ${info.end} of ${info.recordsTotal} entries`;

      api.on('draw', () => {
        const pageInfo = api.page.info();

        input.forEach(el => {
          el.value = pageInfo.page + 1;
          el.max = pageInfo.pages;
        });

        totalSpan.forEach(el => {
          el.textContent = `of ${pageInfo.pages || 1}`;
        });

        prevBtn.forEach(el => {
          el.disabled = pageInfo.page === 0;
        });

        nextBtn.forEach(el => {
          el.disabled = pageInfo.page >= pageInfo.pages - 1;
        });

        tableInfo.textContent = `Showing ${pageInfo.start + 1} to ${pageInfo.end} of ${pageInfo.recordsTotal} entries`;
      });

      // totalSpan.text(`of ${info.pages || 1}`);
      totalSpan.forEach(el => {
        el.textContent = `of ${info.pages || 1}`;
      })
    }
  });

  tableSearch(table, 'songSearch');

  const categoryFilter = document.getElementById('categoryFilter');

  if (categoryFilter) {
    categoryFilter.addEventListener('change', function () {
      var selectedValue = this.value;
      table.order([[0, 'desc'], [1, 'asc']]).column(5).search(selectedValue ? selectedValue : '', true, false).draw();
    });
  }
}