function searchBuilder(table, columns) {
  new DataTable.SearchBuilder(table, {
    liveSearch: false,
    depthLimit: 1,
    columns: columns,
  });


  // 2. Access the container node via the table API chain
  var container = table.searchBuilder.container();
  console.log(container);

  // 3. Append the HTML Node safely to your element
  $('#modal-body').append(container);
}