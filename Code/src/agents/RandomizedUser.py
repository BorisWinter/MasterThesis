from Model.Code.src.agents.User import User
from scipy.stats import rv_continuous
import numpy as np
import logging


class RandomizedUser(User):
    """ User of the network that uses the randomized algorithm to determine when to buy VET.

    Args:
        User (class): Base class for a user in the model.
    """

    def __init__(self, unique_id, model, user_size):
        """Initializes a RandomizedUser agent.

        Args:
            unique_id (int): Unique identifier of the agent.
            model (Model): Model in which the agent acts.
            user_size (float): Amount of VTHO that the user uses each day.
        """

        # Initialize a User class
        super().__init__(unique_id, model, user_size)

        # Determine when to buy based on the algorithm pdf
        self.pdf = self.generate_pdf()
        self.rent_until_spent_norm = self.pdf.rvs(size=1)[0]

        logging.debug(f"Initialized a RANDOMIZED user with ID {unique_id}")

    def generate_pdf(self):
        """Generates the pdf that is used to choose the time of buying.

        Returns:
            rv_continuous.pdf: The pdf that is returned.
        """
        class my_pdf(rv_continuous):
            def _pdf(self, x):
                res = (np.e ** x) / (np.e - 1)
                return res

        pdf = my_pdf(a=0, b=1, name='pdf')
        return pdf

    def OG_decide_to_buy(self):
        """Decides whether or not it is time to buy in the OG setting.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        # Estimate the cost of renting
        _estimated_cost_of_buying = self.VET_needed * self.model.economy.VET_price

        # Determine new FIAT value of max. rent
        self.rent_until_spent = self.rent_until_spent_norm * _estimated_cost_of_buying

        # Buy when
        return self.total_FIAT_spent_rent > (self.rent_until_spent - (self.user_size * self.model.economy.VTHO_price))

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

        # Determine new FIAT value of max. rent
        self.rent_until_spent = self.rent_until_spent_norm * _estimated_cost_of_buying

        # Buy when
        return self.total_FIAT_spent_rent > (self.rent_until_spent - _estimated_cost_of_renting)
