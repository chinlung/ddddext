#!/usr/bin/env python3
#encoding=utf-8
import argparse
import base64
import json
import logging
import os
import pathlib
import platform
import random
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
import warnings
import webbrowser
from datetime import datetime

import nodriver as uc
from nodriver import cdp
from nodriver.core.config import Config
from urllib3.exceptions import InsecureRequestWarning

import util

try:
    import ddddocr
except Exception as exc:
    print(exc)
    pass

CONST_APP_VERSION = "DDDDEXT (2024.04.24)"

CONST_MAXBOT_ANSWER_ONLINE_FILE = "MAXBOT_ONLINE_ANSWER.txt"
CONST_MAXBOT_CONFIG_FILE = "settings.json"
CONST_DDDDEXT_EXTENSION_NAME = "ddddplus_1.0.0"

warnings.simplefilter('ignore',InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig()
logger = logging.getLogger('logger')

def get_config_dict(args):
    app_root = util.get_app_root()
    config_filepath = os.path.join(app_root, CONST_MAXBOT_CONFIG_FILE)

    # allow assign config by command line.
    if args.input and len(args.input) > 0:
        config_filepath = args.input

    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath) as json_data:
            config_dict = json.load(json_data)

            # Define a dictionary to map argument names to their paths in the config_dict
            arg_to_path = {
                "homepage": ["homepage"],
                "proxy_server": ["advanced", "proxy_server_port"],
                "window_size": ["advanced", "window_size"]
            }

            # Update the config_dict based on the arguments
            for arg, path in arg_to_path.items():
                value = getattr(args, arg)
                if value and len(str(value)) > 0:
                    d = config_dict
                    for key in path[:-1]:
                        d = d[key]
                    d[path[-1]] = value

    return config_dict

async def nodriver_goto_homepage(driver, config_dict):
    homepage = config_dict["homepage"]
    tab=None
    try:
        tab = await driver.get(homepage)
        await tab.get_content()
        await tab.sleep()
        # try to avoid error: cannot unpack non-iterable NoneType object, but it still happen.
        time.sleep(2)

        # workaround for not able resize.
        url, is_quit_bot, reset_act_tab = await nodriver_current_url(driver, tab)
        if len(driver.tabs) ==2 and url=="chrome://new-tab-page/":
            print("建議再按一次「搶票」，目前視窗有異常, 程式應該有出錯...")

            #driver.stop()

            for i, tab in enumerate(driver):
                if i == 0:
                    print("close tab:", i)
                    await tab.close()
                if i == 1:
                    print("activate tab:", i)
                    await tab.activate()

            print("goto:", homepage)
            tab = await driver.get(homepage)

        # workaround for hidden chrome-extension tab.
        if len(driver.tabs) ==2:
            if url.startswith("chrome-extension://") and url.endswith("/audio.html"):
                print("close wrong tab...")
                for i, tab in enumerate(driver):
                    if i > 0:
                        print("close tab:", i)
                        await tab.close()

    except Exception as e:
        print(e)
        pass

    # access cookie
    #print(config_dict)
    if len(config_dict["cookie"]) > 0:
        try:
            cookies  = await driver.cookies.get_all()
            for each_cookie in config_dict["cookie"]:
                new_cookie = cdp.network.CookieParam(each_cookie["key"], each_cookie["value"], domain=each_cookie["domain"], path="/", http_only=True, secure=True)
                cookies.append(new_cookie)
            await driver.cookies.set_all(cookies)
        except Exception as e:
            print(e)
            pass

        try:
            for each_tab in driver.tabs:
                await each_tab.reload()
        except Exception as exc:
            print(exc)
            pass


    return tab


def get_nodriver_browser_args():
    browser_args = [
        "--disable-animations",
        "--disable-app-info-dialog-mac",
        "--disable-background-networking",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-dev-shm-usage",
        "--disable-device-discovery-notifications",
        "--disable-dinosaur-easter-egg",
        "--disable-domain-reliability",
        "--disable-features=IsolateOrigins,site-per-process,TranslateUI",
        "--disable-infobars",
        "--disable-logging",
        "--disable-login-animations",
        "--disable-login-screen-apps",
        "--disable-notifications",
        "--disable-password-generation",
        "--disable-popup-blocking",
        "--disable-renderer-backgrounding",
        "--disable-session-crashed-bubble",
        "--disable-smooth-scrolling",
        "--disable-suggestions-ui",
        "--disable-sync",
        "--disable-translate",
        "--hide-crash-restore-bubble",
        "--homepage=about:blank",
        "--no-default-browser-check",
        "--no-first-run",
        "--no-pings",
        "--no-service-autorun",
        "--password-store=basic",
        "--remote-debugging-host=127.0.0.1",
        "--lang=zh-TW",
        #"--disable-remote-fonts",
    ]

    return browser_args

def get_maxbot_extension_path(extension_folder):
    app_root = util.get_app_root()
    extension_path = "webdriver"
    extension_path = os.path.join(extension_path, extension_folder)
    config_filepath = os.path.join(app_root, extension_path)
    #print("config_filepath:", config_filepath)

    # double check extesion mainfest
    path = pathlib.Path(config_filepath)
    if path.exists():
        if path.is_dir():
            #print("found extension dir")
            for item in path.rglob("manifest.*"):
                path = item.parent
            #print("final path:", path)
    return config_filepath

def push_injectjs_to_extension(config_dict, extension_path):
    manifest_filepath = os.path.join(extension_path, "manifest.json")
    js_folder = os.path.join(extension_path, "js")
    #print("manifest_filepath:", manifest_filepath)
    manifest_dict = None
    try:
        with open(manifest_filepath) as json_data:
            manifest_dict = json.load(json_data)
            #print(manifest_dict)
    except Exception as e:
        print("error on open file")
        print(e)
        pass

    if not manifest_dict is None:
        clean_scripts_dict_array = []
        for each_content_scripts in manifest_dict["content_scripts"]:
            is_clean = True
            for each_js in each_content_scripts["js"]:
                if each_js.startswith("js/tmp_"):
                    is_clean = False
                    break
            if is_clean:
                clean_scripts_dict_array.append(each_content_scripts)
        #print(clean_scripts_dict_array)

        if "injectjs" in config_dict:
            if len(config_dict["injectjs"]) > 0:
                js_index = 0
                for each_injectjs in config_dict["injectjs"]:
                    js_index += 1
                    js_filename = "tmp_" + str(js_index) + ".js"
                    script_url = each_injectjs["url"]
                    script_text = each_injectjs["script"]
                    if each_injectjs["enable"] and len(script_url) > 0 and len(script_text) > 0:
                        content_scripts_dict = {}
                        content_scripts_dict["matches"] = [script_url]
                        content_scripts_dict["run_at"] = each_injectjs["run_at"]
                        content_scripts_dict["world"] = each_injectjs["world"]
                        content_scripts_dict["js"] = ["jquery.min.js","js/common.js", "js/" + js_filename]

                        js_filepath = os.path.join(js_folder, js_filename)
                        #print("js_filepath:", js_filepath)
                        try:
                            with open(js_filepath, "w") as text_file:
                                text_file.write(script_text)
                        except Exception as e:
                            print(e)
                            pass
                        clean_scripts_dict_array.append(content_scripts_dict)

        manifest_dict["content_scripts"] = clean_scripts_dict_array


        util.save_json(manifest_dict, manifest_filepath)


def get_extension_config(config_dict):
    default_lang = "zh-TW"
    no_sandbox=True
    browser_args = get_nodriver_browser_args()
    if len(config_dict["advanced"]["proxy_server_port"]) > 2:
        browser_args.append('--proxy-server=%s' % config_dict["advanced"]["proxy_server_port"])
    conf = Config(browser_args=browser_args, lang=default_lang, no_sandbox=no_sandbox)
    if config_dict["advanced"]["chrome_extension"]:
        ext = get_maxbot_extension_path(CONST_DDDDEXT_EXTENSION_NAME)
        if len(ext) > 0:
            push_injectjs_to_extension(config_dict, ext)
            clone_ext = ext.replace(CONST_DDDDEXT_EXTENSION_NAME, "tmp_" + CONST_DDDDEXT_EXTENSION_NAME + "_" + config_dict["token"])
            if not os.path.exists(clone_ext):
                os.mkdir(clone_ext)
            util.copytree(ext, clone_ext)
            conf.add_extension(clone_ext)
            util.dump_settings_to_maxbot_plus_extension(clone_ext, config_dict, CONST_MAXBOT_CONFIG_FILE)
    return conf

async def nodriver_resize_window(driver, config_dict):
    window_size = config_dict["advanced"]["window_size"]
    if len(window_size) > 0:
        #print("window_size", window_size)
        if "," in window_size:
            launch_counter = 1
            target_left = 0
            target_top = 30
            target_width = 480
            target_height = 1024
            size_array = window_size.split(",")
            if len(size_array) >= 2:
                target_width = int(size_array[0])
                target_height = int(size_array[1])
            if len(size_array) >= 3:
                if len(size_array[2]) > 0:
                    launch_counter = int(size_array[2])
                target_left = target_width * launch_counter
                if target_left >= 1440:
                    target_left = 0
            #tab = await driver.main_tab()
            try:
                for i, tab in enumerate(driver):
                    #print(i, launch_counter, target_left, target_width, target_height)
                    if i==0:
                        await tab.activate()
                    await tab.set_window_size(left=target_left, top=target_top, width=target_width, height=target_height)
                    await tab.sleep()
            except Exception as exc:
                # cannot unpack non-iterable NoneType object
                print(exc)
                print("請關閉所有視窗後，重新操作一次")
                pass

# we only handle last tab.
async def nodriver_current_url(driver, tab):
    is_quit_bot = False
    exit_bot_error_strings = [
        "server rejected WebSocket connection: HTTP 500",
        "[Errno 61] Connect call failed ('127.0.0.1',",
        "[WinError 1225] ",
    ]

    url = ""
    tab_count = len(driver.tabs)
    #print("tab_count:", tab_count)

    # PS: manually close tab will cause nodriver no response.
    if tab_count > 1:
        tab = driver.tabs[tab_count-1]

    reset_active_tab = None
    if not tab in driver.tabs:
        print("tab closed by user before.")
        tab = driver.tabs[tab_count-1]
        reset_active_tab = tab

    if tab:
        url_dict = {}
        try:
            url_dict = await tab.js_dumps('window.location.href')
        except Exception as exc:
            print(exc)
            str_exc = ""
            try:
                str_exc = str(exc)
            except Exception as exc2:
                pass
            if len(str_exc) > 0:
                for each_error_string in exit_bot_error_strings:
                    if each_error_string in str_exc:
                        #print('quit bot by error:', each_error_string, driver)
                        is_quit_bot = True

        url_array = []
        if url_dict:
            for k in url_dict:
                if k.isnumeric():
                    if "0" in url_dict[k]:
                        url_array.append(url_dict[k]["0"])
            url = ''.join(url_array)
    return url, is_quit_bot, reset_active_tab

def nodriver_overwrite_prefs(conf):
    #print(conf.user_data_dir)
    prefs_filepath = os.path.join(conf.user_data_dir,"Default")
    if not os.path.exists(prefs_filepath):
        os.mkdir(prefs_filepath)
    prefs_filepath = os.path.join(prefs_filepath,"Preferences")

    prefs_dict = {
        "credentials_enable_service": False,
        "ack_existing_ntp_extensions": False,
        "translate":{"enabled": False}}
    prefs_dict["in_product_help"]={}
    prefs_dict["in_product_help"]["snoozed_feature"]={}
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"]={}
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"]["is_dismissed"]=True
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"]["last_dismissed_by"]=4
    prefs_dict["media_router"]={}
    prefs_dict["media_router"]["show_cast_sessions_started_by_other_devices"]={}
    prefs_dict["media_router"]["show_cast_sessions_started_by_other_devices"]["enabled"]=False
    prefs_dict["net"]={}
    prefs_dict["net"]["network_prediction_options"]=3
    prefs_dict["privacy_guide"]={}
    prefs_dict["privacy_guide"]["viewed"]=True
    prefs_dict["privacy_sandbox"]={}
    prefs_dict["privacy_sandbox"]["first_party_sets_enabled"]=False
    prefs_dict["profile"]={}
    #prefs_dict["profile"]["cookie_controls_mode"]=1
    prefs_dict["profile"]["default_content_setting_values"]={}
    prefs_dict["profile"]["default_content_setting_values"]["notifications"]=2
    prefs_dict["profile"]["default_content_setting_values"]["sound"]=2
    prefs_dict["profile"]["name"]=CONST_APP_VERSION
    prefs_dict["profile"]["password_manager_enabled"]=False
    prefs_dict["safebrowsing"]={}
    prefs_dict["safebrowsing"]["enabled"]=False
    prefs_dict["safebrowsing"]["enhanced"]=False
    prefs_dict["sync"]={}
    prefs_dict["sync"]["autofill_wallet_import_enabled_migrated"]=False

    json_str = json.dumps(prefs_dict)
    with open(prefs_filepath, 'w') as outfile:
        outfile.write(json_str)

    state_filepath = os.path.join(conf.user_data_dir,"Local State")
    state_dict = {}
    state_dict["performance_tuning"]={}
    state_dict["performance_tuning"]["high_efficiency_mode"]={}
    state_dict["performance_tuning"]["high_efficiency_mode"]["state"]=1
    state_dict["browser"]={}
    state_dict["browser"]["enabled_labs_experiments"]=[
        "history-journeys@4",
        "memory-saver-multi-state-mode@1",
        "modal-memory-saver@1",
        "read-anything@2"
    ]
    state_dict["dns_over_https"]={}
    state_dict["dns_over_https"]["mode"]="off"
    json_str = json.dumps(state_dict)
    with open(state_filepath, 'w') as outfile:
        outfile.write(json_str)

async def check_refresh_datetime_occur(driver, target_time):
    is_refresh_datetime_sent = False

    system_clock_data = datetime.now()
    current_time = system_clock_data.strftime('%H:%M:%S')
    if target_time == current_time:
        try:
            for tab in driver.tabs:
                await tab.reload()
                is_refresh_datetime_sent = True
                print("send refresh at time:", current_time)
        except Exception as exc:
            print(exc)
            pass

    return is_refresh_datetime_sent

async def sendkey_to_browser(driver, config_dict, url):
    tmp_filepath = ""
    if "token" in config_dict:
        #print("url:", url)
        #print("token:", config_dict["token"])
        app_root = util.get_app_root()
        tmp_file = config_dict["token"] + "_sendkey.tmp"
        tmp_filepath = os.path.join(app_root, tmp_file)

    if os.path.exists(tmp_filepath):
        sendkey_dict = None
        try:
            with open(tmp_filepath) as json_data:
                sendkey_dict = json.load(json_data)
                #print("url:", url)
                #print(sendkey_dict)
        except Exception as e:
            print("error on open file")
            print(e)
            pass

        if sendkey_dict:
            #print("nodriver start to sendkey")
            for each_tab in driver.tabs:
                all_command_done = await sendkey_to_browser_exist(each_tab, sendkey_dict, url)

                # must all command success to delete tmp file.
                if all_command_done:
                    try:
                        os.unlink(tmp_filepath)
                        #print("remove file:", tmp_filepath)
                    except Exception as e:
                        pass

async def sendkey_to_browser_exist(tab, sendkey_dict, url):
    all_command_done = True
    if "command" in sendkey_dict:
        for cmd_dict in sendkey_dict["command"]:
            #print("cmd_dict", cmd_dict)
            matched_location = True
            if "location" in cmd_dict:
                if cmd_dict["location"] != url:
                    matched_location = False

            if matched_location:
                if cmd_dict["type"] == "sendkey":
                    print("sendkey")
                    target_text = cmd_dict["text"]
                    try:
                        element = await tab.query_selector(cmd_dict["selector"])
                        if element:
                            await element.click()
                            await element.apply('function (element) {element.value = ""; } ')
                            await element.send_keys(target_text);
                        else:
                            #print("element not found:", select_query)
                            pass
                    except Exception as e:
                        all_command_done = False
                        #print("click fail for selector:", select_query)
                        print(e)
                        pass

                if cmd_dict["type"] == "click":
                    print("click")
                    try:
                        element = await tab.query_selector(cmd_dict["selector"])
                        if element:
                            await element.click()
                        else:
                            #print("element not found:", select_query)
                            pass
                    except Exception as e:
                        all_command_done = False
                        #print("click fail for selector:", select_query)
                        print(e)
                        pass
            time.sleep(0.05)
    return all_command_done

async def eval_to_browser(driver, config_dict, url):
    tmp_filepath = ""
    if "token" in config_dict:
        app_root = util.get_app_root()
        tmp_file = config_dict["token"] + "_eval.tmp"
        tmp_filepath = os.path.join(app_root, tmp_file)

    if os.path.exists(tmp_filepath):
        eval_dict = None
        try:
            with open(tmp_filepath) as json_data:
                eval_dict = json.load(json_data)
                print(eval_dict)
        except Exception as e:
            print("error on open file")
            print(e)
            pass

        if eval_dict:
            #print("nodriver start to eval")
            for each_tab in driver.tabs:
                all_command_done = await eval_to_browser_exist(each_tab, eval_dict, url)

                # must all command success to delete tmp file.
                if all_command_done:
                    try:
                        os.unlink(tmp_filepath)
                        #print("remove file:", tmp_filepath)
                    except Exception as e:
                        pass

async def eval_to_browser_exist(tab, eval_dict, url):
    all_command_done = True
    if "command" in eval_dict:
        for cmd_dict in eval_dict["command"]:
            #print("cmd_dict", cmd_dict)
            matched_location = True
            if "location" in cmd_dict:
                if cmd_dict["location"] != url:
                    matched_location = False

            if matched_location:
                if cmd_dict["type"] == "eval":
                    print("eval")
                    target_script = cmd_dict["script"]
                    try:
                        await tab.evaluate(target_script)
                    except Exception as e:
                        all_command_done = False
                        #print("click fail for selector:", select_query)
                        print(e)
                        pass

            time.sleep(0.05)
    return all_command_done

async def main(args):
    config_dict = get_config_dict(args)
    config_dict["token"] = util.get_token()
    #print("current token:", config_dict["token"])

    driver = None
    tab = None
    if not config_dict is None:
        sandbox = False
        conf = get_extension_config(config_dict)
        nodriver_overwrite_prefs(conf)
        # PS: nodrirver run twice always cause error:
        # Failed to connect to browser
        # One of the causes could be when you are running as root.
        # In that case you need to pass no_sandbox=True
        #driver = await uc.start(conf, sandbox=sandbox, headless=config_dict["advanced"]["headless"])
        driver = await uc.start(conf)
        if not driver is None:
            tab = await nodriver_goto_homepage(driver, config_dict)
            if not config_dict["advanced"]["headless"]:
                print("start to resize window")
                await nodriver_resize_window(driver, config_dict)
        else:
            print("無法使用nodriver，程式無法繼續工作")
            sys.exit()
    else:
        print("Load config error!")

    # internal variable. 說明：這是一個內部變數，請略過。
    url = ""
    last_url = ""

    ocr = None
    try:
        if config_dict["ocr_captcha"]["enable"]:
            ocr = ddddocr.DdddOcr(show_ad=False, beta=config_dict["ocr_captcha"]["beta"])
    except Exception as exc:
        print(exc)
        pass

    is_quit_bot = False
    is_refresh_datetime_sent = False

    while True:
        time.sleep(0.05)

        # pass if driver not loaded.
        if driver is None:
            print("nodriver not accessible!")
            break

        if not is_quit_bot:
            url, is_quit_bot, reset_act_tab = await nodriver_current_url(driver, tab)
            if not reset_act_tab is None:
                tab = reset_act_tab
            #print("act_tab url:", url)

        if not is_refresh_datetime_sent:
            is_refresh_datetime_sent = await check_refresh_datetime_occur(driver, config_dict["refresh_datetime"])

        if is_quit_bot:
            try:
                await driver.stop()
                driver = None
            except Exception as e:
                pass
            break

        if url is None:
            continue
        else:
            if len(url) == 0:
                continue

        await sendkey_to_browser(driver, config_dict, url)
        await eval_to_browser(driver, config_dict, url)

def cli():
    parser = argparse.ArgumentParser(
            description="DDDDEXT Argument Parser")

    parser.add_argument("--input",
        help="config file path",
        type=str)

    parser.add_argument("--homepage",
        help="overwrite homepage setting",
        type=str)

    #default="False",
    parser.add_argument("--headless",
        help="headless mode",
        type=str)

    parser.add_argument("--window_size",
        help="Window size",
        type=str)

    parser.add_argument("--proxy_server",
        help="overwrite proxy server, format: ip:port",
        type=str)

    args = parser.parse_args()
    uc.loop().run_until_complete(main(args))

if __name__ == "__main__":
    cli()

