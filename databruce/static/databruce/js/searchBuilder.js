function searchBuilder(table, columns) {
  const modal = document.getElementById("modal-body");

  new DataTable.SearchBuilder(table, {
    liveSearch: false,
    depthLimit: 1,
    columns: columns,
  });

  // 2. Access the container node via the table API chain
  var container = table.searchBuilder.container();

  modal.insertAdjacentHTML('afterend', container)
}