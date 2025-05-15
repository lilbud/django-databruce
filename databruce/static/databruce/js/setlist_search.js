function select2(e) {
    var selectOptions = {
        theme: "bootstrap-5",
        selectionCssClass: "form-select",
        dropdownCssClass: "form-control",
        minimumInputLength: 3,
        dropdownPosition: 'below'
    };

    $(e).select2(selectOptions);
}

const wrapFormEl = document.getElementById("setlist-search");
const submitBtn = document.getElementById("submit-button");
const totalFormsInput = document.getElementById("id_form-TOTAL_FORMS");
const conjunctionSelect = document.getElementById("conjunctionSelect");

// shows or hides the song2 select based on the value of position
function song2(e) {
    const song2 = $(e).parent().parent().find("[class*=song2]")

    if (e.value == "followed_by") {
        song2.parent().show();
        select2(song2);
    } else {
        song2.parent().hide();
    }
}

// adds form when add row button is clicked
function addForm() {
    const totalFormsValue = totalFormsInput.value;

    var clonedDiv = $("#new_row").clone();

    clonedDiv.attr("id", `song_row-${totalFormsValue}`);
    clonedDiv.removeClass("invisible");

    clonedDiv.find('[class*=choice]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-choice");
        $(this).attr("name", "form-" + totalFormsValue + "-choice");
    });

    clonedDiv.find('[class*=song1]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-song1");
        $(this).attr("name", "form-" + totalFormsValue + "-song1");
        select2(this);
    });

    clonedDiv.find('[class*=position]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-position");
        $(this).attr("name", "form-" + totalFormsValue + "-position");
    });

    clonedDiv.find('[class*=song2]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-song2");
        $(this).attr("name", "form-" + totalFormsValue + "-song2");
        $(this).hide();
    });

    const conjunction = document.createElement("div");
    conjunction.innerHTML = `<div class="col-8 offset-2" id="conjunctionText">${conjunctionSelect.value.toUpperCase()}</div>`;
    conjunction.classList.add("row", "mb-2", "conjunctionDiv");
    console.log(conjunction);

    wrapFormEl.appendChild(conjunction);

    $(submitBtn).before(clonedDiv);
    totalFormsInput.value++;

    clonedDiv.find('[class*=position]').change(function () {
        song2(this);
    });
};

const addFormBtn = document.getElementById("add-form-btn");
addFormBtn.addEventListener('click', addForm);

function removeForm(e) {
    if (totalFormsInput.value > 0) {
        $(e).parent().parent().remove();


        // removes a conjunction div if it is first or last
        if ($(wrapFormEl).find("div:first").hasClass('conjunctionDiv')) {
            console.log($(wrapFormEl).find("div:first"));
            $(wrapFormEl).find("div:first").remove();
        };

        if ($(wrapFormEl).find("div:last").hasClass('conjunctionDiv')) {
            $(wrapFormEl).find("div:last").remove();
        };

        $(wrapFormEl).find("[id^=song_row]").each(function () {
            var next_row = $(this).next();
            if (next_row.hasClass('conjunctionDiv')) {
                var row_after_next = next_row.next()
                if (row_after_next.hasClass('conjunctionDiv')) {
                    //two conjunctions in a row so remove
                    row_after_next.remove()
                }
            } else if (next_row.hasClass('song-row')) {
                //song row with no conjunction between
                $(this).after($('.conjunctionDiv').html())
            }
        });

        totalFormsInput.value--;
    }
}

$(document).ready(function () {
    // hide all song2 selects by default
    $("[class*=song2]").each(function () {
        $(`#${this.id}`).parent().hide();
    });

    // apply select2 to the first song select
    $("#id_form-0-song1").each(function () {
        select2(this);
    });

    // apply select2 to song2 when position = followed by
    $("[class*=position]").change(function () {
        song2(this);
    });

    // changes the conjunction between setlist search rows when select changed
    $("[id=conjunctionSelect]").change(function () {
        document.querySelectorAll('#conjunctionText').forEach(element => {
            element.innerHTML = this.value.toUpperCase();
        });
    });
});