#proj1vending_STUDENT.py

#By Alyousef Soliman 100883692
#This program is strictly my own work. Any material
#beyond course learning materials that is taken from
#the Web or other sources is properly cited, giving
#credit to the original author(s).

import PySimpleGUI as sg
from time import sleep

# Hardware interface module
hardware_present = False
try:
    from gpiozero import Button, Servo
    hardware_present = True
    key1 = Button(5)  # GPIO pin 5 for the physical return button
    servo = Servo(17)  # GPIO pin 17 for the servo motor (dispenses products)
except (ImportError, RuntimeError):
    hardware_present = False

# Setting this constant to True enables the logging function
# Set it to False for normal operation
TESTING = True

def log(s):
    """
    Logs a debug message if TESTING is enabled.
    Args:
        s (str): The message to log.
    """
    if TESTING:
        print(s)

class VendingMachine:
    """
    Represents the vending machine state machine.
    Contains products, coins, and manages state transitions.
    """

    PRODUCTS = {
        "coke": ("coke", 150),
        "chocolate": ("chocolate", 150),
        "chips": ("chips", 100),
        "cookie": ("cookie", 70),
        "soda": ("soda", 120),
        "water": ("water", 80)
    }

    COINS = {
        "5 cents": ("5 cents", 5),
        "10 cents": ("10 cents", 10),
        "25 cents": ("25 cents", 25),
        "1 dollar": ("1 dollar", 100),
        "2 dollars": ("2 dollars", 200),
    }

    def __init__(self):
        """
        Initializes the vending machine, setting up states, events, and balances.
        """
        self.state = None
        self.states = {}
        self.event = ""
        self.amount = 0
        self.change_due = 0
        self.coin_values = sorted([coin[1] for coin in self.COINS.values()], reverse=True)
        log(str(self.coin_values))

    def add_state(self, state):
        """
        Adds a new state to the state machine.
        Args:
            state (State): The state to add.
        """
        self.states[state.name] = state

    def go_to_state(self, state_name):
        """
        Transitions to the specified state.
        Args:
            state_name (str): The name of the target state.
        """
        if self.state:
            log(f'Exiting {self.state.name}')
            self.state.on_exit(self)
        self.state = self.states[state_name]
        log(f'Entering {self.state.name}')
        self.state.on_entry(self)

    def update(self):
        """
        Updates the current state based on the latest event.
        """
        if self.state:
            self.state.update(self)

    def add_coin(self, coin):
        """
        Adds the value of the coin to the total balance.
        Args:
            coin (str): The key representing the coin.
        """
        self.amount += self.COINS[coin][1]

    def button_action(self):
        """
        Callback function for Raspberry Pi button to handle the return action.
        """
        self.event = 'RETURN'
        self.update()

class State:
    """
    Superclass for all vending machine states.
    Contains default methods to be overridden by subclasses.
    """
    _NAME = ""

    def __init__(self):
        """Initializes the state."""
        pass

    @property
    def name(self):
        """Returns the name of the state."""
        return self._NAME

    def on_entry(self, machine):
        """Defines actions to perform when entering the state."""
        pass

    def on_exit(self, machine):
        """Defines actions to perform when exiting the state."""
        pass

    def update(self, machine):
        """Handles updates within the state."""
        pass

class WaitingState(State):
    """
    Waiting state: The initial state, awaiting the first coin.
    """
    _NAME = "waiting"

    def update(self, machine):
        """
        Handles coin insertion to transition to the AddCoinsState.
        """
        if machine.event in machine.COINS:
            machine.add_coin(machine.event)
            machine.go_to_state('add_coins')

class AddCoinsState(State):
    """
    AddCoinsState: Accepts additional coins and handles product selection.
    """
    _NAME = "add_coins"

    def update(self, machine):
        """
        Processes coins or product selection and manages transitions.
        """
        if machine.event == "RETURN":
            machine.change_due = machine.amount
            machine.amount = 0
            machine.go_to_state('count_change')
        elif machine.event in machine.COINS:
            machine.add_coin(machine.event)
        elif machine.event in machine.PRODUCTS:
            if machine.amount >= machine.PRODUCTS[machine.event][1]:
                machine.go_to_state('deliver_product')

class DeliverProductState(State):
    """
    DeliverProductState: Dispenses the selected product.
    """
    _NAME = "deliver_product"

    def on_entry(self, machine):
        """
        Handles the dispensing of the product and manages state transitions.
        """
        machine.change_due = machine.amount - machine.PRODUCTS[machine.event][1]
        machine.amount = 0
        print("Buzz... Whir... Click...", machine.PRODUCTS[machine.event][0])

        if hardware_present:
            print("Activating servo to dispense the product...")
            servo.min()
            sleep(1)
            servo.mid()
            sleep(1)

        if machine.change_due > 0:
            machine.go_to_state('count_change')
        else:
            machine.go_to_state('waiting')

class CountChangeState(State):
    """
    CountChangeState: Returns any remaining change to the user.
    """
    _NAME = "count_change"

    def on_entry(self, machine):
        """
        Logs and prepares to return change.
        """
        print(f"Change due: $%0.2f" % (machine.change_due / 100))
        log(f"Returning change: {machine.change_due}")

    def update(self, machine):
        """
        Iteratively returns change in coins.
        """
        for coin in machine.coin_values:
            while machine.change_due >= coin:
                print(f"Returning {coin} cents")
                machine.change_due -= coin
        if machine.change_due == 0:
            machine.go_to_state('waiting')

# MAIN PROGRAM
if __name__ == "__main__":
    """
    Main program to set up the vending machine GUI and start the event loop.
    """
    sg.theme('BluePurple')

    coin_col = [[sg.Text("ENTER COINS", font=("Helvetica", 24))]]
    for item in VendingMachine.COINS:
        coin_col.append([sg.Button(item, font=("Helvetica", 18))])

    select_col = [[sg.Text("SELECT ITEM", font=("Helvetica", 24))]]
    for item in VendingMachine.PRODUCTS:
        select_col.append([sg.Button(item, font=("Helvetica", 18))])

    layout = [
        [sg.Column(coin_col, vertical_alignment="TOP"), sg.VSeparator(), sg.Column(select_col, vertical_alignment="TOP")],
        [sg.Button("RETURN", font=("Helvetica", 12))]
    ]
    window = sg.Window('Vending Machine', layout)

    vending = VendingMachine()
    vending.add_state(WaitingState())
    vending.add_state(AddCoinsState())
    vending.add_state(DeliverProductState())
    vending.add_state(CountChangeState())
    vending.go_to_state('waiting')

    if hardware_present:
        key1.when_pressed = vending.button_action

    while True:
        event, values = window.read(timeout=10)
        if event != '__TIMEOUT__':
            log((event, values))
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        vending.event = event
        vending.update()

    window.close()
    print("Normal exit")
