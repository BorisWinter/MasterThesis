from mesa import Agent
# from random import randint
import logging


class User(Agent):
    """An agent that acts as a user of the network.

    Args:
        Agent (class): Base class for Mesa agents.
    """

    def __init__(self, unique_id, model, user_size):
        """Initializes a User!

        Args:
            unique_id (int): Unique identifier of the agent.
            model (Model): Model of the VeChain network in which the agent acts.
            user_size (float): Amount of VTHO that the User uses each day.
        """

        # Initialize an agent
        super().__init__(unique_id, model)

        self.active = True
        self.state = "RENTING"

        self.rent_until_spent = 0
        self.bought_at_day = 0
        self.CR = 0

        self.VET = 0
        self.VTHO = 0
        self.total_VTHO_bought = 0
        self.total_VET_bought = 0

        self.total_FIAT_spent_rent = 0
        self.total_FIAT_spent_buying = 0

        self.max_days = self.set_max_days()
        self.optimal = 0
        self.alphas = []
        self.weighted_a = 1
        self.max_a = 1
        self.y = 0
        self.b = 0

        self.VTHO_LOB_ID = []
        self.VET_LOB_ID = []

        # Determine the VET needed to generate required daily VTHO
        self.user_size = user_size
        self.VET_needed = (self.user_size) / self.model.VTHO_generation_rate

        # Metrics for eventual CR calculation
        self.is_first_step = True
        self.initial_buy_price = 0
        self.potential_FIAT_spent_rent = 0

    def step(self):
        """Step function of the user. Defines all the actions that the user makes in one step/day.
        """

        if self.active:

            if self.model.experiment_setting in ["OG-SKI-RENTAL"]:
                # Different functions for the OG problem, for speed
                if self.state == "BOUGHT":
                    self.OG_bought_step()
                elif self.state == "RENTING":
                    self.OG_renting_step()
            else:
                if self.state == "BOUGHT":
                    self.bought_step()
                elif self.state == "RENTING":
                    self.renting_step()

            # Handle usage trend?
            self.handle_usage_trend()

            # Check whether the user should become inactive after this day
            self.handle_max_days_reached()

    def handle_usage_trend(self):
        """Changes the user size based on any usage trend.
        """

        if self.model.usage_trend in ["UP-SMALL", "UP-LARGE"]:
            # Increase total daily usage from trend
            self.user_size += self.model.usage_trend_step_size
            self.VET_needed = (self.user_size) / \
                self.model.VTHO_generation_rate

        elif self.model.usage_trend in ["DOWN-SMALL", "DOWN-LARGE"]:
            # Decrease total daily usage from trend
            self.user_size -= self.model.usage_trend_step_size
            self.VET_needed = (self.user_size) / \
                self.model.VTHO_generation_rate

    def handle_max_days_reached(self):
        """Checks whether the user has reached their maximum number of days as specified by the adversary. Sets the user to inactive if they have.
        """

        if self.model.schedule.steps >= self.max_days:
            # Determine the achieved CR
            self.set_CR()

            # Set user to inactive
            self.active = False

            logging.warning(
                f"User {self.unique_id} [{self.state}] has reached their max. number of active days on day {self.model.schedule.steps}.")

    def set_max_days(self):
        """Plays the adversary. Randomly chooses a last day for the user from a uniform distribution with range [1,simulation_length]
        """
        return self.random.randint(1, self.model.simulation_length)
        # return 3649

    def set_CR(self):
        """Sets the competitive ratio (CR) of the user for the day when the function is called.
        """

        # Small users need to be compared to an optimal small user
        # if self.user_size == self.model.small_user_size:
        optimal = min(self.initial_buy_price,
                      self.potential_FIAT_spent_rent)
        self.CR = (self.total_FIAT_spent_rent +
                   self.total_FIAT_spent_buying) / optimal
        self.optimal = optimal
        logging.warning(
            f"User {self.unique_id} became inactive and achieved CR: {self.CR}")

    def OG_bought_step(self):
        """Handles the actions of users in the OG settings that have already bought VET.
        """
        # Log the would-be rent cost
        self.potential_FIAT_spent_rent += self.model.economy.VTHO_price * self.user_size

        # Make the transactions (redundant for the OG problem)
        self.VTHO += self.user_size
        self.VTHO -= self.user_size

    def OG_renting_step(self):
        """Handles the actions of the users in the OG settings that are still renting.
        """

        if self.is_first_step:
            # Determine the initial buy price (used for calculating the optimal performance and CR)
            self.initial_buy_price = self.VET_needed * self.model.economy.VET_price
            self.is_first_step = False

        # Check whether to buy at this point in time
        if self.OG_decide_to_buy():

            # Log the would-be rent cost
            self.potential_FIAT_spent_rent += self.model.economy.VTHO_price * self.user_size

            # Buy the required VET
            self.OG_buy_VET()

            # Log the day of buying
            self.bought_at_day = self.model.schedule.steps

        # This else is controversial since you could say that the buyer needs to wait a full day before benefitting from the bought VET.
        # However, it is only a small assumption and this maps better to the original Ski Rental Problem.
        else:
            self.OG_buy_VTHO()

        # Make the transactions (redundant for the OG problem)
        self.VTHO += self.user_size
        self.VTHO -= self.user_size

    def bought_step(self):
        """Handles the actions of users that have already bought VET.
        """
        # Add the generated VTHO
        self.VTHO += self.user_size

        # Log the would-be rent costs for the CR calculation
        _VTHO_LOB = self.model.economy.LOB_VTHO.iloc[self.random.randint(
            0, 99), :]
        self.potential_FIAT_spent_rent += self.estimate_rent_cost(_VTHO_LOB)

        # Make the daily transactions
        self.make_transactions()

    def renting_step(self):
        """Handles the actions of the users that are still renting.
        """

        # Generate random VET and VTHO LOB's to act as the current state of the exchange
        rando_VET = self.random.randint(0, 99)
        rando_VTHO = self.random.randint(0, 99)
        _VET_LOB = self.model.economy.LOB_VET.iloc[rando_VET, :]
        _VTHO_LOB = self.model.economy.LOB_VTHO.iloc[rando_VTHO, :]

        logging.warning(f"User selected VTHO LOB {rando_VTHO}")
        self.VTHO_LOB_ID = rando_VTHO
        self.VET_LOB_ID = rando_VET

        if self.is_first_step:
            # Determine the initial buy price (used for calculating the optimal performance and CR)
            self.initial_buy_price = self.estimate_buy_cost(_VET_LOB)
            self.is_first_step = False

        # Check whether to buy at this point in time
        if self.decide_to_buy(_VTHO_LOB, _VET_LOB):

            # Log the would-be rent costs for the CR calculation
            self.potential_FIAT_spent_rent += self.estimate_rent_cost(
                _VTHO_LOB)

            # Buy the required amount of VET
            self.buy_VET(_VET_LOB)

            # Log the day of buying
            self.bought_at_day = self.model.schedule.steps

        # This else is controversial since you could say that the buyer needs to wait a full day before benefitting from the bought VET.
        # However, it is only a small assumption and this maps better to the original Ski Rental Problem.
        else:
            self.buy_VTHO(_VTHO_LOB)

        # Add the generated/bought VTHO
        self.VTHO += self.user_size

        # Make the daily transactions
        self.make_transactions()

    def make_transactions(self):
        """Makes the user's transactions on the network.
        """

        # Remove the spent VTHO from the user's wallet
        self.VTHO -= self.user_size

        # Destroy 70% of the spent VTHO
        self.model.economy.decrease_circulating_VTHO(0.7 * self.user_size)

        logging.debug(
            f"User {self.unique_id} [{self.state}] made their transactions.")

    def estimate_rent_cost(self, LOB):
        """Estimates the cost of renting for this day based on the given LOB

        Args:
            LOB (List): Limit order book of the VTHO/USDT pair.

        Returns:
            float: The estimated cost in FIAT of renting on this day.
        """

        # Select only the asks
        _LOB_orders = LOB[50:]

        # Calculate how much to buy/sell and how many ticks it would move the price
        _relative_order_size = self.user_size / self.model.economy.liquidity_VTHO
        _tick_change = _LOB_orders.cumsum().searchsorted(_relative_order_size)

        # Calculate how much to buy from the last of the i orders
        _amount_from_last_order = self.user_size - \
            sum([_LOB_orders[i]*self.model.economy.liquidity_VTHO for i in range(_tick_change)])

        # Calulate how much you would pay for the amount that you need from the last ask
        _price_paid_last_order = _amount_from_last_order * \
            (self.model.economy.VTHO_price +
             (_tick_change * self.model.economy.VTHO_LOB_tick_size))

        # Calculate total price that you would pay if you rent today
        _estimated_cost_of_renting = sum([_LOB_orders[i]*self.model.economy.liquidity_VTHO*(self.model.economy.VTHO_price + (
            i * self.model.economy.VTHO_LOB_tick_size)) for i in range(_tick_change)]) + _price_paid_last_order

        return _estimated_cost_of_renting

    def estimate_buy_cost(self, LOB):
        """Estimates the cost of buying on this day based on the given LOB

        Args:
            LOB (List): Limit order book of the VET/USDT pair.

        Returns:
            float: The estimated cost in FIAT of buying today.
        """

        # Select only the asks
        _LOB_orders = LOB[50:]

        # Calculate how much to buy/sell and the effect on price
        _relative_order_size = self.VET_needed / self.model.economy.liquidity_VET
        _tick_change = _LOB_orders.cumsum().searchsorted(_relative_order_size)

        # Calculate how much to buy from the last of the i orders
        _amount_from_last_order = self.VET_needed - \
            sum([_LOB_orders[i]*self.model.economy.liquidity_VET for i in range(_tick_change)])

        # Calulate how much you would pay for the amount that you need from the last ask
        _price_paid_last_order = _amount_from_last_order * \
            (self.model.economy.VET_price +
             (_tick_change * self.model.economy.VET_LOB_tick_size))

        # Calculate total price that you would pay if you buy today
        _estimated_cost_of_buying = sum([_LOB_orders[i]*self.model.economy.liquidity_VET*(self.model.economy.VET_price + (
            i * self.model.economy.VET_LOB_tick_size)) for i in range(_tick_change)]) + _price_paid_last_order

        return _estimated_cost_of_buying

    def OG_buy_VET(self):
        """Buys VET in the OG setting and updates the state of the user accordingly.
        """

        # Update the user's state
        self.state = "BOUGHT"

        # Buy the required VET
        _price_paid = self.model.economy.VET_price * self.VET_needed

        # Update the user's buy expenses
        self.update_buy_expenses(self.VET_needed, _price_paid)

    def OG_buy_VTHO(self):
        """Buys VTHO in the OG setting and updates the state of the user accordingly.
        """

        # Buy the required VET
        _price_paid = self.model.economy.VTHO_price * self.user_size

        # Update the user's buy expenses
        self.update_rent_expenses(self.user_size, _price_paid)

    def buy_VET(self, LOB):
        """Buys VET and updates the state of the user accordingly.
        """

        # Update the user's state
        self.state = "BOUGHT"

        # Buy the required VET
        _price_paid = self.model.economy.VET_order(
            self.VET_needed, LOB, order_type="BUY")
        self.VET += self.VET_needed

        # Update the user's buy expenses
        self.update_buy_expenses(self.VET_needed, _price_paid)

        # Subtract the VET from the circulating supply
        self.model.economy.decrease_circulating_VET(self.VET_needed)

        logging.warning(
            f"User {self.unique_id} has decided to buy VET after spending {self.total_FIAT_spent_rent} on rent!")
        logging.debug(
            f"User {self.unique_id} bought {self.VET_needed} VET for a FIAT price of {_price_paid}")

    def buy_VTHO(self, LOB):
        """Buys VTHO and updates the state of the user accordingly.
        """

        # Buy the required VTHO
        _price_paid = self.model.economy.VTHO_order(
            self.user_size, LOB, order_type="BUY")

        # Update the rent expenses
        self.update_rent_expenses(self.user_size, _price_paid)

        logging.debug(
            f"User {self.unique_id} bought {self.user_size} VTHO for a FIAT price of {_price_paid}")

    def update_rent_expenses(self, VTHO_bought, FIAT_expense):
        """Updates the user's expenses from renting.

        Args:
            VTHO_bought (float): The amount of VTHO that was bought.
            FIAT_expense (float): The amount of FIAT money spent on VTHO.
        """

        self.total_VTHO_bought += VTHO_bought
        self.total_FIAT_spent_rent += FIAT_expense
        self.potential_FIAT_spent_rent += FIAT_expense

    def update_buy_expenses(self, VET_bought, FIAT_expense):
        """Updates the user's expenses from buying.

        Args:
            VET_bought (float): The amount of VET that was bought.
            FIAT_expense (float): The amount of FIAT money spent on VET.
        """
        self.total_VET_bought += VET_bought
        self.total_FIAT_spent_buying += FIAT_expense
