$(document).ready(function () {
  $('#start_date').mask('0000-00-00');
  $('#end_date').mask('0000-00-00');

  var selectOptions = {
    theme: "bootstrap-5",
    selectionCssClass: "form-select",
    dropdownCssClass: "form-control",
    minimumInputLength: 3,
    dropdownPosition: 'below',
    allowClear: true,
    placeholder: '',
    width: 'resolve' // need to override the changed default
  };

  document.querySelectorAll(".select2").forEach(element => {
    $(`#${element.id}`).select2(selectOptions);
  });
});

