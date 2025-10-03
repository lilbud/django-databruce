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

// this counter updates when a row is added or removed, used to set row/field specific IDs.
var song_count = -1;

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
    $(e).closest('.song-row').remove();
    song_count -= 1;
    
    adjust_conjunctions();
}

/**
 * Adds row to setlist search container, enables select2 on those fields as well
 */
function addForm() {
    // row count for setting IDs
    song_count += 1;

    // grab hidden "template" row and add to search container
    $("#setlist-search").append($("#new_row").html());

    var row = $('#setlist-search').find('.song-row').last();

    // remove display none and show the new row
    row.attr('id', `song-row-${song_count}`).removeClass("d-none");

    // adding incremented ids to fields
    row.find('[class*=choice]').attr("id", `form-${song_count}-choice`);
    row.find('[class*=song1]').attr("id", `form-${song_count}-song1`).select2(selectOptions);
    row.find('[class*=position]').attr("id", `form-${song_count}-position`);
    row.find('[class*=song2]').attr("id", `form-${song_count}-song2`).parent().hide();

    // show/hide the song2 field when position = followed_by
    row.find('[class*=position]').change(function () {
        if ($(this).val() == "followed_by") {
            row.find(`#form-${song_count}-song2`).parent().show();
            row.find(`#form-${song_count}-song2`).select2(selectOptions);
        } else {
            row.find(`#form-${song_count}-song2`).parent().hide();
        }
    });

    adjust_conjunctions();
};

$(document).ready(function () {  
  // add first form
  addForm();

  adjust_conjunctions();

  $('#conjunctionSelect').change(function() {
      adjust_conjunctions();
  });
  
  $('.select2').each(function() {
    $(this).select2(selectOptions);
  });
});