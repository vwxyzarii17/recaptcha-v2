from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException
)

from stem import Signal
from stem.control import Controller

import speech_recognition as sr
from pydub import AudioSegment

from flask import Flask, request, jsonify

import requests
import threading
import tempfile
import traceback
import atexit
import time
import os
import uuid

# =========================
# FLASK
# =========================

app = Flask(__name__)

# =========================
# GLOBAL
# =========================

driver = None
wait = None
MAIN_WINDOW = None

driver_lock = threading.Lock()

REQUEST_COUNT = 0
MAX_REQUEST_BEFORE_RESTART = 100

# =========================
# TOR ROTATE
# =========================

def renew_tor_ip():

    try:

        with Controller.from_port(port=9051) as controller:

            controller.authenticate()

            controller.signal(Signal.NEWNYM)

        print("TOR IP CHANGED")

        time.sleep(5)

        return True

    except Exception as e:

        print("TOR ERROR:", e)

        return False

# =========================
# INIT DRIVER
# =========================

def init_driver():

    global driver
    global wait
    global MAIN_WINDOW

    try:

        print("INIT FIREFOX DRIVER")

        options = Options()

        # =========================
        # FIREFOX BIN
        # =========================

        options.binary_location = "/usr/bin/firefox-esr"

        # =========================
        # HEADLESS
        # =========================

        options.add_argument("-headless")

        # =========================
        # CONTAINER FIX
        # =========================

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # =========================
        # PERFORMANCE
        # =========================

        options.set_preference(
            "permissions.default.image",
            2
        )

        options.set_preference(
            "browser.display.use_document_fonts",
            0
        )

        options.set_preference(
            "toolkit.cosmeticAnimations.enabled",
            False
        )

        options.set_preference(
            "browser.tabs.animate",
            False
        )

        # =========================
        # LOAD STRATEGY
        # =========================

        options.set_preference(
            "webdriver.load.strategy",
            "eager"
        )

        # =========================
        # TOR SOCKS
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
        # WEBRTC LEAK FIX
        # =========================

        options.set_preference(
            "media.peerconnection.enabled",
            False
        )

        # =========================
        # ANTI SELENIUM
        # =========================

        options.set_preference(
            "dom.webdriver.enabled",
            False
        )

        # =========================
        # DRIVER
        # =========================

        service = Service(
            "/usr/local/bin/geckodriver"
        )

        driver = webdriver.Firefox(
            service=service,
            options=options
        )

        driver.set_window_size(1280, 720)

        driver.set_page_load_timeout(20)

        wait = WebDriverWait(driver, 10)

        MAIN_WINDOW = driver.current_window_handle

        print("FIREFOX READY")

    except Exception as e:

        print("INIT DRIVER ERROR")
        print(str(e))
        traceback.print_exc()

        driver = None

# =========================
# ENSURE DRIVER
# =========================

def ensure_driver():

    global driver

    try:

        if driver is None:

            print("DRIVER NONE -> REINIT")

            init_driver()

            return

        driver.title

    except Exception:

        print("DRIVER DEAD -> REINIT")

        try:
            driver.quit()
        except:
            pass

        init_driver()

# =========================
# RESTART DRIVER
# =========================

def restart_driver():

    global driver

    print("RESTART DRIVER")

    try:

        if driver:

            driver.quit()

    except:
        pass

    init_driver()

# =========================
# CREATE TAB
# =========================

def create_page():

    global driver

    driver.switch_to.new_window("tab")

# =========================
# CLOSE TAB
# =========================

def close_page():

    global driver
    global MAIN_WINDOW

    try:

        current = driver.current_window_handle

        if current != MAIN_WINDOW:

            driver.close()

            driver.switch_to.window(MAIN_WINDOW)

    except Exception as e:

        print("CLOSE PAGE ERROR:", e)

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

    global REQUEST_COUNT
    global driver
    global wait

    start_time = time.time()

    recognizer = sr.Recognizer()

    session = requests.Session()

    uid = str(uuid.uuid4())

    mp3_path = os.path.join(
        tempfile.gettempdir(),
        f"{uid}.mp3"
    )

    wav_path = os.path.join(
        tempfile.gettempdir(),
        f"{uid}.wav"
    )

    try:

        with driver_lock:

            # =========================
            # ENSURE DRIVER
            # =========================

            ensure_driver()

            if driver is None:

                return {
                    "success": False,
                    "message": "driver failed init"
                }

            # =========================
            # AUTO RESTART
            # =========================

            REQUEST_COUNT += 1

            if REQUEST_COUNT >= MAX_REQUEST_BEFORE_RESTART:

                REQUEST_COUNT = 0

                restart_driver()

            # =========================
            # NEW TAB
            # =========================

            create_page()

            print("OPEN:", url)

            driver.get(url)

            # =========================
            # SWITCH ANCHOR
            # =========================

            if not switch_to_anchor():

                close_page()

                return {
                    "success": False,
                    "message": "anchor iframe not found"
                }

            # =========================
            # CLICK CHECKBOX
            # =========================

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

            time.sleep(2)

            # =========================
            # SWITCH BFRAME
            # =========================

            if not switch_to_bframe():

                close_page()

                return {
                    "success": False,
                    "message": "bframe iframe not found"
                }

            # =========================
            # AUDIO BUTTON
            # =========================

            audio_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.ID,
                        "recaptcha-audio-button"
                    )
                )
            )

            audio_button.click()

            print("AUDIO MODE")

            # =========================
            # ATTEMPTS
            # =========================

            for attempt in range(5):

                try:

                    print(f"ATTEMPT {attempt+1}")

                    if not switch_to_bframe():

                        raise Exception(
                            "bframe missing"
                        )

                    # =========================
                    # AUDIO SOURCE
                    # =========================

                    audio_source = wait.until(
                        EC.presence_of_element_located(
                            (
                                By.ID,
                                "audio-source"
                            )
                        )
                    )

                    audio_url = audio_source.get_attribute(
                        "src"
                    )

                    print("AUDIO URL:", audio_url)

                    # =========================
                    # DOWNLOAD AUDIO
                    # =========================

                    r = session.get(
                        audio_url,
                        timeout=15
                    )

                    with open(mp3_path, "wb") as f:

                        f.write(r.content)

                    # =========================
                    # CONVERT AUDIO
                    # =========================

                    AudioSegment.from_mp3(
                        mp3_path
                    ).export(
                        wav_path,
                        format="wav"
                    )

                    # =========================
                    # SPEECH TO TEXT
                    # =========================

                    with sr.AudioFile(
                        wav_path
                    ) as source:

                        audio_data = recognizer.record(
                            source
                        )

                    text = recognizer.recognize_google(
                        audio_data
                    )

                    print("TEXT:", text)

                    # =========================
                    # INPUT
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

                    # =========================
                    # VERIFY
                    # =========================

                    verify_button = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.ID,
                                "recaptcha-verify-button"
                            )
                        )
                    )

                    verify_button.click()

                    time.sleep(3)

                    # =========================
                    # CHECK SOLVED
                    # =========================

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

                            driver.switch_to.default_content()

                            token = driver.execute_script("""
                                return document.getElementById(
                                    'g-recaptcha-response'
                                ).value
                            """)

                            close_page()

                            return {
                                "success": True,
                                "token": token,
                                "solve_time": round(
                                    time.time() - start_time,
                                    2
                                )
                            }

                    print("FAILED")

                    renew_tor_ip()

                    driver.refresh()

                    time.sleep(3)

                except Exception as e:

                    print("ATTEMPT ERROR:", e)

                    renew_tor_ip()

                    driver.refresh()

                    time.sleep(3)

            close_page()

            return {
                "success": False,
                "message": "failed solve captcha",
                "solve_time": round(
                    time.time() - start_time,
                    2
                )
            }

    except (
        TimeoutException,
        WebDriverException,
        Exception
    ) as e:

        print("MAIN ERROR:", e)

        traceback.print_exc()

        close_page()

        return {
            "success": False,
            "message": str(e),
            "solve_time": round(
                time.time() - start_time,
                2
            )
        }

    finally:

        try:

            if os.path.exists(mp3_path):

                os.remove(mp3_path)

            if os.path.exists(wav_path):

                os.remove(wav_path)

        except:
            pass

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
# HEALTH
# =========================

@app.route("/health")
def health():

    global driver

    return jsonify({
        "success": True,
        "driver_alive": driver is not None
    })

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
# CLEANUP
# =========================

@atexit.register
def cleanup():

    global driver

    try:

        if driver:

            print("QUIT DRIVER")

            driver.quit()

    except:
        pass

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    init_driver()

    if driver is None:

        print("FAILED INIT DRIVER")

    port = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
        )
