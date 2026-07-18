function searchBuilder(table, columns) {
    new DataTable.SearchBuilder(table, {
        liveSearch: false,
        depthLimit: 1,
        columns: sb_columns,
    });

    var container = table.searchBuilder.container();
    $('#modal-body').append(container);
}