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