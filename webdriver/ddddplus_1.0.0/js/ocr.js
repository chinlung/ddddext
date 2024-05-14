const storage = chrome.storage.local;
var settings = null;
var inputInterval = null;
var ocrInterval = null;
var target_captcha_length = 4;
var target_captcha_selector = "";
var target_input_selector = "";

function get_ocr_image()
{
    //console.log("get_ocr_image");
    let image_data = "";
    let img = document.querySelector(target_captcha_selector);
    if(img!=null) {
        let canvas = document.createElement('canvas');
        let context = canvas.getContext('2d');
        canvas.height = img.naturalHeight;
        canvas.width = img.naturalWidth;
        context.drawImage(img, 0, 0);
        let img_data = canvas.toDataURL();
        if(img_data) {
            image_data = img_data.split(",")[1];
            //console.log(image_data);
        }
    }
    return image_data;
}

var last_captcha_answer="";
chrome.runtime.onMessage.addListener((message) => {
    //console.log('sent from background', message);
    if(message.answer.length==target_captcha_length) {
        set_ocr_answer(message.answer);
        last_captcha_answer=message.answer;
    } else {
        // renew captcha.
        if(last_captcha_answer!=message.answer) {
            last_captcha_answer=message.answer;
            console.log("renew captcha");
            $(target_captcha_selector).click();
        }
    }
});

function set_ocr_answer(answer)
{
    //console.log("answer:"+answer);
    if(answer.length > 0) {
        $(target_input_selector).val(answer);
    }
}

async function get_ocr_answer(api_url, image_data)
{
    let bundle = {
      action: 'ocr',
      data: {
        'url': api_url + 'ocr',
        'image_data':image_data,
      }
    };

    const return_answer = await chrome.runtime.sendMessage(bundle);
    //console.log(return_answer);
}

function orc_image_ready(api_url)
{
    let ret=false;
    let image_data = get_ocr_image();
    if(image_data.length>0) {
        ret=true;
        if(ocrInterval) clearInterval(ocrInterval);
        get_ocr_answer(api_url, image_data);
    }
    //console.log("orc_image_ready:"+ret);
    return ret;
}

function get_remote_url(settings)
{
    let remote_url_string = "";
    if(settings) {
        let remote_url_array = [];
        if(settings.advanced.remote_url.length > 0) {
            remote_url_array = JSON.parse('[' +  settings.advanced.remote_url +']');
        }
        if(remote_url_array.length) {
            remote_url_string = remote_url_array[0];
        }
    }
    return remote_url_string;
}

function ocr_main(settings) {
    //console.log("ocr main");
    if(settings) {
        let remote_url_string = get_remote_url(settings);

        if(settings.ocr_captcha.captcha.length) {
            settings.ocr_captcha.captcha.forEach((d)=> {
                //console.log(d);
                let is_match_url = false;
                if(d.enable) {
                    if(d.url=="") {
                        is_match_url = true;
                    } else {
                        if(document.location.href.indexOf(d.url) > -1) {
                            is_match_url = true;
                        }
                    }
                }
                //console.log(is_match_url);
                if(is_match_url && d.captcha.length  && d.input.length) {
                    if(d.maxlength.length > 0) {
                        target_captcha_length = parseInt(d.maxlength);
                    }

                    target_captcha_selector = d.captcha;
                    target_input_selector = d.input;
                    const current_inputed_value = $(target_input_selector).val();
                    if(current_inputed_value == "") {
                        if(!orc_image_ready(remote_url_string)) {
                            ocrInterval = setInterval(() => {
                                orc_image_ready(remote_url_string);
                            }, 100);
                        }
                    }
                }
            });
        }

        if(settings.autofill.length) {
            settings.autofill.forEach((d)=> {
                //console.log(d);
                let is_match_url = false;
                if(d.enable) {
                    if(d.url=="") {
                        is_match_url = true;
                    } else {
                        if(document.location.href.indexOf(d.url) > -1) {
                            is_match_url = true;
                        }
                    }
                }
                //console.log(is_match_url);
                if(is_match_url && d.selector.length  && d.value.length) {
                    $(d.selector).val(d.value);
                }
            });
        }

        if(settings.autocheck.length) {
            settings.autocheck.forEach((d)=> {
                //console.log(d);
                let is_match_url = false;
                if(d.enable) {
                    if(d.url=="") {
                        is_match_url = true;
                    } else {
                        if(document.location.href.indexOf(d.url) > -1) {
                            is_match_url = true;
                        }
                    }
                }
                //console.log(is_match_url);
                if(is_match_url && d.selector.length) {
                    $(d.selector).prop("checked", d.value);
                }
            });
        }
    }
}

function checkall()
{
    $('input[type=checkbox]:not(:checked)').each(function() {
        $(this).click();
    });
}

function checkall_main(settings)
{
    if(settings) {
        //console.log(settings.advanced.checkall_keyword);
        let checkall_keyword_array = [];
        if(settings) {
            if(settings.advanced.checkall_keyword.length > 0) {
                if(settings.advanced.checkall_keyword!='""') {
                    checkall_keyword_array = JSON.parse('[' + settings.advanced.checkall_keyword +']');
                }
            }
        }
        //console.log(checkall_keyword_array);
        for (let i = 0; i < checkall_keyword_array.length; i++) {
            let is_match_url = false;
            if(document.location.href.indexOf(checkall_keyword_array[i]) > -1) {
                is_match_url = true;
            }
            //console.log(is_match_url);
            if(is_match_url) {
                checkall();
            }
        }
    }
}

storage.get('settings', function (items)
{
    if (items.settings)
    {
        settings = items.settings;
    }
});

storage.get('status', function (items)
{
    if (items.status && items.status=='ON')
    {
        inputInterval= setInterval(() => {
            ocr_main(settings);
            checkall_main(settings);
        }, 200);
    } else {
        //console.log('maxbot status is not ON');
    }
});
