$(document).ready(function () {    
    $("#new-cred-request").click(function (){
        if($("#request-cred-form").is(":visible")){
            send_credential_request();
        } else{
            $("#request-cred-form").show(); 
        }
    })
    $("#request-cred-form").hide();

    $("#store-cred-request").click(function (){
        store_credential_request();
        $("#store-cred-form").hide();
    })
    $("#store-cred-form").hide();

    $("#new-pres-request").click(function (){
        if($("#request-pres-form").is(":visible")){
            send_presentation_request();
            $("#request-cred-form").hide();
        } else{
            $("#request-pres-form").show(); 
        }
    })
    $("#request-pres-form").hide();

    $("#new-pres-response").click(function (){
        send_presentation_response();
        $("#send-pres-form").hide();
    })
    $("#send-pres-form").hide();

    $(".nav-link").click(function () {
        id = "#" + $(this).text();
        if (!$(this).hasClass("active")) {
            $(".nav-link").removeClass("active");
            $(this).addClass("active");
            $("main").hide();
            $(id).show();
        }
    })

    $("main").hide();
    $("#Connections").show();

    get_issuer_dids();
    get_subject_dids();
});

function parse_row(row) {
    new_row = []
    for (i = 0; i < row.length; i++) {
        if (row[i] == undefined)
            new_row.push("null")
        else
            new_row.push(row[i])
    }
    return new_row
}

function get_connections(server, table) {
    try {
        $.get(server + "/connections", function (response) {
            response.results.forEach(element => {
                row = [
                    element.connection_id,
                    element.my_did,
                    element.their_did,
                    element.their_role,
                    element.state,
                    element.rfc23_state
                ];
                table.row.add(parse_row(row)).draw(false);
                if(element.state == "active" || element.state == "response"){
                    $("#connection-id").append(create_option(element.connection_id, element.connection_id))
                    $("#connection-id-pres").append(create_option(element.connection_id, element.connection_id))
                }
            });
        })
    } catch (e) {
        console.log(e);
    }
}

if (!Date.prototype.toISOStringNoMilli) {
    (function() {
        function pad(number) {
            if (number < 10) {
                return '0' + number;
            }
            return number;
        }
        
        Date.prototype.toISOStringNoMilli = function() {
        return this.getUTCFullYear() +
            '-' + pad(this.getUTCMonth() + 1) +
            '-' + pad(this.getUTCDate()) +
            'T' + pad(this.getUTCHours()) +
            ':' + pad(this.getUTCMinutes()) +
            ':' + pad(this.getUTCSeconds()) +
            'Z';
        };
    })()
}

function create_option(value, name){
    option = document.createElement("option");
    option.value = value;
    option.innerHTML = name;
    return option;
}

function get_issuer_dids(){
    try {
        $.get("http://localhost:8080/wallet/did?method=key", function (response) {
            results = response.results;
            results.forEach(element => {
                $("#my-did").append(create_option(element.did, element.did));
            });
        })
    } catch (e) {
        console.log(e);
    }
}

function get_subject_dids(){
    try {
        $.get("http://localhost:8081/wallet/did?method=key", function (response) {
            results = response.results;
            results.forEach(element => {
                $("#issuer-did").append(create_option(element.did, element.did));
            });
        })
    } catch (e) {
        console.log(e);
    }
}

function addTooltip(element, title, position="top"){
    $(element).attr("data-bs-toggle", "tooltip");
    $(element).attr("data-bs-placement", position);
    $(element).attr("title", title);
    return new bootstrap.Tooltip(element);
}

function get_exchanges(server, table){
    try {
        $.get(server + "/issue-credential-2.0/records", function (response) {
            results = response.results;
            results.forEach(element => {
                row = [
                    element.cred_ex_record.cred_ex_id,
                    element.cred_ex_record.role,
                    element.cred_ex_record.state
                ];
                line = table.row.add(parse_row(row)).node();
                if(element.cred_ex_record.state == "credential-received"){
                    $(line.children[0]).click(function(){
                        $("#store-cred-form").show();
                        $("#store-cred-form").find("[aria-describedby='cred-ex-id']").val(line.children[0].innerHTML);
                    })
                    line.children[0] = addTooltip(line.children[0], "Store credential");
                }
                
            });
            table.draw();
        })
    } catch (e) {
        console.log(e);
    }
}

function get_presentations(server, table){
    try {
        $.get(server + "/present-proof-2.0/records", function (response) {
            results = response.results;
            results.forEach(element => {
                input_descriptor_id = null
                try{
                    input_descriptor_id = element.by_format.pres_request.dif.presentation_definition.input_descriptors[0].id;
                } catch (e) {
                    console.log(e);
                }
                row = [
                    element.pres_ex_id,
                    element.role,
                    input_descriptor_id,
                    element.state,
                ];
                line = table.row.add(parse_row(row)).node();
                if(element.state == "request-received"){
                    $(line.children[0]).click(function(){
                        $("#send-pres-form").show();
                        $("#send-pres-form").find("[aria-describedby='pres-ex-id']").val(line.children[0].innerHTML);
                        get_presentation_credential(server);
                    })
                    line.children[0] = addTooltip(line.children[0], "Send presentation");
                }else if(element.state == "presentation-received"){
                    $(line.children[0]).click(function(){
                        verify_presentation(server, line.children[0].innerHTML);
                    })
                    line.children[0] = addTooltip(line.children[0], "Verify presentation");
                }
            });
            table.draw();
        })
    } catch (e) {
        console.log(e);
    }
}

function get_credentials(server, table){
    try {
        $.post(server + "/credentials/w3c", "{}", function (response) {
            results = response.results;
            results.forEach(element => {
                row = [
                    element.record_id,
                    element.issuer_id,
                    element.subject_ids[0],
                ];
                cred = table.row.add(parse_row(row)).node();
                $(cred).click(function() {
                    window.location.href = "/credential/" + element.record_id
                })
            });
            table.draw();
        })
    } catch (e) {
        console.log(e);
    }
}

function send_credential_request(){
    form = $("#request-cred-form");
    my_did = form.find("[aria-describedby='my-did']").val();
    issuer_did = form.find("[aria-describedby='issuer-did']").val();
    connection_id = form.find("[aria-describedby='connection-id']").val();
    cred_id = form.find("[aria-describedby='cred-id']").val();
    cred_name = form.find("[aria-describedby='cred-name']").val();
    cred_lastname = form.find("[aria-describedby='cred-lastname']").val();
    cred_dregreetype = form.find("[aria-describedby='cred-dregreetype']").val();
    cred_prooftype = form.find("[aria-describedby='cred-prooftype']").val();
    cred_degreename = form.find("[aria-describedby='cred-degreename']").val();
    college = form.find("[aria-describedby='college']").val();
    date = (new Date()).toISOStringNoMilli();
    $.getJSON("static/js/credential.json", function(request) {
        console.log(request); // this will show the info it in firebug console
        console.log(cred_prooftype);
        request.connection_id = connection_id;
        credential = request.filter.ld_proof.credential;
        request.filter.ld_proof.options.proofType = cred_prooftype;
        credential.issuer = issuer_did;
        credential.issuanceDate = date;
        credential.credentialSubject.id = my_did;
        credential.credentialSubject.givenName = cred_name;
        credential.credentialSubject.familyName = cred_lastname;
        credential.credentialSubject.degree.type = cred_dregreetype;
        credential.credentialSubject.degree.degreeType = "Undergraduate";
        credential.credentialSubject.degree.name = cred_degreename;
        credential.credentialSubject.college = college;
        console.log(request);
        try {
            $.ajax({
                url:"http://localhost:8080/issue-credential-2.0/send-request",
                type:"POST",
                data: JSON.stringify(request),
                contentType:"application/json; charset=utf-8",
                dataType:"json",
                function (response) {
                    console.log(response);
                }
            })
        } catch (e) {
            console.log(e);
        }
    });
}

function send_presentation_request(){
    form = $("#request-pres-form");
    connection_id = form.find("[aria-describedby='connection-id']").val();
    pres_id = form.find("[aria-describedby='pres-id']").val();
    pres_name = form.find("[aria-describedby='pres-name']").val();
    pres_prooftype = form.find("[aria-describedby='pres-prooftype']").val();
    $.getJSON("static/js/presentation.json", function(request) {
        console.log(request); // this will show the info it in firebug console
        request.connection_id = connection_id;
        format = request.presentation_request.dif.presentation_definition.format;
        format.ldp_vp.proof_type.push(pres_prooftype);
        input_descriptor = request.presentation_request.dif.presentation_definition.input_descriptors[0];
        input_descriptor.id = pres_id;
        input_descriptor.name = pres_name;
        console.log(request);
        try {
            $.ajax({
                url:"http://localhost:8081/present-proof-2.0/send-request",
                type:"POST",
                data: JSON.stringify(request),
                contentType:"application/json; charset=utf-8",
                dataType:"json",
                function (response) {
                    console.log(response);
                }
            })
        } catch (e) {
            console.log(e);
        }
    });
}

function store_credential_request(){
    form = $("#store-cred-form");
    cred_ex_id = form.find("[aria-describedby='cred-ex-id']").val();
    cred_id = form.find("[aria-describedby='cred-id']").val();
    request = {"credential_id": cred_id}
    try {
        $.ajax({
            url:"http://localhost:8080/issue-credential-2.0/records/" + cred_ex_id + "/store",
            type:"POST",
            crossDomain: true,
            data: JSON.stringify(request),
            contentType:"application/json; charset=utf-8",
            accept: "application/json",
            dataType:"json",
            function (response) {
                console.log(response);
            }
        })
    } catch (e) {
        console.log(e);
    }
}

function send_presentation_response(){
    form = $("#send-pres-form")
    pres_ex_id = form.find("[aria-describedby='pres-ex-id']").val();
    pres_cred_id = form.find("[aria-describedby='pres-cred-id']").val();
    request = {
        "dif": { 
            "record_ids": { "university_degree_1": [pres_cred_id] } 
        }
    }
    try {
        $.ajax({
            url:"http://localhost:8080/present-proof-2.0/records/" + pres_ex_id + "/send-presentation",
            type:"POST",
            crossDomain: true,
            data: JSON.stringify(request),
            contentType:"application/json; charset=utf-8",
            accept: "application/json",
            dataType:"json",
            function (response) {
                console.log(response);
            }
        })
    } catch (e) {
        console.log(e);
    }
}

function get_presentation_credential(server){
    form = $("#send-pres-form")
    pres_ex_id = form.find("[aria-describedby='pres-ex-id']").val();
    try {
        $.get(server + "/present-proof-2.0/records/" + pres_ex_id + "/credentials", function (response) {
            response.forEach(element => {
                form.find("[aria-describedby='pres-cred-id']").append(create_option(element.record_id, element.record_id));
            });
        })
    } catch (e) {
        console.log(e);
    }
}

function verify_presentation(server, pres_ex_id){
    try {
        $.post(server + "/present-proof-2.0/records/" + pres_ex_id + "/verify-presentation", "{}", function (response) {
            console.log(response);
            window.location.reload();
        })
    } catch (e) {
        console.log(e);
    }
}