from decimal import Decimal

from playwright.sync_api import Page

from qa_portfolio.pages.base_page import BasePage
from qa_portfolio.pages.money import parse_price

PATH = "/inventory.html"


class InventoryPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.locator('[data-test="inventory-item"]')
        self.sort_select = page.locator('[data-test="product-sort-container"]')

    def _item(self, name: str):
        return self.items.filter(has_text=name)

    def add_to_cart(self, *names: str) -> None:
        for name in names:
            self._item(name).get_by_role("button", name="Add to cart").click()

    def remove_from_cart(self, name: str) -> None:
        self._item(name).get_by_role("button", name="Remove").click()

    def item_names(self) -> list[str]:
        return self.page.locator('[data-test="inventory-item-name"]').all_inner_texts()

    def item_prices(self) -> list[Decimal]:
        texts = self.page.locator('[data-test="inventory-item-price"]').all_inner_texts()
        return [parse_price(text) for text in texts]

    def price_of(self, name: str) -> Decimal:
        return parse_price(
            self._item(name).locator('[data-test="inventory-item-price"]').inner_text()
        )

    def sort_by(self, option_value: str) -> None:
        """option_value is one of: az, za, lohi, hilo."""
        self.sort_select.select_option(option_value)
