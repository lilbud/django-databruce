function songTable(url, height) {
    let searchTimeout;

    if (!height) {
        height = 'auto';
    }

    var table = new DataTable('#songTable', {
        layout: {
            topStart: null,
            bottomStart: null,
            topEnd: null,
            bottomEnd: null,
            top: ['customInputPaging', 'info'],
            bottom: ['customInputPaging', 'info'],
        },
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