$(document).ready(function () {
    $("#new-invitation").click(function () {
        $(".input-group").removeClass("d-none");
    });

    $("textarea[name=invitation]").on('input', function (e) {
        try {
            data = JSON.parse(this.value);
            $(this).css('color', 'black');
            $.post("/invitation/accept", this.value, function (data) {
                console.log(data);
            })
        } catch (e) {
            console.log("err");
            $(this).css('color', 'red');
            return;
        }
        return;
    })

    conn_tab = $('#connections-tab').DataTable();
    get_connections("http://localhost:8080", conn_tab);
    exch_tab = $('#exchanges-tab').DataTable();
    get_exchanges("http://localhost:8080", exch_tab);
    cred_tab = $('#credentials-tab').DataTable();
    get_credentials("http://localhost:8080", cred_tab);
    pres_tab = $('#presentations-tab').DataTable();
    get_presentations("http://localhost:8080", pres_tab);
});