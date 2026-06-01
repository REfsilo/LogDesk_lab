import os
import pytest
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


BASE_URL = "http://127.0.0.1:5000"


@pytest.fixture
def driver(request):
    options = Options()
    options.add_argument("--window-size=1366,768")

    browser = webdriver.Chrome(options=options)

    try:
        requests.post(f"{BASE_URL}/test/reset", timeout=3)
    except requests.exceptions.RequestException:
        pass

    yield browser

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        os.makedirs("reports/screenshots", exist_ok=True)

        screenshot_path = f"reports/screenshots/{request.node.name}.png"
        browser.save_screenshot(screenshot_path)

        print(f"\nСкриншот ошибки сохранён: {screenshot_path}")

    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()

    setattr(item, "rep_" + report.when, report)
