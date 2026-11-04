from playwright.sync_api import Page

from qa_portfolio.pages.base_page import BasePage


class CartPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.locator('[data-test="inventory-item"]')

    def item_names(self) -> list[str]:
        return self.page.locator('[data-test="inventory-item-name"]').all_inner_texts()

    def remove(self, name: str) -> None:
        self.items.filter(has_text=name).get_by_role("button", name="Remove").click()

    def checkout(self) -> None:
        self.page.locator('[data-test="checkout"]').click()
        self.page.wait_for_url("**/checkout-step-one.html")
