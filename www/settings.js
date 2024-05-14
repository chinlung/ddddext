
// action bar
const run_button = document.querySelector('#run_btn');
const save_button = document.querySelector('#save_btn');
const reset_button = document.querySelector('#reset_btn');
const exit_button = document.querySelector('#exit_btn');

const new_captcha_button = document.querySelector('#new_captcha_btn');
const new_autofill_button = document.querySelector('#new_autofill_btn');
const new_autocheck_button = document.querySelector('#new_autocheck_btn');

// preference
const homepage = document.querySelector('#homepage');

// advance
const window_size = document.querySelector('#window_size');
const checkall_keyword = document.querySelector('#checkall_keyword');


const ocr_captcha_use_public_server = document.querySelector('#ocr_captcha_use_public_server');
const remote_url = document.querySelector('#remote_url');
const PUBLIC_SERVER_URL = "http://maxbot.dropboxlike.com:16888/";

var settings = null;

maxbot_load_api();

function load_settins_to_form(settings)
{
    if (settings)
    {
        homepage.value = settings.homepage;
        window_size.value  = settings.advanced.window_size;

        let remote_url_string = "";
        let remote_url_array = [];
        if(settings.advanced.remote_url.length > 0) {
            remote_url_array = JSON.parse('[' +  settings.advanced.remote_url +']');
        }
        if(remote_url_array.length) {
            remote_url_string = remote_url_array[0];
        }
        remote_url.value = remote_url_string;

        checkall_keyword.value = settings.advanced.checkall_keyword;
        if(checkall_keyword.value=='""') {
            checkall_keyword.value='';
        }

        if(settings.ocr_captcha.captcha.length) {
            settings.ocr_captcha.captcha.forEach((d)=> {
                captcha_new_with_value(d);
            });
        }

        if(settings.autofill.length) {
            settings.autofill.forEach((d)=> {
                autofill_new_with_value(d);
            });
        }

        if(settings.autocheck.length) {
            settings.autocheck.forEach((d)=> {
                autocheck_new_with_value(d);
            });
        }

        initai_captcha();
        initai_autofill();
        initai_autocheck();
    } else {
        console.log('no settings found');
    }
}

function maxbot_load_api()
{
    let api_url = "http://127.0.0.1:16888/load";
    $.get( api_url, function() {
        //alert( "success" );
    })
    .done(function(data) {
        //alert( "second success" );
        //console.log(data);
        settings = data;
        load_settins_to_form(data);
    })
    .fail(function() {
        //alert( "error" );
    })
    .always(function() {
        //alert( "finished" );
    });
}

function maxbot_reset_api()
{
    captcha_reset();
    autofill_reset();
    autocheck_reset();

    let api_url = "http://127.0.0.1:16888/reset";
    $.get( api_url, function() {
        //alert( "success" );
    })
    .done(function(data) {
        //alert( "second success" );
        //console.log(data);
        settings = data;
        load_settins_to_form(data);
        check_unsaved_fields();
    })
    .fail(function() {
        //alert( "error" );
    })
    .always(function() {
        //alert( "finished" );
    });
}

function checkUsePublicServer()
{
    remote_url.value = PUBLIC_SERVER_URL;
}

let messageClearTimer;

function message(msg)
{
    $("#message_detail").html("存檔完成");
    $("#message_modal").modal("show");
}

function message_old(msg)
{
    clearTimeout(messageClearTimer);
    const message = document.querySelector('#message');
    message.innerText = msg;
    messageClearTimer = setTimeout(function ()
        {
            message.innerText = '';
        }, 3000);
}

function maxbot_launch()
{
    save_changes_to_dict(true);
    maxbot_save_api(maxbot_run_api());
}

function maxbot_run_api()
{
    let api_url = "http://127.0.0.1:16888/run";
    $.get( api_url, function() {
        //alert( "success" );
    })
    .done(function(data) {
        //alert( "second success" );
    })
    .fail(function() {
        //alert( "error" );
    })
    .always(function() {
        //alert( "finished" );
    });
}

function maxbot_shutdown_api()
{
    let api_url = "http://127.0.0.1:16888/shutdown";
    $.get( api_url, function() {
        //alert( "success" );
    })
    .done(function(data) {
        //alert( "second success" );
        window.close();
    })
    .fail(function() {
        //alert( "error" );
    })
    .always(function() {
        //alert( "finished" );
    });
}

function get_autofill_array()
{
    let autofill = [];
    let last_node = $("#autofill-container tr[data-index]").last().attr("data-index");
    let node=0;
    if(last_node) {
        node=parseInt(last_node);
    }
    if(node>0){
        for(let i=1; i<=node; i++) {
            let item={};
            item["enable"]=true;
            item["url"]=$("#autofill_url_" + i).val();
            item["selector"]=$("#autofill_selector_" + i).val();
            item["value"]=$("#autofill_value_" + i).val();
            autofill.push(item);
        }
    }
    return autofill;
}

function get_autocheck_array()
{
    let autocheck = [];
    let last_node = $("#autocheck-container tr[data-index]").last().attr("data-index");
    let node=0;
    if(last_node) {
        node=parseInt(last_node);
    }
    if(node>0){
        for(let i=1; i<=node; i++) {
            let item={};
            item["enable"]=true;
            item["url"]=$("#autocheck_url_" + i).val();
            item["selector"]=$("#autocheck_selector_" + i).val();
            item["value"]=$("#autocheck_value_" + i).prop("checked");
            autocheck.push(item);
        }
    }
    return autocheck;
}

function get_captcha_array()
{
    let captcha = [];
    let last_node = $("#captcha-container tr[data-index]").last().attr("data-index");
    let node=0;
    if(last_node) {
        node=parseInt(last_node);
    }
    if(node>0){
        for(let i=1; i<=node; i++) {
            let item={};
            item["enable"]=true;
            item["url"]=$("#captcha_url_" + i).val();
            item["captcha"]=$("#captcha_selector_" + i).val();
            item["input"]=$("#input_selector_" + i).val();
            item["maxlength"]=$("#maxlength_" + i).val();
            captcha.push(item);
        }
    }
    return captcha;
}

function save_changes_to_dict(silent_flag)
{
    if(settings) {

        // preference
        settings.homepage = homepage.value;
        // advanced
        settings.advanced.window_size = window_size.value;

        let remote_url_array = [];
        remote_url_array.push(remote_url.value);
        let remote_url_string = JSON.stringify(remote_url_array);
        remote_url_string = remote_url_string.substring(0,remote_url_string.length-1);
        remote_url_string = remote_url_string.substring(1);
        //console.log("final remote_url_string:"+remote_url_string);

        settings.advanced.remote_url = remote_url_string;

        let checkall_keyword_string = checkall_keyword.value;
        if(checkall_keyword_string.indexOf('"')==-1) {
            checkall_keyword_string = '"' + checkall_keyword_string + '"';
        }
        settings.advanced.checkall_keyword = checkall_keyword_string;

        settings.ocr_captcha.captcha = get_captcha_array();
        settings.autofill = get_autofill_array();
        settings.autocheck = get_autocheck_array();

    }
    if(!silent_flag) {
        message('已存檔');
    }
}

function maxbot_save_api(callback)
{
    let api_url = "http://127.0.0.1:16888/save";
    if(settings) {
        $.post( api_url, JSON.stringify(settings), function() {
            //alert( "success" );
        })
        .done(function(data) {
            //alert( "second success" );
            check_unsaved_fields();
            if(callback) callback;
        })
        .fail(function() {
            //alert( "error" );
        })
        .always(function() {
            //alert( "finished" );
        });
    }
}

function maxbot_save()
{
    save_changes_to_dict(false);
    maxbot_save_api();
}

function check_unsaved_fields()
{
    if(settings) {
        const field_list_basic = ["homepage"];
        field_list_basic.forEach(f => {
            const field = document.querySelector('#'+f);
            if(field.value != settings[f]) {
                $("#"+f).addClass("is-invalid");
            } else {
                $("#"+f).removeClass("is-invalid");
            }
        });
        const field_list_advance = [
            "remote_url",
            "window_size"
        ];
        field_list_advance.forEach(f => {
            const field = document.querySelector('#'+f);
            let formated_input = field.value;
            let formated_saved_value = settings["advanced"][f];
            //console.log(f);
            //console.log(field.value);
            //console.log(formated_saved_value);
            if(typeof formated_saved_value == "string") {
                if(formated_input=='')
                    formated_input='""';
                if(formated_saved_value=='')
                    formated_saved_value='""';
                if(formated_saved_value.indexOf('"') > -1) {
                    if(formated_input.length) {
                        if(formated_input != '""') {
                            formated_input = '"' + formated_input + '"';
                        }
                    }
                }
            }
            let is_not_match = (formated_input != formated_saved_value);
            if(is_not_match) {
                //console.log(f);
                //console.log(formated_input);
                //console.log(formated_saved_value);
                $("#"+f).addClass("is-invalid");
            } else {
                $("#"+f).removeClass("is-invalid");
            }
        });
    }
}

run_button.addEventListener('click', maxbot_launch);
save_button.addEventListener('click', maxbot_save);
reset_button.addEventListener('click', maxbot_reset_api);
exit_button.addEventListener('click', maxbot_shutdown_api);

new_captcha_button.addEventListener('click', captcha_new);
new_autofill_button.addEventListener('click', autofill_new);
new_autocheck_button.addEventListener('click', autocheck_new);

ocr_captcha_use_public_server.addEventListener('change', checkUsePublicServer);

const onchange_tag_list = ["input","select","textarea"];
onchange_tag_list.forEach((tag) => {
    const input_items = document.querySelectorAll(tag);
    input_items.forEach((userItem) => {
        userItem.addEventListener('change', check_unsaved_fields);
    });
});

homepage.addEventListener('keyup', check_unsaved_fields);

function captcha_reset()
{
    let last_node = $("#captcha-container tr[data-index]").remove();
}

function captcha_new()
{
    captcha_new_with_value();
}

function captcha_new_with_value(item)
{
    let last_node = $("#captcha-container tr[data-index]").last().attr("data-index");
    let node=1;
    if(last_node) {
        node=parseInt(last_node)+1;
    }
    let html = $("#captcha-template").html();
    if(html) {
        html=html.replace(/@node@/g,""+node);
        //console.log(html);
        $("#captcha-container").append(html);
        $("#captcha-actionbar").insertAfter($("#captcha-container tr").last());

        if(item) {
            $("#captcha_url_"+node).val(item["url"]);
            $("#captcha_selector_"+node).val(item["captcha"]);
            $("#input_selector_"+node).val(item["input"]);
            $("#maxlength_"+node).val(item["maxlength"]);
        }
    }
}

function captcha_remove(node)
{
    $("#captcha-container tr[data-index='"+ node +"']").remove();
}

function initai_captcha()
{
    let last_node = $("#captcha-container tr[data-index]").last().attr("data-index");
    if(!last_node) {
        captcha_new();
    }
}

function autofill_reset()
{
    let last_node = $("#autofill-container tr[data-index]").remove();
}

function autofill_new()
{
    autofill_new_with_value();
}

function autofill_new_with_value(item)
{
    let last_node = $("#autofill-container tr[data-index]").last().attr("data-index");
    let node=1;
    if(last_node) {
        node=parseInt(last_node)+1;
    }
    let html = $("#autofill-template").html();
    html=html.replace(/@node@/g,""+node);
    //console.log(html);
    $("#autofill-container").append(html);
    $("#autofill-actionbar").insertAfter($("#autofill-container tr").last());

    if(item) {
        $("#autofill_url_"+node).val(item["url"]);
        $("#autofill_selector_"+node).val(item["selector"]);
        $("#autofill_value_"+node).val(item["value"]);
    }
}

function autofill_remove(node)
{
    $("#autofill-container tr[data-index='"+ node +"']").remove();
}

function initai_autofill()
{
    let last_node = $("#autofill-container tr[data-index]").last().attr("data-index");
    if(!last_node) {
        autofill_new();
    }
}

function autocheck_reset()
{
    let last_node = $("#autocheck-container tr[data-index]").remove();
}

function autocheck_new()
{
    autocheck_new_with_value();
}

function autocheck_new_with_value(item)
{
    let last_node = $("#autocheck-container tr[data-index]").last().attr("data-index");
    let node=1;
    if(last_node) {
        node=parseInt(last_node)+1;
    }
    let html = $("#autocheck-template").html();
    html=html.replace(/@node@/g,""+node);
    //console.log(html);
    $("#autocheck-container").append(html);
    $("#autocheck-actionbar").insertAfter($("#autocheck-container tr").last());

    if(item) {
        $("#autocheck_url_"+node).val(item["url"]);
        $("#autocheck_selector_"+node).val(item["selector"]);
        $("#autocheck_value_"+node).prop("checked", item["value"]);
    }
}

function autocheck_remove(node)
{
    $("#autocheck-container tr[data-index='"+ node +"']").remove();
}

function initai_autocheck()
{
    let last_node = $("#autocheck-container tr[data-index]").last().attr("data-index");
    if(!last_node) {
        autocheck_new();
    }
}
