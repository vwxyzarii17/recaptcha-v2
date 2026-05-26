from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import speech_recognition as sr
from pydub import AudioSegment

from flask import Flask, request, jsonify

from threading import Lock

import requests
import time
import random
import os
import json

# =========================
# ENV
# =========================

os.environ["DISPLAY"] = ":99"
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
# THREAD LOCK
# =========================

driver_lock = Lock()

# =========================
# INIT DRIVER
# =========================

def init_driver():

    global driver
    global wait

    options = Options()

    # =========================
    # NON HEADLESS
    # =========================

    # JANGAN tambah --headless

    options.add_argument("--width=900")
    options.add_argument("--height=700")

    # =========================
    # ANTI DETECT
    # =========================

    options.set_preference(
        "dom.webdriver.enabled",
        False
    )

    options.set_preference(
        "media.navigator.enabled",
        False
    )

    options.set_preference(
        "media.peerconnection.enabled",
        False
    )

    options.set_preference(
        "privacy.resistFingerprinting",
        False
    )

    options.set_preference(
        "webgl.disabled",
        False
    )

    options.set_preference(
        "useAutomationExtension",
        False
    )

    # =========================
    # PERFORMANCE
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

    options.set_preference(
        "browser.tabs.remote.autostart",
        False
    )

    # =========================
    # USER AGENT
    # =========================

    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Android 13; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0"
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

    driver.set_window_size(900, 700)

    wait = WebDriverWait(driver, 20)

    driver.get("about:blank")

    print("firefox ready")

# =========================
# CAPTCHA SOLVER
# =========================

def solve_recaptcha(url):

    global driver
    global wait

    solve_start = time.time()

    recognizer = sr.Recognizer()

    session = requests.Session()

    main_tab = driver.current_window_handle

    driver.execute_script(
        "window.open('about:blank','_blank');"
    )

    driver.switch_to.window(
        driver.window_handles[-1]
    )

    try:

        print("\nOPEN:", url)

        driver.get(url)

        time.sleep(random.uniform(2, 4))

        # =========================
        # FIND RECAPTCHA
        # =========================

        frames = driver.find_elements(
            By.TAG_NAME,
            "iframe"
        )

        found = False

        for frame in frames:

            src = frame.get_attribute("src")

            if src and "anchor" in src:

                driver.switch_to.frame(frame)

                found = True
                break

        if not found:

            return {
                "success": False,
                "message": "recaptcha not found"
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

        time.sleep(random.uniform(1, 2))

        checkbox.click()

        print("checkbox clicked")

        # =========================
        # OPEN AUDIO MODE
        # =========================

        driver.switch_to.default_content()

        frames = driver.find_elements(
            By.TAG_NAME,
            "iframe"
        )

        for frame in frames:

            src = frame.get_attribute("src")

            if src and "bframe" in src:

                driver.switch_to.frame(frame)
                break

        audio_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "recaptcha-audio-button"
                )
            )
        )

        time.sleep(random.uniform(1, 2))

        audio_button.click()

        print("audio mode opened")

        time.sleep(2)

        # =========================
        # SOLVE LOOP
        # =========================

        for attempt in range(10):

            try:

                print(f"\nATTEMPT {attempt+1}")

                audio_source = wait.until(
                    EC.presence_of_element_located(
                        (
                            By.ID,
                            "audio-source"
                        )
                    )
                )

                audio_url = audio_source.get_attribute("src")

                print("audio:", audio_url)

                # =========================
                # DOWNLOAD AUDIO
                # =========================

                r = session.get(
                    audio_url,
                    timeout=15
                )

                with open(
                    "captcha.mp3",
                    "wb"
                ) as f:

                    f.write(r.content)

                print("audio downloaded")

                # =========================
                # CONVERT
                # =========================

                AudioSegment.from_mp3(
                    "captcha.mp3"
                ).export(
                    "captcha.wav",
                    format="wav"
                )

                print("converted")

                # =========================
                # SPEECH TO TEXT
                # =========================

                with sr.AudioFile(
                    "captcha.wav"
                ) as source:

                    audio_data = recognizer.record(source)

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

                time.sleep(random.uniform(0.5, 1))

                input_box.send_keys(text)

                print("typed")

                # =========================
                # VERIFY
                # =========================

                verify_button = driver.find_element(
                    By.ID,
                    "recaptcha-verify-button"
                )

                time.sleep(random.uniform(0.5, 1))

                verify_button.click()

                print("verify clicked")

                time.sleep(3)

                # =========================
                # CHECK SUCCESS
                # =========================

                driver.switch_to.default_content()

                frames = driver.find_elements(
                    By.TAG_NAME,
                    "iframe"
                )

                solved = False

                for frame in frames:

                    src = frame.get_attribute("src")

                    if src and "anchor" in src:

                        driver.switch_to.frame(frame)

                        checked = driver.find_element(
                            By.ID,
                            "recaptcha-anchor"
                        ).get_attribute(
                            "aria-checked"
                        )

                        if checked == "true":

                            solved = True

                        break

                if solved:

                    driver.switch_to.default_content()

                    token = wait.until(
                        EC.presence_of_element_located(
                            (
                                By.NAME,
                                "g-recaptcha-response"
                            )
                        )
                    ).get_attribute("value")

                    result = {
                        "success": True,
                        "token": token,
                        "solve_time": round(
                            time.time() - solve_start,
                            2
                        )
                    }

                    print(json.dumps(result, indent=4))

                    return result

                print("retrying")

                driver.switch_to.default_content()

                frames = driver.find_elements(
                    By.TAG_NAME,
                    "iframe"
                )

                for frame in frames:

                    src = frame.get_attribute("src")

                    if src and "bframe" in src:

                        driver.switch_to.frame(frame)
                        break

                reload_btn = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.ID,
                            "recaptcha-reload-button"
                        )
                    )
                )

                reload_btn.click()

                time.sleep(2)

            except Exception as e:

                print("attempt error:", e)

        return {
            "success": False,
            "message": "failed solve"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        try:

            driver.delete_all_cookies()

        except:
            pass

        try:

            driver.execute_script("""
            window.localStorage.clear();
            window.sessionStorage.clear();
            """)

        except:
            pass

        try:

            driver.close()

            driver.switch_to.window(main_tab)

            driver.get("about:blank")

        except Exception as e:

            print("tab cleanup error:", e)

        for f in ["captcha.mp3", "captcha.wav"]:

            if os.path.exists(f):

                os.remove(f)

# =========================
# API
# =========================

@app.route("/")
def home():

    return jsonify({
        "status": "running"
    })

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

    with driver_lock:

        global driver

        if driver is None:

            init_driver()

        result = solve_recaptcha(url)

    return jsonify(result)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    init_driver()

    port = int(
        os.environ.get(
            "PORT",
            7860
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
  )
