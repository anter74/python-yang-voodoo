import os
import time

import pytest


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from test.yangui.browser import Runner

os.environ["YANGUI_BIND_PORT"] = "8096"
os.environ["YANGUI_BASE_API"] = "http://127.0.0.1:8096"

from examples.htmlforms.stubserver import do

DELAY_AFTER_FILE_SELECTION = 0.5
BASE_URL = "http://127.0.0.1:8099"


@pytest.fixture
def runner(monkeypatch):
    # p = Process(target=do)
    # p.start()
    # time.sleep(2)

    options = webdriver.ChromeOptions()
    options.add_argument("--enable-javascript")

    chrome = webdriver.Chrome("./chromedriver", options=options)
    yield Runner(chrome)

    chrome.quit()


def test_simple_test_uploading_form(runner):
    runner.get(BASE_URL + "/web/testforms")
    # element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "yangui-page-render-done")))
    # driver.execute_script("stop_yangui_spinner();")
    # stop_yangui_spinneri
    assert runner.driver.title == "YANG Unicorn Interface ✨ 🦄 ✨ - 💣 Prototype 💣 - testforms"
    button = runner.get_html_byid("yangui-upload-button")
    button.click()

    input_file = runner.get_html_byid("yangui-file-input")
    runner.wait_for_visible("yanguiUploadModal")
    input_file.send_keys(f"{os.getcwd()}/templates/forms/upload.json")

    time.sleep(DELAY_AFTER_FILE_SELECTION)
    button = runner.get_html_byid("yangui-file-button")
    button.send_keys(Keys.ENTER)

    runner.assert_screenshot("nav-tabContent", "test/yangui/results/test_simple_uploading_form")


def test_simple_test_completing_lists(runner):
    runner.driver.get(BASE_URL + "/web/testforms")

    textbox = runner.get_yangui_element("/testforms:simpleleaf")
    textbox.click()
    textbox.send_keys("ax")
    textbox.send_keys(Keys.TAB)

    textbox = runner.get_yangui_element("/testforms:topleaf")
    textbox.send_keys("a")

    runner.get_html_byuuid("/testforms:mainlist", "plus-").click()

    runner.get_html_bybase64id("/testforms:mainlist/mainkey").click()
    runner.get_html_bybase64id("/testforms:mainlist/mainkey").send_keys("a")
    runner.get_html_bybase64id("/testforms:mainlist/subkey").click()
    runner.get_html_bybase64id("/testforms:mainlist/subkey").send_keys("a")
    runner.get_html_byid("yangui-create-list-button").click()
    time.sleep(4)

    button = runner.get_html_byid("yangui-validate-button")
    button.click()

    success = runner.get_html_byid("yangui-msg-success")
    assert runner.wait_for_text(success, "payload successfully validated", attempts=50)

    assert runner.get_html_byid("yangui-msg-danger").text == ""

    runner.driver.execute_script("yangui_debug_payload()")

    debug = runner.get_html_byid("yangui-content-debug")
    # runner.save_value_to_temporary_file(debug, not_empty=True, attempts=50)

    assert (
        runner.wait_for_text_value(debug, not_empty=True, attempts=100)
        == """{
    "testforms:simpleleaf": "ax",
    "testforms:topleaf": "a",
    "testforms:mainlist": [
        {
            "mainkey": "a",
            "subkey": "a"
        }
    ]
}"""
    )


def test_simple_test_rendering_of_a_page(runner):
    runner.get(BASE_URL + "/web/testforms")
    assert runner.driver.title == "YANG Unicorn Interface ✨ 🦄 ✨ - 💣 Prototype 💣 - testforms"

    textbox = runner.get_yangui_element("/testforms:simpleleaf")
    textbox.click()
    textbox.send_keys("ax")
    textbox.send_keys(Keys.TAB)

    textbox = runner.get_yangui_element("/testforms:topleaf")
    textbox.send_keys("a")

    button = runner.get_html_byid("yangui-validate-button")
    button.click()

    success = runner.get_html_byid("yangui-msg-success")
    assert runner.wait_for_text(success, "payload successfully validated", attempts=50)

    assert runner.get_html_byid("yangui-msg-danger").text == ""

    runner.driver.execute_script("yangui_debug_payload()")

    debug = runner.get_html_byid("yangui-content-debug")
    assert (
        runner.wait_for_text_value(debug, not_empty=True, attempts=50)
        == """{
    "testforms:simpleleaf": "ax",
    "testforms:topleaf": "a"
}"""
    )
