// function tableSearch(table, searchID) {
//     let searchTimeout;

//     $(`#${searchID}`).on('keyup change clear', function () {
//         const value = $(this).val();
//         clearTimeout(searchTimeout);

//         searchTimeout = setTimeout(function () {
//             // API signature: table.search( input, regex, smart, caseInsen )
//             table.search(`${value}`, false, false, true).draw();
//         }, 700);
//     });
// }

function tableSearch(table, searchID) {
    let searchTimeout;
    let lastSearchValue = ''; // Cache the last successfully sent search term

    // Added 'blur' to catch clicking off, and 'search' for the native input 'x' clear button
    $(`#${searchID}`).on('keyup change clear blur search', function (e) {
        const value = $(this).val();

        // 1. If focus is lost (blur), instantly clear the typing timeout
        if (e.type === 'blur') {
            clearTimeout(searchTimeout);
        }

        // 2. Prevent server spam: Halt if the string hasn't changed
        if (value === lastSearchValue) {
            return;
        }

        // 3. Handle immediate execution conditions
        if (e.type === 'blur' || e.type === 'clear' || e.type === 'search') {
            clearTimeout(searchTimeout);
            lastSearchValue = value;
            // API signature: table.search( input, regex, smart, caseInsen )
            table.search(`${value}`, true, false, true).draw();
            return;
        }

        // 4. Fallback to debounced typing search
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function () {
            lastSearchValue = value;
            // API signature: table.search( input, regex, smart, caseInsen )
            table.search(`${value}`, true, false, true).draw();
        }, 700);
    });
}