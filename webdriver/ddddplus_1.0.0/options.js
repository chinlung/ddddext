const storage = chrome.storage.local;

const save_button = document.querySelector('#save_btn');

const ocr_captcha_use_public_server = document.querySelector('#ocr_captcha_use_public_server');
const remote_url = document.querySelector('#remote_url');

const PUBLIC_SERVER_URL = "http://maxbot.dropboxlike.com:16888/";

var settings = null;

loadChanges();

save_button.addEventListener('click', saveChanges);
ocr_captcha_use_public_server.addEventListener('change', checkUsePublicServer);

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

async function saveChanges()
{
    const silent_flag = false;

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

        settings.ocr_captcha.captcha = get_captcha_array();
        settings.autofill = get_autofill_array();

    }
    if(!silent_flag) {
        message('已存檔');
    }

}

function loadChanges()
{
    storage.get('settings', function (items)
    {
        //console.log(items);
        if (items.settings)
        {
            settings = items.settings;

            let remote_url_string = "";
            let remote_url_array = [];
            if(settings.advanced.remote_url.length > 0) {
                remote_url_array = JSON.parse('[' +  settings.advanced.remote_url +']');
            }
            if(remote_url_array.length) {
                remote_url_string = remote_url_array[0];
            }
            remote_url.value = remote_url_string;

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

            initai_captcha();
            initai_autofill();
        } else {
            console.log('no settings found');
        }

    }
    );
}

async function checkUsePublicServer()
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
