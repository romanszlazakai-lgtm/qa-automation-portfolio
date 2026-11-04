"""Checkout covers three screens: customer info, overview and confirmation."""

from decimal import Decimal

from playwright.sync_api import Page

from qa_portfolio.pages.base_page import BasePage
from qa_portfolio.pages.money import parse_price


class CheckoutPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.first_name = page.locator('[data-test="firstName"]')
        self.last_name = page.locator('[data-test="lastName"]')
        self.postal_code = page.locator('[data-test="postalCode"]')
        self.error = page.locator('[data-test="error"]')
        self.complete_header = page.locator('[data-test="complete-header"]')

    # Step one: customer information

    def fill_customer_info(self, first_name: str, last_name: str, postal_code: str) -> None:
        self.first_name.fill(first_name)
        self.last_name.fill(last_name)
        self.postal_code.fill(postal_code)

    def submit_customer_info(self) -> None:
        """Click Continue without waiting. Use for validation tests that stay on step one."""
        self.page.locator('[data-test="continue"]').click()

    def continue_to_overview(self) -> None:
        self.submit_customer_info()
        self.page.locator('[data-test="finish"]').wait_for()

    # Step two: overview

    def line_item_prices(self) -> list[Decimal]:
        texts = self.page.locator('[data-test="inventory-item-price"]').all_inner_texts()
        return [parse_price(text) for text in texts]

    def subtotal(self) -> Decimal:
        return parse_price(self.page.locator('[data-test="subtotal-label"]').inner_text())

    def tax(self) -> Decimal:
        return parse_price(self.page.locator('[data-test="tax-label"]').inner_text())

    def total(self) -> Decimal:
        return parse_price(self.page.locator('[data-test="total-label"]').inner_text())

    def finish(self) -> None:
        self.page.locator('[data-test="finish"]').click()
        self.complete_header.wait_for()
