$(document).ready(function () {
    $('#start_date').mask('0000-00-00');
    $('#end_date').mask('0000-00-00');

    var selectOptions = {
        theme: "bootstrap-5",
        selectionCssClass: "form-select",
        dropdownCssClass: "form-control",
        minimumInputLength: 3,
        dropdownPosition: 'below'
    };

    $('#citySelect').select2(selectOptions);
    $('#stateSelect').select2(selectOptions);
    $('#countrySelect').select2(selectOptions);
    $('#musicianSelect').select2(selectOptions);
    $('#bandSelect').select2(selectOptions);
});