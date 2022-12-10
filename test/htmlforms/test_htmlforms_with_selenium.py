import base64
import os
import time
from multiprocessing import Process

import pytest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


os.environ["YANGUI_BIND_PORT"] = "8096"
os.environ["YANGUI_BASE_API"] = "http://127.0.0.1:8096"

from examples.htmlforms.stubserver import do


BASE_URL = "http://127.0.0.1:8099"


def get_html_byid(driver, path):
    return driver.find_element(By.ID, path)


def get_yangui_element(driver, path):
    return driver.find_element(By.ID, base64.urlsafe_b64encode(path.encode("utf-8")).decode("utf-8"))


def wait_for_text_value(element, not_empty=True, attempts=100):
    # get_attribute('innerHTML')
    for attempt in range(attempts):
        if element.get_attribute("value"):
            return element.get_attribute("value")
        time.sleep(0.1)

    assert False, f"{element} still empty after {attempts} attempts"


def wait_for_text(element, text, exact=True, attempts=100):
    # get_attribute('innerHTML')
    for attempt in range(attempts):
        if text == element.text or (exact and text in element.text):
            return element.text
        time.sleep(0.1)

    assert False, f"'{text}' not found in {element} after {attempts} attempts"


@pytest.fixture
def driver(monkeypatch):
    # p = Process(target=do)
    # p.start()
    # time.sleep(2)

    options = webdriver.ChromeOptions()
    options.add_argument("--enable-javascript")

    chrome = webdriver.Chrome("./chromedriver", options=options)
    yield chrome

    chrome.quit()


def test_simple_test_rendering_of_a_page(driver):
    driver.get(BASE_URL + "/web/testforms")
    # element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "yangui-page-render-done")))
    # driver.execute_script("stop_yangui_spinner();")
    # stop_yangui_spinneri
    assert driver.title == "YANG Unicorn Interface ✨ 🦄 ✨ - 💣 Prototype 💣 - testforms"

    textbox = get_yangui_element(driver, "/testforms:simpleleaf")
    textbox.click()
    textbox.send_keys("ax")
    textbox.send_keys(Keys.TAB)

    textbox = get_yangui_element(driver, "/testforms:topleaf")
    textbox.send_keys("a")

    button = get_html_byid(driver, "yangui-validate-button")
    button.click()

    danger = get_html_byid(driver, "yangui-msg-danger")
    success = get_html_byid(driver, "yangui-msg-success")

    assert wait_for_text(success, "payload successfully validated", attempts=50)
    assert danger.text == ""

    driver.execute_script("debug_payload()")

    debug = get_html_byid(driver, "yangui-content-debug")
    assert (
        wait_for_text_value(debug, not_empty=True, attempts=50)
        == """{
    "testforms:simpleleaf": "ax",
    "testforms:topleaf": "a"
}"""
    )
