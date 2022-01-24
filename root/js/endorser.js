$(document).ready(function () {
    $("#new-invitation").click(function () {
        $(".input-group").removeClass("d-none");
        create_invitation();
    });

    conn_tab = $('#connections-tab').DataTable();
    get_connections("http://localhost:8081", conn_tab);
    exch_tab = $('#exchanges-tab').DataTable();
    get_exchanges("http://localhost:8081", exch_tab);
    pres_tab = $('#presentations-tab').DataTable();
    get_presentations("http://localhost:8081", pres_tab);
});

function create_invitation() {
    try {
        $(this).css('color', 'black');
        $.post("/invitation/create", function (data) {
            response = JSON.parse(data);
            invitation = JSON.stringify(response.invitation);
            console.log(invitation);
            $("textarea[name=invitation]").val(invitation);
        })
    } catch (e) {
        console.log(e);
    }
}