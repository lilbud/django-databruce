function get_options({ ajax_url = false }) {
  var options = {
    theme: "bootstrap-5",
    selectionCssClass: "form-select",
    dropdownCssClass: "form-control",
    minimumInputLength: 3,
    dropdownAutoWidth: true,
    dropdownPosition: 'below',
    allowClear: true,
    placeholder: '',
    width: '100%', // need to override the changed default\
    ajax: {
      delay: 500,
      url: '/api/v1/',
      dataType: 'json',
      data: function (params) {
        return {
          name: params.term,
        }
      },
      processResults: function (data) {
        // Map your custom data to the Select2 format
        return {
          results: $.map(data.results, function (item) {
            return {
              id: item.id,   // Replace with your ID field name
              text: item.name // Replace with your text field name
            };
          })
        };
      }
    }
  };

  if (ajax_url) {
    options.ajax.url += ajax_url;
  };

  return options;
}

// this counter updates when a row is added or removed, used to set row/field specific IDs.
const totalForms = document.getElementById("id_form-TOTAL_FORMS");

/**
 * Adjusts conjunctions between song rows.
 * Modified version of the one from Jerrybase, I couldn't figure this out
 * My changes are limited to condensing a few things using jQuery
 */
function adjust_conjunctions() {
  // remove conjunction row if it is first or last in search div

  var row = $('#setlist-search').find('.conjunction-row')

  $(row).first().remove();
  $(row).last().remove();

  // loop song rows
  $('#setlist-search').find('.song-row').each(function () {
    var next_row = $(this).next();

    if (next_row.hasClass('.conjunction-row') && next_row.next('.conjunction-row')) {
      next_row.next('.conjunction-row').remove();
    } else if ($(this).next().hasClass('song-row')) {
      $(this).after($('#conjunction').html());
    }
  });

  // update conjunction text when select updated
  $('.conjunction').html($('#conjunctionSelect').val());
};

/**
 * Removes the selected row from the setlist search, decrement ID counter.
 *
 * @param {object} button - rows remove button, used to find parent search row.
 */
function removeForm(e) {
  // remove last song row
  $(e).closest('.song-row').remove();

  // increment value of management form total count
  totalForms.value--;

  adjust_conjunctions();
}

/**
 * Show/hide the song2 field when position = followed_by
 * @param {object} row - parent row of the select element
 * @param {object} select - select element that triggered the change
 */
function positionChange(row, select) {
  var select_row = $(select).parent().parent();

  if ($(select).val() == "followed_by") {
    select_row.find("[id*=song2]").parent().show();
    select_row.find("[id*=song2]").select2(get_options({ ajax_url: 'songs/' }));
  } else {
    select_row.find("[id*=song2]").parent().hide();
  }
}

/**
 * Adds row to setlist search container, enables select2 on those fields as well
 */
function addForm() {
  // row count for setting IDs
  var count = totalForms.value;

  // grab hidden "template" row and add to search container
  $("#setlist-search").append($("#new_row").html());

  var row = $('#setlist-search').find('.song-row').last();

  // remove display none and show the new row
  row.attr('id', `song-row-${count}`).removeClass("d-none");

  // adding incremented ids to fields
  row.find('.choice').attr({ 'id': `id_form-${count}-choice`, 'name': `form-${count}-choice` });
  row.find('.song1').attr({ 'id': `id_form-${count}-song1`, 'name': `form-${count}-song1` }).select2(get_options({ ajax_url: 'songs/' }));
  row.find('.position').attr({ 'id': `id_form-${count}-position`, 'name': `form-${count}-position` });
  row.find('.song2').attr({ 'id': `id_form-${count}-song2`, 'name': `form-${count}-song2` }).parent().hide();

  $('.position').change(function () {
    positionChange(row, this);
  });

  adjust_conjunctions();

  // increment value of management form total count
  totalForms.value++;
};



$(document).ready(function () {
  var row = $('#setlist-search').find('.song-row').last();

  $('#city').select2(get_options({ ajax_url: 'cities/' }));
  $('#state').select2(get_options({ ajax_url: 'states/' }));
  $('#country').select2(get_options({ ajax_url: 'countries/' }));
  $('#tour').select2(get_options({ ajax_url: 'tours/' }));
  $('#relation').select2(get_options({ ajax_url: 'relations/' }));
  $('#band').select2(get_options({ ajax_url: 'bands/' }));
  $('#venue').select2(get_options({ ajax_url: 'venues/' }));

  row.find('.song2').parent().hide();
  row.find('.song1').select2(get_options({ ajax_url: 'songs/' }));

  $('[class*=position]').change(function () {
    positionChange(row, this);
  });

  $('#conjunctionSelect').change(function () {
    adjust_conjunctions();
  });
});