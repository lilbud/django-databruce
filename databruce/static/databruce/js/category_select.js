/**
 * Create category selector for filtering datatables.
 * Created this to simplify adding a category selector to tables,
 * rather than having to manually add the code on each.
 *
 * @param {object} column - The table column to search on.
 * @param {string} label - The label to show before the dropdown, typically Category.
 * @param {array} values - The search values to add to the dropdown.
 *
 * @returns {none} None, simply adds the dropdown.
 */
function categorySelect(label, values) {
    var select = document.createElement('label');
    var btn_group = document.createElement('div');
    var btn = document.createElement('button');
    var dropdown = document.createElement('div');

    // dropdown label
    $(select).attr('for', 'select').addClass('me-2 text-sm my-auto').text(`${label}:`);

    // button group
    $(btn_group).attr('id', 'select').addClass('dt-buttons btn-group');

    // add label and button group to dropdown
    $('#dropdown-container').append(select).append(btn_group);

    // dropdown button
    $(btn).addClass('btn btn-primary btn-sm me-2 dropdown-toggle buttons-collection').attr({'id': 'category-select-btn', 'type': 'button', 'data-bs-toggle': 'dropdown', 'aria-expanded': 'false'}).text(values[0].label);

    // dropdown menu
    $(dropdown).addClass('dropdown-menu dt-button-collection').attr('id', 'category-select');

    // add dropdown menu to button
    $('#select').append(btn).append(dropdown);

    for (let i in values) {
        var item = document.createElement('a');

        $(item).addClass('dropdown-item dt-button pe-auto').attr({'value': values[i].value, 'href':'#'}).text(values[i].label);

        $('#category-select').append(item);
    };
};

function categorySearch(column) {
    $('#category-select .dropdown-item.dt-button').on('click', function() {
        column.search($(this).attr('value'), {regex: true}).draw();

        // remove checks from all items
        $(this).parent().find('.dropdown-item').each(function(){
            $('.check').remove();
        });

        // set select text to current value
        $('#category-select-btn').text($(this).text());

        // add check to selected
        $(this).append('<div class="float-end check">✓</div>');
    });
}