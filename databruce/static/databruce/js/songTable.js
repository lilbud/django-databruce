song_table_defs = [
    { targets: '_all', className: 'text-wrap text-xs' },
]

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
                return renderLink('/events/', data.event_id, data.date_day);
            }
        },
    },
    {
        'data': 'last_event',
        'name': 'last_event',
        'width': '10rem',
        'render': function (data, type, row, meta) {
            if (type === 'display' && data) {
                return renderLink('/events/', data.event_id, data.date_day);
            }
        },
    },
    { 'data': 'song__original', 'name': 'song__original', 'visible': false, 'orderable': false },
]

function songTable(url, height) {
    let searchTimeout;

    if (!height) {
        height = 'auto';
    }

    var table = new DataTable('#songTable', {
        ajax: {
            'url': url,
        },
        scrollY: height,
        columns: song_table_columns,
        initComplete: function (settings, json) {
            var info = this.api().page.info();
            $('#song-count-badge').text(info.recordsTotal);
        }
    });

    $('#song-search').on('keyup change clear', function () {
        const value = $(this).val();
        clearTimeout(searchTimeout);

        searchTimeout = setTimeout(function () {
            table.search(value).draw();
        }, 500);
    });

    $('#categoryFilter').on('change', function () {
        var selectedValue = this.value;
        table.order([[0, 'desc'], [1, 'asc']]).column(5).search(selectedValue ? selectedValue : '', true, false).draw();
    });
}