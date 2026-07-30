event_table_columns = [
    {
        'data': 'date',
        'name': 'event_id',
        'type': 'text',
        'width': '1rem',
        'className': 'text-nowrap',
        'render': function (data, type, row, meta) {
            return `<a href="/events/${row.event_id}">${data.display_day}</a>`
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
                    return `<span class="text-danger fw-semibold">[${row.type}] ${data}</span>`
                }
                return `<span class="text-danger fw-semibold">[${row.type}]</span>`
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
        serverSide: true,
        processing: true,
        paging: false,
        pageLength: -1,
        // initComplete: function (settings, json) {
        //     var info = this.api().page.info();
        //     $('#event-count-badge').text(info.recordsTotal);
        // }
    });

    tableSearch(table, 'search');

    $('#PublicityFilter').on('change', function () {
        var selectedValue = this.value;
        table.order([[0, 'asc']]).column(6).search(selectedValue ? selectedValue : '', true, false).draw();
    });
}