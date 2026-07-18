function eventTableSearch(url) {
    let searchTimeout;

    var table = new DataTable('#eventTable', {
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
        columns: event_table_columns,
        initComplete: function (settings, json) {
            var info = this.api().page.info();
            $('#event-count-badge').text(info.recordsTotal);
        }
    });

    tableSearch(table, 'search');

    $('#PublicityFilter').on('change', function () {
        var selectedValue = this.value;
        table.order([[0, 'asc']]).column(6).search(selectedValue ? selectedValue : '', true, false).draw();
    });
}