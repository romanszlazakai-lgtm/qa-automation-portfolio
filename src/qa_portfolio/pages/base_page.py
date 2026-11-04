"""Common parts shared by every SauceDemo page after login."""

from playwright.sync_api import Locator, Page


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def title(self) -> Locator:
        return self.page.locator('[data-test="title"]')

    @property
    def cart_badge(self) -> Locator:
        return self.page.locator('[data-test="shopping-cart-badge"]')

    def cart_count(self) -> int:
        """Number shown on the cart icon. The badge is absent when the cart is empty."""
        if self.cart_badge.count() == 0:
            return 0
        return int(self.cart_badge.inner_text())

    def open_cart(self) -> None:
        self.page.locator('[data-test="shopping-cart-link"]').click()
        self.page.wait_for_url("**/cart.html")

    def logout(self) -> None:
        self.page.get_by_role("button", name="Open Menu").click()
        self.page.locator('[data-test="logout-sidebar-link"]').click()
