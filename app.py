from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)

from stem import Signal
from stem.control import Controller

import speech_recognition as sr
from pydub import AudioSegment

from flask import Flask, request, jsonify

import requests
import time
import os
import json

# =========================
# ENV
# =========================

os.environ["PATH"] += ":/data/data/com.termux/files/usr/bin"
os.environ["MOZ_DISABLE_CONTENT_SANDBOX"] = "1"

# =========================
# FLASK
# =========================

app = Flask(__name__)

# =========================
# GLOBAL
# =========================

driver = None
wait = None

# =========================
# TOR IP ROTATE
# =========================

def renew_tor_ip():

    try:

        with Controller.from_port(port=9051) as controller:

            controller.authenticate()

            controller.signal(Signal.CLEARDNSCACHE)

            controller.signal(Signal.NEWNYM)

        print("\nTOR IP CHANGED\n")

        time.sleep(10)

        return True

    except Exception as e:

        print("FAILED CHANGE IP:", e)

        return False

# =========================
# RESTART FIREFOX
# =========================

def restart_driver():

    global driver
    global wait

    print("\nRESTARTING FIREFOX...\n")

    try:
        driver.quit()
    except:
        pass

    time.sleep(1)

    init_driver()

# =========================
# HOME
# =========================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "solver online"
    })

# =========================
# INIT FIREFOX
# =========================

def init_driver():

    global driver
    global wait

    options = Options()

    # headless
    options.add_argument("-headless")

    # termux x11
    options.add_argument("--display=:1")

    # =========================
    # TOR
    # =========================

    options.set_preference(
        "network.proxy.type",
        1
    )

    options.set_preference(
        "network.proxy.socks",
        "127.0.0.1"
    )

    options.set_preference(
        "network.proxy.socks_port",
        9050
    )

    options.set_preference(
        "network.proxy.socks_version",
        5
    )

    options.set_preference(
        "network.proxy.socks_remote_dns",
        True
    )

    # =========================
    # ANTI LEAK
    # =========================

    options.set_preference(
        "media.peerconnection.enabled",
        False
    )

    # =========================
    # ANTI FINGERPRINT
    # =========================

    options.set_preference(
        "privacy.firstparty.isolate",
        True
    )

    options.set_preference(
        "network.cookie.cookieBehavior",
        1
    )

    options.set_preference(
        "privacy.resistFingerprinting",
        True
    )

    # =========================
    # ANTI SELENIUM
    # =========================

    options.set_preference(
        "dom.webdriver.enabled",
        False
    )

    options.set_preference(
        "useAutomationExtension",
        False
    )

    options.set_preference(
        "media.navigator.enabled",
        False
    )

    # =========================
    # SPEED
    # =========================

    options.set_preference(
        "permissions.default.image",
        2
    )

    options.set_preference(
        "toolkit.cosmeticAnimations.enabled",
        False
    )

    options.set_preference(
        "browser.cache.disk.enable",
        True
    )

    options.set_preference(
        "browser.cache.memory.enable",
        True
    )

    # =========================
    # STARTUP
    # =========================

    options.set_preference(
        "browser.startup.page",
        0
    )

    options.set_preference(
        "browser.startup.homepage",
        "about:blank"
    )

    options.set_preference(
        "startup.homepage_welcome_url",
        "about:blank"
    )

    options.set_preference(
        "startup.homepage_welcome_url.additional",
        ""
    )

    options.set_preference(
        "browser.newtabpage.enabled",
        False
    )

    print("START FIREFOX")

    service = Service(
        "/data/data/com.termux/files/usr/bin/geckodriver",
        log_output=os.devnull
    )

    driver = webdriver.Firefox(
        service=service,
        options=options
    )

    driver.set_window_size(900, 700)

    driver.set_page_load_timeout(30)

    wait = WebDriverWait(driver, 15)

    # remove extra tabs
    tabs = driver.window_handles

    if len(tabs) > 1:

        main_tab = tabs[0]

        for tab in tabs[1:]:

            driver.switch_to.window(tab)
            driver.close()

        driver.switch_to.window(main_tab)

    # block popup
    driver.execute_script("""
    window.open = function(){};
    """)

    print("FIREFOX READY")

# =========================
# SWITCH ANCHOR
# =========================

def switch_to_anchor():

    global driver

    driver.switch_to.default_content()

    frames = driver.find_elements(By.TAG_NAME, "iframe")

    for frame in frames:

        try:

            src = frame.get_attribute("src")

            if src and "anchor" in src:

                driver.switch_to.frame(frame)

                return True

        except:
            pass

    return False

# =========================
# SWITCH BFRAME
# =========================

def switch_to_bframe():

    global driver

    driver.switch_to.default_content()

    frames = driver.find_elements(By.TAG_NAME, "iframe")

    for frame in frames:

        try:

            src = frame.get_attribute("src")

            if src and "bframe" in src:

                driver.switch_to.frame(frame)

                return True

        except:
            pass

    return False

# =========================
# SOLVER
# =========================

def solve_recaptcha(url):

    global driver
    global wait

    recognizer = sr.Recognizer()

    session = requests.Session()

    solve_start = time.time()

    try:

        # =========================
        # NEW TOR IP
        # =========================

        renew_tor_ip()

        # =========================
        # CHECK IP
        # =========================

        driver.get("https://api.ipify.org")

        print("TOR IP:", driver.page_source)

        # =========================
        # OPEN TARGET
        # =========================

        driver.delete_all_cookies()

        print("\nOPEN:", url)

        driver.get(url)

        

        print("TITLE:", driver.title)

        # =========================
        # FIND CHECKBOX
        # =========================

        if not switch_to_anchor():

            return {
                "success": False,
                "message": "anchor iframe not found"
            }

        checkbox = wait.until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "recaptcha-anchor"
                )
            )
        )

        checkbox.click()

        print("CHECKBOX CLICKED")

        time.sleep(1)

        # =========================
        # AUDIO MODE
        # =========================

        if not switch_to_bframe():

            return {
                "success": False,
                "message": "bframe not found"
            }

        audio_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "recaptcha-audio-button"
                )
            )
        )

        audio_button.click()

        print("AUDIO MODE CLICKED")

        # =========================
        # ATTEMPTS
        # =========================

        for attempt in range(10):

            try:

                print(f"\nATTEMPT {attempt + 1}")

                # refresh frame
                if not switch_to_bframe():

                    raise Exception("bframe missing")

                # =========================
                # AUDIO URL
                # =========================

                audio_source = wait.until(
                    EC.presence_of_element_located(
                        (
                            By.ID,
                            "audio-source"
                        )
                    )
                )

                audio_url = audio_source.get_attribute("src")

                print("AUDIO URL:", audio_url)

                # =========================
                # DOWNLOAD AUDIO
                # =========================

                r = session.get(
                    audio_url,
                    timeout=15
                )

                with open("captcha.mp3", "wb") as f:

                    f.write(r.content)

                print("AUDIO DOWNLOADED")

                # =========================
                # MP3 -> WAV
                # =========================

                AudioSegment.from_mp3(
                    "captcha.mp3"
                ).export(
                    "captcha.wav",
                    format="wav"
                )

                print("WAV CREATED")

                # =========================
                # SPEECH RECOGNITION
                # =========================

                with sr.AudioFile("captcha.wav") as source:

                    audio_data = recognizer.record(source)

                text = recognizer.recognize_google(
                    audio_data
                )

                print("TEXT:", text)

                # =========================
                # INPUT ANSWER
                # =========================

                input_box = wait.until(
                    EC.presence_of_element_located(
                        (
                            By.ID,
                            "audio-response"
                        )
                    )
                )

                input_box.clear()

                input_box.send_keys(text)

                print("ANSWER TYPED")

                # =========================
                # VERIFY
                # =========================

                wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.ID,
                            "recaptcha-verify-button"
                        )
                    )
                ).click()

                print("VERIFY CLICKED")

                time.sleep(1)

                # =========================
                # CHECK SOLVED
                # =========================

                solved = False

                if switch_to_anchor():

                    checked = wait.until(
                        EC.presence_of_element_located(
                            (
                                By.ID,
                                "recaptcha-anchor"
                            )
                        )
                    ).get_attribute(
                        "aria-checked"
                    )

                    print("CHECKED:", checked)

                    if checked == "true":

                        solved = True

                if solved:

                    print("\nCAPTCHA SOLVED")

                    driver.switch_to.default_content()

                    token = driver.execute_script("""
                    return document.getElementById(
                        'g-recaptcha-response'
                    ).value
                    """)

                    result = {
                        "success": True,
                        "token": token,
                        "solve_time": round(
                            time.time() - solve_start,
                            2
                        )
                    }

                    print(
                        json.dumps(
                            result,
                            indent=4
                        )
                    )

                    return result

                print("NOT SOLVED")

            except (
                NoSuchElementException,
                TimeoutException,
                WebDriverException,
                Exception
            ) as e:

                print("\nATTEMPT ERROR:", e)

                # =========================
                # CHANGE TOR IP
                # =========================

                print("\nCHANGING TOR IP...\n")

                renew_tor_ip()

                # =========================
                # RESTART FIREFOX
                # =========================

                restart_driver()

                try:

                    # check new ip
                    driver.get("https://api.ipify.org")

                    print(
                        "NEW TOR IP:",
                        driver.page_source
                    )

                    # reopen target
                    driver.delete_all_cookies()

                    driver.get(url)

                    time.sleep(1)

                except Exception as err:

                    print("REOPEN ERROR:", err)

                continue

        return {
            "success": False,
            "message": "failed solve captcha",
            "solve_time": round(
                time.time() - solve_start,
                2
            )
        }

    except Exception as e:

        print("MAIN ERROR:", e)

        renew_tor_ip()

        restart_driver()

        return {
            "success": False,
            "message": str(e),
            "solve_time": round(
                time.time() - solve_start,
                2
            )
        }

# =========================
# API
# =========================

@app.route("/solve", methods=["POST"])
def solve():

    data = request.json

    if not data:

        return jsonify({
            "success": False,
            "message": "json required"
        })

    url = data.get("url")

    if not url:

        return jsonify({
            "success": False,
            "message": "url required"
        })

    result = solve_recaptcha(url)

    return jsonify(result)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    init_driver()

    app.run(
        host="0.0.0.0",
        port=7860,
        threaded=True
    )
