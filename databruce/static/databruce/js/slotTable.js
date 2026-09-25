setlist_slots = [
  {
    'data': 'event',
    'name': 'event__event_id',
    'width': '8rem',
    'type': 'date',
    'className': 'all text-nowrap',
    'render': function (data, type, row, meta) {
      return eventDateFormat(data);
    },
  },
  {
    'data': 'show_opener',
    'name': 'show_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.slug}">${data.name}</a>`
      }
    },
  },
  {
    'data': 's1_closer',
    'name': 's1_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.slug}">${data.name}</a>`
      }
    },
  },
  {
    'data': 's2_opener',
    'name': 's2_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.slug}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'main_closer',
    'name': 'main_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.slug}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'encore_opener',
    'name': 'encore_opener__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.slug}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'show_closer',
    'name': 'show_closer__name',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (type === 'display' && data) {
        return `<a href="/songs/${data.slug}">${data.name}</a>`
      }
    },
  },
]

function slotTable(url) {
  var slotTable = new DataTable('#slotTable', {
    fixedColumns: true,
    ajax: {
      'url': url,
    },
    order: [[0, 'asc']],
    layout: {
      topStart: {
        customOrder: {
          selectId: '#slotTableOrder'
        }
      }
    },
    pageLength: -1,
    responsive: {
      details: false,
    },
    columns: setlist_slots,
    initComplete: function () {
      let api = this.api();
      let info = api.page.info();

      api.columns().every(function () {
        var columnData = this.data().join(''); // Combine all cell data into one string

        // Check if the combined string is empty
        if (columnData.length === 0) {
          // If empty, hide the column
          this.visible(false);
        }
      });

      const input = $('#slotTableControls .page-input');
      const prevBtn = $('#slotTableControls .btn-prev');
      const nextBtn = $('#slotTableControls .btn-next');
      const totalSpan = $('#slotTableControls .total-pages');
      const tableInfo = $('#slotTableInfo');

      // Initial button states
      input.val(info.page + 1);
      prevBtn.attr('disabled', info.page === 0);
      nextBtn.attr('disabled', info.page >= info.pages - 1);

      tableInfo.text(`Showing ${info.start + 1} to ${info.end} of ${info.recordsTotal} entries`);

      api.on('draw', () => {
        const pageInfo = api.page.info();

        input.val(pageInfo.page + 1);
        input.attr('max', pageInfo.pages);

        totalSpan.text(`of ${pageInfo.pages || 1}`);

        // Handle button states
        prevBtn.attr('disabled', pageInfo.page === 0);
        nextBtn.attr('disabled', pageInfo.page >= pageInfo.pages - 1);

        // FIX: Swapped out 'info' for 'pageInfo' so it updates dynamically
        tableInfo.text(`Showing ${pageInfo.start + 1} to ${pageInfo.end} of ${pageInfo.recordsTotal} entries`);
      });

      totalSpan.text(`of ${info.pages || 1}`);

      nextBtn.on('click', function () {
        slotTable.page('next').draw(false);
      });

      prevBtn.on('click', function () {
        slotTable.page('previous').draw(false);
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

  tableSearch(slotTable, 'slotSearch');
}