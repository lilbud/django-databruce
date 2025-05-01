function select2() {
    var selectOptions = {
        theme: "bootstrap-5",
        selectionCssClass: "form-select",
        dropdownCssClass: "form-control",
        minimumInputLength: 3,
        dropdownPosition: 'below'
    };

    document.querySelectorAll("#songSelect").forEach(element => {
        $(`#${element.id}`).select2(selectOptions);
    });

    document.querySelectorAll("#song2Select").forEach(element => {
        $(`#${element.id}`).parent().hide();
    });

    $('#positionSelect').change(function () {
        if (this.value == 'followed_by') {
            document.querySelectorAll("#song2Select").forEach(element => {
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