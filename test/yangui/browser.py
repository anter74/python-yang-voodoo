import base64
import os
import hashlib
import tempfile
import time
import uuid

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

YANGUI_SELENIUM_LAST_FAILED_SCREENSHOT = "/tmp/yangui-selenium-last-pytest-screenshot.png"


class Runner:
    def __init__(self, driver):
        self.driver = driver

    @staticmethod
    def path_to_base64(path):
        return base64.urlsafe_b64encode(path.encode("utf-8")).decode("utf-8")

    def wait_after_ajax(self):
        if self.driver == "firefox":
            time.sleep(3)
        time.sleep(0.5)

    def get(self, url):
        self.driver.get(url)

    def get_file_md5sum(self, file):
        return hashlib.md5(open(file, "rb").read()).hexdigest()

    def wait_for_visible(self, element, property="display", css="block", attempts=50):
        for attempt in range(attempts):
            try:
                v = self.get_html_byid(element)
            except:
                continue
            if v.value_of_css_property(property) == css:
                return True
            time.sleep(0.1)
        assert (
            False
        ), f"{element} does not have css property {property} == {css} after {attempts} (got {v.value_of_css_property(property)})"

    def wait_for_not_visible(self, element, property="display", css="none", attempts=50):
        for attempt in range(attempts):
            try:
                v = self.get_html_byid(element)
            except:
                continue
            if v.value_of_css_property(property) == css:
                return True
            time.sleep(0.1)
        assert (
            False
        ), f"{element} does not have css property {property} == {css} after {attempts} (got {v.value_of_css_property(property)})"

    def assert_screenshot(self, id, stored_result):
        tf = tempfile.NamedTemporaryFile(suffix=".png")
        if isinstance(id, str):
            id = self.driver.find_element(By.ID, id)
        id.screenshot(tf.name)

        result_name = f"{stored_result}_{self.driver.name}.png"
        if not os.path.exists(result_name):
            id.screenshot(YANGUI_SELENIUM_LAST_FAILED_SCREENSHOT)
            assert (
                False
            ), f"Stored Screenshot Result: {stored_result}_{self.driver.name}.png does not exist.\nSee\neog {YANGUI_SELENIUM_LAST_FAILED_SCREENSHOT}\ncp {YANGUI_SELENIUM_LAST_FAILED_SCREENSHOT} {os.getcwd()}/{stored_result}_{self.driver.name}.png\n"

        expected_md5sum = self.get_file_md5sum(result_name)
        received_md5sum = self.get_file_md5sum(tf.name)
        if expected_md5sum == received_md5sum:
            return True
        id.screenshot(YANGUI_SELENIUM_LAST_FAILED_SCREENSHOT)
        assert (
            False
        ), f"Stored Screenshot Result: {stored_result}_{self.driver.name}.png {expected_md5sum} != {received_md5sum}\n\nReceived {received_md5sum}:\neog {YANGUI_SELENIUM_LAST_FAILED_SCREENSHOT}\nExpected {expected_md5sum}:\neog {os.getcwd()}/{stored_result}_{self.driver.name}.png\n\ncp {YANGUI_SELENIUM_LAST_FAILED_SCREENSHOT} {os.getcwd()}/{stored_result}_{self.driver.name}.png\n"

    def get_html_byid(self, path):
        return self.driver.find_element(By.ID, path)

    def get_html_bybase64id(self, path):
        return self.driver.find_element(By.ID, base64.urlsafe_b64encode(path.encode("utf-8")).decode("utf-8"))

    def get_html_byuuid(self, path, prefix):
        this_uuid = str(uuid.uuid5(uuid.uuid5(uuid.NAMESPACE_URL, "pyvwu"), path))
        return self.driver.find_element(By.ID, f"{prefix}{this_uuid}")

    def get_yangui_element(self, path):
        return self.driver.find_element(By.ID, base64.urlsafe_b64encode(path.encode("utf-8")).decode("utf-8"))

    @staticmethod
    def wait_for_text_value(element, not_empty=True, attempts=100):
        # get_attribute('innerHTML')
        for attempt in range(attempts):
            if element.get_attribute("value"):
                return element.get_attribute("value")
            time.sleep(0.1)

        assert False, f"{element} still empty after {attempts} attempts"

    @staticmethod
    def save_value_to_temporary_file(element, not_empty=True, attempts=100):
        # get_attribute('innerHTML')
        for attempt in range(attempts):
            if element.get_attribute("value"):
                with open("/tmp/yangui-temp-val", "w") as fh:
                    fh.write(element.get_attribute("value"))
                return True
            time.sleep(0.1)

        assert False, f"{element} still empty after {attempts} attempts"

    @staticmethod
    def wait_for_text(element, text, exact=True, attempts=100):
        # get_attribute('innerHTML')
        for attempt in range(attempts):
            if text == element.text or (exact and text in element.text):
                return element.text
            time.sleep(0.1)

        assert False, f"'{text}' not found in {element} after {attempts} attempts"
