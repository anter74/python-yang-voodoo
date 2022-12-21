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


def test_missing_enumerations_in_list_elements(runner):
    runner.driver.get(BASE_URL + "/web/testforms")

    plus = runner.get_html_byuuid("/testforms:trio-list", "plus-")
    plus.click()

    key1 = runner.get_html_bybase64id("/testforms:trio-list/key1")
    key1.click()
    key1.send_keys("aaaaaah")

    runner.driver.execute_script(
        f"yangui_set_picker('{runner.path_to_base64('/testforms:trio-list/key2')}','bumblebee')"
    )

    key3 = runner.get_html_bybase64id("/testforms:trio-list/key3")
    key3.click()
    key3.send_keys("55")

    button = runner.get_html_byid("yangui-create-list-button")
    button.click()

    runner.wait_after_ajax()
    runner.wait_after_ajax()
    list_element = runner.get_html_byuuid(
        "/testforms:trio-list[key1='aaaaaah'][key2='bumblebee'][key3='55']", "collapse-"
    )
    runner.assert_screenshot(list_element, "test/yangui/results/ensure_new_listelements_selectpickers_are_visible")

    bob = runner.get_html_bybase64id("/testforms:trio-list[key1='aaaaaah'][key2='bumblebee'][key3='55']/bob")
    bob.click()
    bob.send_keys("BOBBBBBBBBBBBBBBBBBBBYY")
    bob.send_keys(Keys.TAB)
    path = runner.path_to_base64("/testforms:trio-list[key1='aaaaaah'][key2='bumblebee'][key3='55']/alice")
    runner.driver.execute_script(f'yangui_set_picker("{path}","abc", true)')

    runner.wait_after_ajax()

    expand = runner.get_html_byuuid("/testforms:trio-list[key1='aaaaaah'][key2='bumblebee'][key3='55']", "button-")
    expand.click()
    runner.wait_after_ajax()
    expand.click()
    runner.wait_after_ajax()
    expand.click()
    runner.wait_after_ajax()
    expand.click()
    runner.wait_after_ajax()
    expand.click()
    runner.wait_after_ajax()

    list = runner.get_html_byuuid("/testforms:trio-list", "collapse-")
    runner.assert_screenshot(list_element, "test/yangui/results/ensure_new_listelements_dont_repeatedly_add")

    runner.driver.execute_script("yangui_debug_payload()")
    #
    debug = runner.get_html_byid("yangui-content-debug")
    # runner.save_value_to_temporary_file(debug, not_empty=True, attempts=50)
    assert (
        runner.wait_for_text_value(debug, not_empty=True, attempts=100)
        == """{
    "testforms:trio-list": [
        {
            "key1": "aaaaaah",
            "key2": "bumblebee",
            "key3": 55,
            "bob": "BOBBBBBBBBBBBBBBBBBBBYY",
            "alice": "abc"
        }
    ]
}"""
    )
