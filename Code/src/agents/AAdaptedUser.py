from Model.Code.src.agents.User import User
import logging
import random
import numpy as np


class AAdaptedUser(User):
    """ User of the network that uses the A-ADAPTED algorithm to determine when to buy VET.

    Args:
        User (class): Base class for a user in the model.
    """

    def __init__(self, unique_id, model, user_size):
        """Initializes an AAdaptedUser agent.

        Args:
            unique_id (int): Unique identifier of the agent.
            model (Model): Model in which the agent acts.
            user_size (float): Amount of VTHO that the user uses each day.
        """

        # Initialize the parent User class
        super().__init__(unique_id, model, user_size)

        # Initialize y and the fluctuation ratios
        self.y = 1
        # self.alphas = [1, ]
        # self.alpha_weights = [0.9**i for i in range(99, -1, -1)]
        self.max_a = 1

        # Generate initial LOB's for VET and VTHO
        _init_VTHO_LOB = self.model.economy.LOB_VTHO.iloc[self.random.randint(
            0, 99), :]
        _init_VET_LOB = self.model.economy.LOB_VET.iloc[self.random.randint(
            0, 99), :]

        # Initialize the buy-to-rent array
        _initial_buy_cost = self.estimate_buy_cost(_init_VET_LOB)
        _initial_rent_cost = self.estimate_rent_cost(_init_VTHO_LOB)
        _initial_price_to_rent = _initial_buy_cost / _initial_rent_cost
        self.price_to_rents = [_initial_price_to_rent, ]

        logging.debug(f"Initialized a STRATEGY-A user with ID {unique_id}")

    def update_y_value(self):
        """Updates the y value based on the algorithm.
        """

        # Get current buy to rent ratio
        _price_to_rent = self.price_to_rents[-1]

        # Calculate the weighted mean fluctuation ratio
        # _a_length = len(self.alphas) if len(
        #     self.alphas) < 100 else 100  # effect is negligable after 100
        # _mean_alpha = np.average(
        #     self.alphas[-_a_length:], weights=self.alpha_weights[-_a_length:])
        # self.weighted_a = _mean_alpha

        # Keep adding mean fluctuation ratio to numerator
        _n = 1 + (_price_to_rent - (_price_to_rent % self.max_a))
        if _n <= _price_to_rent:
            _numerator = _n
        else:
            _numerator = _n - self.max_a

        # _numerator = 1
        # while (_numerator) <= _price_to_rent - self.max_a:
        #     _numerator += self.max_a

        # Update y
        _y = _numerator / _price_to_rent
        if _y < 0:
            self.y = 0
        elif _y > 1:
            self.y = 1
        else:
            self.y = _y

    def OG_decide_to_buy(self):
        """Decides whether or not it is time to buy in the OG setting.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        # Estimate the cost of renting and buying today
        _estimated_cost_of_buying = self.VET_needed * self.model.economy.VET_price
        _estimated_cost_of_renting = self.user_size * self.model.economy.VTHO_price

        # Buy when
        return (self.total_FIAT_spent_rent + _estimated_cost_of_renting) >= self.y * _estimated_cost_of_buying

    def decide_to_buy(self, VTHO_LOB, VET_LOB):
        """Decides whether or not it is time to buy.

        Args:
            VTHO_LOB (List): LOB of the VTHO/USDT pair.
            VET_LOB (List): LOB of the VET/USDT pair.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        # Estimate the cost of renting and buying based on the LOB's
        _estimated_cost_of_renting = self.estimate_rent_cost(VTHO_LOB)
        _estimated_cost_of_buying = self.estimate_buy_cost(VET_LOB)

        # Update the user's buy-to-rent ratio
        self.buy_to_rent = _estimated_cost_of_buying / _estimated_cost_of_renting

        # Update the price-to-rent array
        self.price_to_rents.append(self.buy_to_rent)

        # Determine the fluctuation ratio based on this and the previous day
        if self.price_to_rents[-1] >= self.price_to_rents[-2]:
            _alpha = self.price_to_rents[-1] / self.price_to_rents[-2]
        else:
            _alpha = self.price_to_rents[-2] / self.price_to_rents[-1]

        # Update the maximum fluctuation ratio if needed
        if _alpha > self.max_a:
            self.max_a = _alpha

        # Update the current y
        self.update_y_value()

        # Buy when
        return (self.total_FIAT_spent_rent + _estimated_cost_of_renting) >= self.y * _estimated_cost_of_buying
