function select2() {
    var selectOptions = {
        theme: "bootstrap-5",
        selectionCssClass: "form-select",
        dropdownCssClass: "form-control",
        minimumInputLength: 3,
        dropdownPosition: 'below'
    };

    let forms = document.querySelectorAll("#songSelect");
    let song2forms = document.querySelectorAll("#song2Select");

    forms.forEach(element => {
        $(`#${element.id}`).select2(selectOptions);
    });

    song2forms.forEach(element => {
        $(`#${element.id}`).parent().hide();
    });

    $('#positionSelect').change(function () {
        if (this.value == 'followed_by') {
            song2forms.forEach(element => {
                console.log(element.id);
                $(`#${element.id}`).parent().show();
                $(`#${element.id}`).select2(selectOptions);
            });
        } else {
            $("#song2Select").parent().hide();
        };
    });

    document.querySelector("#reset").addEventListener('click', function (e) {
        $("#song2Select").parent().hide();
    });
}