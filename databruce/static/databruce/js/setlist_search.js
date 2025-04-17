$(document).ready(function () {
    var selectOptions = {
        theme: "bootstrap-5",
        selectionCssClass: "form-select",
        dropdownCssClass: "form-control",
        minimumInputLength: 3,
        dropdownPosition: 'below'
    };

    $('#songSelect').select2(selectOptions);
});