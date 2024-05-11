#!/usr/bin/env python3
#encoding=utf-8
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
import warnings
import webbrowser
from datetime import datetime

import nodriver as uc
from nodriver import cdp
from nodriver.core.config import Config
from urllib3.exceptions import InsecureRequestWarning
import urllib.parse

import util

try:
    import ddddocr
except Exception as exc:
    print(exc)
    pass

CONST_APP_VERSION = "MaxBot (2024.04.16)"

CONST_MAXBOT_ANSWER_ONLINE_FILE = "MAXBOT_ONLINE_ANSWER.txt"
CONST_MAXBOT_CONFIG_FILE = "settings.json"
CONST_DDDDEXT_EXTENSION_NAME = "ddddplus_1.0.0"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

warnings.simplefilter('ignore',InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig()
logger = logging.getLogger('logger')

def get_config_dict():
    app_root = util.get_app_root()
    config_filepath = os.path.join(app_root, CONST_MAXBOT_CONFIG_FILE)

    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath) as json_data:
            config_dict = json.load(json_data)

    return config_dict

async def nodriver_goto_homepage(driver, config_dict):
    homepage = config_dict["homepage"]
    try:
        tab = await driver.get(homepage)
        await tab.get_content()
    except Exception as e:
        pass
    return tab


def get_nodriver_browser_args():
    browser_args = [
        "--user-agent=%s" % (USER_AGENT),
        "--disable-2d-canvas-clip-aa",
        "--disable-3d-apis",
        "--disable-animations",
        "--disable-app-info-dialog-mac",
        "--disable-background-networking",
        "--disable-backgrounding-occluded-windows",
        "--disable-bookmark-reordering",
        "--disable-boot-animation",
        "--disable-breakpad",
        "--disable-canvas-aa",
        "--disable-client-side-phishing-detection",
        "--disable-cloud-import",
        "--disable-component-cloud-policy",
        "--disable-component-update",
        "--disable-composited-antialiasing",
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
        "--disable-office-editing-component-extension",
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
        "--no-sandbox"
        "--no-service-autorun",
        "--password-store=basic",
        "--remote-allow-origins=*",
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

def get_extension_config(config_dict):
    default_lang = "zh-TW"
    no_sandbox=True
    browser_args = get_nodriver_browser_args()
    conf = Config(browser_args=browser_args, lang=default_lang, no_sandbox=no_sandbox)
    if config_dict["advanced"]["chrome_extension"]:
        ext = get_maxbot_extension_path(CONST_DDDDEXT_EXTENSION_NAME)
        if len(ext) > 0:
            conf.add_extension(ext)
            util.dump_settings_to_maxbot_plus_extension(ext, config_dict, CONST_MAXBOT_CONFIG_FILE)
    return conf

async def nodriver_resize_window(tab, config_dict):
    if len(config_dict["advanced"]["window_size"]) > 0:
        if "," in config_dict["advanced"]["window_size"]:
            size_array = config_dict["advanced"]["window_size"].split(",")
            position_left = 0
            if len(size_array) >= 3:
                position_left = int(size_array[0]) * int(size_array[2])
            #tab = await driver.main_tab()
            if tab:
                await tab.set_window_size(left=position_left, top=30, width=int(size_array[0]), height=int(size_array[1]))

async def nodriver_current_url(tab):
    is_quit_bot = False
    exit_bot_error_strings = [
        "server rejected WebSocket connection: HTTP 500",
        "[Errno 61] Connect call failed ('127.0.0.1',",
        "[WinError 1225] ",
    ]

    url = ""
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
    return url, is_quit_bot

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

async def main():
    config_dict = get_config_dict()

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
            await nodriver_resize_window(tab, config_dict)
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

    maxbot_last_reset_time = time.time()
    is_quit_bot = False
    while True:
        time.sleep(0.05)

        # pass if driver not loaded.
        if driver is None:
            print("nodriver not accessible!")
            break

        if not is_quit_bot:
            url, is_quit_bot = await nodriver_current_url(tab)

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

def cli():
    uc.loop().run_until_complete(main())

if __name__ == "__main__":
    cli()

