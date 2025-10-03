/**
 * Create category selector for datatable filtering.
 * Created this to simplify adding a category selector to tables,
 * rather than having to manually add the code on each.
 *
 * @param {object} column - The table column to search on.
 * @param {string} label - The label to show before the dropdown, typically Category.
 * @param {array} values - The search values to add to the dropdown.
 *
 * @returns {none} None, simply adds the dropdown.
 */
function categorySelect(column, label, values) {
    var select = document.createElement('label');
    var btn_group = document.createElement('div');
    var btn = document.createElement('btn');
    var dropdown = document.createElement('div');

    // dropdown label
    $(select).attr('for', 'select').addClass('me-2 text-sm').text(`${label}:`);

    // button group
    $(btn_group).addClass('btn-group').attr('id', 'select');

    // add label and button group to dropdown
    $('#dropdown-container').append(select).append(btn_group);

    // dropdown button
    $(btn).addClass('btn btn-primary btn-sm mb-1 mr-2 dropdown-toggle').attr({'id': 'category-select-btn', 'type': 'button', 'data-bs-toggle': 'dropdown', 'aria-expanded': 'false'}).text(values[0].label);

    // dropdown menu
    $(dropdown).addClass('dropdown-menu').attr('id', 'category-select');

    // add dropdown menu to button
    $('#select').append(btn).append(dropdown);

    for (let i in values) {
        var item = document.createElement('a');

        $(item).addClass('dropdown-item dt-button').attr({'href': '#', 'value': values[i].value}).text(values[i].label);

        $('#category-select').append(item);

        $('#category-select .dropdown-item.dt-button').on('click', function() {
            // removes active check from all buttons
            $('#category-select .dropdown-item.dt-button').each(function() {
                $('.check').remove();
            });

            // gets value attribute and searches last column
            column.search($(this).attr('value'), {regex: true}).draw();

            // sets button text to selected
            $('#category-select-btn').text($(this).text());

            // adds check to actively filtered value
            $(this).append('<div class="float-end check">✓</div>');
        });
    };
}