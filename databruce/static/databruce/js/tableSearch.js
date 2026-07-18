function tableSearch(table, searchID) {
    let searchTimeout;

    $(`#${searchID}`).on('keyup change clear', function () {
        const value = $(this).val();
        clearTimeout(searchTimeout);

        searchTimeout = setTimeout(function () {
            // API signature: table.search( input, regex, smart, caseInsen )
            table.search(`${value}`, false, false, true).draw();
        }, 500);
    });
}