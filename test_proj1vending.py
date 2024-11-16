#test_proj1vending.py

#By Alyousef Soliman 100883692
#This program is strictly my own work. Any material
#beyond course learning materials that is taken from
#the Web or other sources is properly cited, giving
#credit to the original author(s).

import pytest
from proj1vending_STUDENT import VendingMachine, WaitingState, AddCoinsState, DeliverProductState, CountChangeState

@pytest.fixture
def vending_machine():
    """
    Fixture to create a fresh vending machine instance for testing.
    Returns:
        VendingMachine: A new vending machine instance.
    """
    vending = VendingMachine()
    vending.add_state(WaitingState())
    vending.add_state(AddCoinsState())
    vending.add_state(DeliverProductState())
    vending.add_state(CountChangeState())
    vending.go_to_state('waiting')
    return vending

def test_initial_state(vending_machine):
    """
    Test that the vending machine initializes correctly.
    """
    assert vending_machine.state.name == 'waiting'
    assert vending_machine.amount == 0
    assert vending_machine.change_due == 0

def test_add_coin(vending_machine):
    """
    Test adding coins to the vending machine.
    """
    vending_machine.event = "25 cents"
    vending_machine.update()
    assert vending_machine.amount == 25
    assert vending_machine.state.name == 'add_coins'

    vending_machine.event = "1 dollar"
    vending_machine.update()
    assert vending_machine.amount == 125  # 25 + 100
    assert vending_machine.state.name == 'add_coins'

def test_product_selection(vending_machine):
    """
    Test selecting a product with sufficient funds.
    """
    vending_machine.event = "2 dollars"
    vending_machine.update()
    assert vending_machine.amount == 200

    vending_machine.event = "chips"  # Chips cost 100
    vending_machine.update()
    assert vending_machine.state.name == 'deliver_product'
    assert vending_machine.change_due == 100  # 200 - 100

def test_return_coins(vending_machine):
    """
    Test returning coins when no product is selected.
    """
    vending_machine.event = "1 dollar"
    vending_machine.update()
    assert vending_machine.amount == 100

    vending_machine.event = "RETURN"
    vending_machine.update()
    assert vending_machine.change_due == 100
    assert vending_machine.amount == 0
    assert vending_machine.state.name == 'count_change'

def test_change_return(vending_machine):
    """
    Test returning change after a product purchase.
    """
    vending_machine.event = "2 dollars"
    vending_machine.update()
    assert vending_machine.amount == 200

    vending_machine.event = "soda"  # Soda costs 120
    vending_machine.update()
    assert vending_machine.change_due == 80  # 200 - 120
    assert vending_machine.state.name == 'count_change'

    vending_machine.update()
    assert vending_machine.change_due == 0
    assert vending_machine.state.name == 'waiting'

def test_insufficient_funds(vending_machine):
    """
    Test that the machine does not dispense a product with insufficient funds.
    """
    vending_machine.event = "5 cents"
    vending_machine.update()
    assert vending_machine.amount == 5

    vending_machine.event = "chocolate"  # Chocolate costs 150
    vending_machine.update()
    assert vending_machine.state.name == 'add_coins'
    assert vending_machine.amount == 5  # No deduction as funds are insufficient
