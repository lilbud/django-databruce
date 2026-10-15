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

      const tableInfo = document.getElementById('slotTableInfo');
      tableInfo.textContent = `Showing ${info.start + 1} to ${info.end} of ${info.recordsTotal} entries`;

    }
  });

  tableSearch(slotTable, 'slotSearch');
}