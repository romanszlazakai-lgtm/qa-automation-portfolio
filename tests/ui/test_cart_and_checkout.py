from decimal import Decimal

import pytest
from playwright.sync_api import expect

from qa_portfolio.pages import CartPage, CheckoutPage, InventoryPage

BACKPACK = "Sauce Labs Backpack"
BIKE_LIGHT = "Sauce Labs Bike Light"
ONESIE = "Sauce Labs Onesie"


def test_adding_items_updates_cart_badge(inventory: InventoryPage) -> None:
    assert inventory.cart_count() == 0

    inventory.add_to_cart(BACKPACK, BIKE_LIGHT)

    expect(inventory.cart_badge).to_have_text("2")


def test_cart_lists_selected_items(inventory: InventoryPage) -> None:
    inventory.add_to_cart(BACKPACK, ONESIE)
    inventory.open_cart()

    cart = CartPage(inventory.page)
    assert sorted(cart.item_names()) == sorted([BACKPACK, ONESIE])


def test_removing_item_from_cart(inventory: InventoryPage) -> None:
    inventory.add_to_cart(BACKPACK, ONESIE)
    inventory.open_cart()
    cart = CartPage(inventory.page)

    cart.remove(ONESIE)

    assert cart.item_names() == [BACKPACK]
    expect(cart.cart_badge).to_have_text("1")


@pytest.mark.parametrize(
    ("option", "key", "reverse"),
    [
        pytest.param("lohi", "price", False, id="price-low-to-high"),
        pytest.param("hilo", "price", True, id="price-high-to-low"),
        pytest.param("az", "name", False, id="name-a-to-z"),
        pytest.param("za", "name", True, id="name-z-to-a"),
    ],
)
def test_sorting_products(inventory: InventoryPage, option: str, key: str, reverse: bool) -> None:
    inventory.sort_by(option)

    values = inventory.item_prices() if key == "price" else inventory.item_names()
    assert values == sorted(values, reverse=reverse)


@pytest.mark.smoke
def test_checkout_end_to_end(inventory: InventoryPage) -> None:
    expected_prices = [inventory.price_of(BACKPACK), inventory.price_of(BIKE_LIGHT)]
    inventory.add_to_cart(BACKPACK, BIKE_LIGHT)
    inventory.open_cart()
    CartPage(inventory.page).checkout()

    checkout = CheckoutPage(inventory.page)
    checkout.fill_customer_info("Jan", "Kowalski", "00-950")
    checkout.continue_to_overview()

    # The money checks a bank would care about: line items add up and the total adds up.
    assert sorted(checkout.line_item_prices()) == sorted(expected_prices)
    assert checkout.subtotal() == sum(expected_prices, Decimal("0"))
    assert checkout.tax() > 0
    assert checkout.total() == checkout.subtotal() + checkout.tax()

    checkout.finish()

    expect(checkout.complete_header).to_have_text("Thank you for your order!")
    assert checkout.cart_count() == 0


@pytest.mark.parametrize(
    ("first", "last", "postal", "expected_error"),
    [
        pytest.param("", "Kowalski", "00-950", "Error: First Name is required", id="no-first-name"),
        pytest.param("Jan", "", "00-950", "Error: Last Name is required", id="no-last-name"),
        pytest.param("Jan", "Kowalski", "", "Error: Postal Code is required", id="no-postal-code"),
    ],
)
def test_checkout_requires_customer_info(
    inventory: InventoryPage, first: str, last: str, postal: str, expected_error: str
) -> None:
    inventory.add_to_cart(BACKPACK)
    inventory.open_cart()
    CartPage(inventory.page).checkout()
    checkout = CheckoutPage(inventory.page)

    checkout.fill_customer_info(first, last, postal)
    checkout.continue_to_overview()

    expect(checkout.error).to_have_text(expected_error)
