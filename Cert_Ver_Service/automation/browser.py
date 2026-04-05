from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def build_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def _safe_text(driver, css) -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, css).text.strip()
    except NoSuchElementException:
        return None


def _first_match(driver, *selectors) -> str:
    for css in selectors:
        val = _safe_text(driver, css)
        if val:
            return val
    return None