from selenium.webdriver import ChromeOptions
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import sys
import platform

sys.stdout.reconfigure(encoding='utf-8')

"""
Headless Chrome utilities to drive supervive.op.gg interactions.
Creates a minimal wrapper used to press "Fetch New Matches" for a player.
"""

class HeadlessChrome:
    """
    Creating an instance initializes a headless Chrome WebDriver.
    Selects the chromedriver binary based on host OS.
    """

    def __init__(self) -> None:
        """
        Configure Chrome in headless mode and start a WebDriver session.
        """
        options = ChromeOptions()
        #options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-extensions")
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
            "profile.block_third_party_cookies": True
        }
        os = platform.system()

        match os:
            case "Windows":
              CHROME_DRIVER=r"./webdrivers/windows/chromedriver-win64/chromedriver.exe"
            case "Linux":
              CHROME_DRIVER=r"./webdrivers/linux/chromedriver-linux64/chromedriver"

        self.driver = Chrome(
            service=ChromeService(CHROME_DRIVER),
            options=options,
        )
        self.driver.set_window_size(1200,720)
        self.driver.minimize_window()

    def fetch_new_matches(self, user_id):
        """
        Open a player's OPGG page and click "Fetch New Matches".
        @param user_id - URL-escaped slug after steam- (e.g., Name%23Tag).
        @return 1 on success (Refresh appears), 0 on failure/timeout.
        """
        wait = WebDriverWait(self.driver, 10)
        try:
            self.driver.get(rf"https://supervive.op.gg/players/steam-{user_id}")
        except:
            return 0
        try:
            #print(self.driver.page_source, flush=True)
            fetch_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[contains(text(), "Fetch New Matches")]',
                    )
                )
            )
            fetch_btn.click()

            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[contains(text(), "Refresh")]')
                    )
                )
                return 1
            except TimeoutException:
                print(TimeoutException)
                return 0
        except TimeoutException:
            print(TimeoutException)
            return 0


# Usage:
"""HC = HeadlessChrome()
result = HC.fetch_new_matches(r"roughly%2044%20ducks%2344")
print(result)"""

