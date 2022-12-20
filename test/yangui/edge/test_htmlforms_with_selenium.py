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
    edge = webdriver.Edge()
    yield Runner(edge)
    edge.quit()


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

    runner.wait_after_ajax()
    runner.wait_for_not_visible("yangui-spinner")
    runner.assert_screenshot("nav-tabContent", "test/yangui/results/test_simple_uploading_form")


#     danger = get_html_byid(driver, "yangui-msg-danger")
#     success = get_html_byid(driver, "yangui-msg-success")
#
#     assert wait_for_text(success, "payload successfully validated", attempts=50)
#     assert danger.text == ""
#
#     driver.execute_script("yangui_debug_payload()")
#
#     debug = get_html_byid(driver, "yangui-content-debug")
#     raise ValueError(debug)
#     assert (
#         wait_for_text_value(debug, not_empty=True, attempts=50)
#         == """{
#     "testforms:simpleleaf": "ax",
#     "testforms:topleaf": "a"
# }"""
#     )


# #
# def test_simple_test_completing_lists(driver):
#     driver.get(BASE_URL + "/web/testforms")
#     # element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "yangui-page-render-done")))
#     # driver.execute_script("stop_yangui_spinner();")
#     # stop_yangui_spinneri
#     assert driver.title == "YANG Unicorn Interface ✨ 🦄 ✨ - 💣 Prototype 💣 - testforms"
#
#     textbox = get_yangui_element(driver, "/testforms:simpleleaf")
#     textbox.click()
#     textbox.send_keys("ax")
#     textbox.send_keys(Keys.TAB)
#
#     textbox = get_yangui_element(driver, "/testforms:topleaf")
#     textbox.send_keys("a")
#
#     get_html_byuuid(driver, "/testforms:mainlist", "plus-").click()
#
#     get_html_bybase64id(driver, "/testforms:mainlist/mainkey").click()
#     get_html_bybase64id(driver, "/testforms:mainlist/mainkey").send_keys("a")
#     get_html_bybase64id(driver, "/testforms:mainlist/subkey").click()
#     get_html_bybase64id(driver, "/testforms:mainlist/subkey").send_keys("a")
#     get_html_byid(driver, "yangui-create-list-button").click()
#     time.sleep(4)
#     get_html_byuuid(driver, "/testforms:mainlist[mainkey='a'][subkey='a']", "collapse-").screenshot("/tmp/a.png")
#
#     button = get_html_byid(driver, "yangui-validate-button")
#     button.click()
#
#     danger = get_html_byid(driver, "yangui-msg-danger")
#     success = get_html_byid(driver, "yangui-msg-success")
#
#     assert wait_for_text(success, "payload successfully validated", attempts=50)
#     assert danger.text == ""
#
#     driver.execute_script("yangui_debug_payload()")
#
#     debug = get_html_byid(driver, "yangui-content-debug")
#     raise ValueError(debug)
#     assert (
#         wait_for_text_value(debug, not_empty=True, attempts=50)
#         == """{
#     "testforms:simpleleaf": "ax",
#     "testforms:topleaf": "a"
# }"""
#     )
#

#
# def test_simple_test_rendering_of_a_page(driver):
#     driver.get(BASE_URL + "/web/testforms")
#     # element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "yangui-page-render-done")))
#     # driver.execute_script("stop_yangui_spinner();")
#     # stop_yangui_spinneri
#     assert driver.title == "YANG Unicorn Interface ✨ 🦄 ✨ - 💣 Prototype 💣 - testforms"
#
#     textbox = get_yangui_element(driver, "/testforms:simpleleaf")
#     textbox.click()
#     textbox.send_keys("ax")
#     textbox.send_keys(Keys.TAB)
#
#     textbox = get_yangui_element(driver, "/testforms:topleaf")
#     textbox.send_keys("a")
#
#     button = get_html_byid(driver, "yangui-validate-button")
#     button.click()
#
#     danger = get_html_byid(driver, "yangui-msg-danger")
#     success = get_html_byid(driver, "yangui-msg-success")
#
#     assert wait_for_text(success, "payload successfully validated", attempts=50)
#     assert danger.text == ""
#
#     driver.execute_script("yangui_debug_payload()")
#
#     debug = get_html_byid(driver, "yangui-content-debug")
#     assert (
#         wait_for_text_value(debug, not_empty=True, attempts=50)
#         == """{
#     "testforms:simpleleaf": "ax",
#     "testforms:topleaf": "a"
# }"""
#     )
