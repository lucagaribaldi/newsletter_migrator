
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
import markdown2

def setup_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def load_cookies(driver, cookies_path):
    driver.get("https://substack.com")
    time.sleep(3)
    with open(cookies_path, "r") as f:
        cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(2)

def create_new_post(driver, title, markdown_content, date=None, save_as_draft=True):
    driver.get("https://substack.com/write")
    time.sleep(5)

    # Inserisci il titolo
    title_input = driver.find_element(By.CSS_SELECTOR, "textarea[data-testid='post-title-input']")
    title_input.clear()
    title_input.send_keys(title)
    time.sleep(1)

    # Inserisci il contenuto (convertito in HTML)
    html_content = markdown2.markdown(markdown_content)
    js_script = f"""
    document.querySelector('[data-testid="post-body-editor"] .notranslate').innerHTML = `{html_content}`;
    """
    driver.execute_script(js_script)
    time.sleep(1)

    # Salva come bozza
    if save_as_draft:
        save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
        save_btn.click()
        time.sleep(2)
