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

const wrapFormEl = document.getElementById("setlist-search");
const submitBtn = document.getElementById("submit-button");
const totalFormsInput = document.getElementById("id_form-TOTAL_FORMS");
const addFormBtn = document.getElementById("add-form-btn");

// shows or hides the song2 select based on the value of position
function song2(e) {
    const song2 = $(e).parent().parent().find("[class*=song2]")

    if (e.value == "followed_by") {
        song2.parent().show();
        song2.select2(selectOptions);
    } else {
        song2.parent().hide();
    }
}

// adds form when add row button is clicked
function addForm() {
    const totalFormsValue = totalFormsInput.value;

    var clonedDiv = $("#new_row").clone();

    clonedDiv.attr("id", `song_row-${totalFormsValue}`).removeClass("d-none");

    clonedDiv.find('[class*=choice]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-choice").attr("name", "form-" + totalFormsValue + "-choice");
    });

    clonedDiv.find('[class*=song1]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-song1").attr("name", "form-" + totalFormsValue + "-song1").select2(selectOptions);
    });

    clonedDiv.find('[class*=position]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-position").attr("name", "form-" + totalFormsValue + "-position");
    });

    clonedDiv.find('[class*=song2]').each(function () {
        $(this).attr("id", "id_form-" + totalFormsValue + "-song2").attr("name", "form-" + totalFormsValue + "-song2").parent().hide();
    });

    $(wrapFormEl).append(clonedDiv);
    totalFormsInput.value++;

    clonedDiv.find('[class*=position]').change(function () {
        song2(this);
    });
};

function resetForm() {
    location.reload();
}

function removeForm(e) {
    if (totalFormsInput.value > 0) {
        $(e).parent().parent().remove();
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
        $(this).select2(selectOptions);
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