from selenium.webdriver import ChromeOptions
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import platform


class HeadlessChrome:
    """creating a class instance initializes webdriver"""

    def __init__(self) -> None:
        options = ChromeOptions()
        options.add_argument("--headless")
        os = platform.system()

        match os:
            case "Windows":
                self.driver = Chrome(
                    service=ChromeService(
                        r"./webdrivers/windows/chromedriver-win64/chromedriver.exe"
                    ),
                    options=options,
                )
            case "Linux":
                self.driver = Chrome(
                    service=ChromeService(
                        r"./webdrivers/linux/chromedriver-linux64/chromedriver"
                    ),
                    options=options,
                )

    def fetch_new_matches(self, user_id):
        """
        returns 1 if success

        returns 0 if too many requests (timeout is about one minute)
        """
        wait = WebDriverWait(self.driver, 10)

        self.driver.get(rf"https://supervive.op.gg/players/steam-{user_id}")
        try:
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
                self.driver.close()
                return 1
            except TimeoutException:
                self.driver.close()
                return 0
        except TimeoutException:
            self.driver.close()
            return 0


# Usage:
"""HC = HeadlessChrome()
result = HC.fetch_new_matches(r"roughly%2044%20ducks%2344")
print(result)
"""
