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

const wrapFormEl = document.getElementById("search-form");
const submitBtn = document.getElementById("submit-button");
const totalFormsInput = document.getElementById("id_form-TOTAL_FORMS");

function song2(e) {
    const song2 = $(e).parent().parent().find("[class*=song2]")

    if (e.value == "followed_by") {
        song2.parent().show();
        select2(song2);
    } else {
        song2.parent().hide();
    }
}

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
        const removeDiv = document.getElementById(e.closest("[id^=song_row]").id);
        wrapFormEl.removeChild(removeDiv);
        totalFormsInput.value--;
    }
}

$(document).ready(function () {
    $("[class*=song2]").each(function () {
        $(`#${this.id}`).parent().hide();
    });

    $("#id_form-0-song1").each(function () {
        select2(this);
    });

    $("[class*=position]").change(function () {
        song2(this);
    });
});