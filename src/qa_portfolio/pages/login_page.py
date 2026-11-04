from playwright.sync_api import Locator, Page


class LoginPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.username = page.locator('[data-test="username"]')
        self.password = page.locator('[data-test="password"]')
        self.login_button = page.locator('[data-test="login-button"]')
        self.error: Locator = page.locator('[data-test="error"]')

    def open(self) -> "LoginPage":
        self.page.goto("/")
        return self

    def login(self, username: str, password: str) -> None:
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()
