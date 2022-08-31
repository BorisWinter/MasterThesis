import matplotlib.pyplot as plt
from Model.Code.src.agents.User import User
from scipy.stats import rv_discrete, rv_continuous
import numpy as np
import logging
from random import randint


class RandomUser(User):
    """ User of the network that randomly chooses a day to buy VET

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

        # Initialize the parent User class
        super().__init__(unique_id, model, user_size)

        # Determine when to buy by selecting a random day in the range [0,simulation_length]
        self.day_of_buying = randint(0, self.model.simulation_length)

        logging.debug(f"Initialized a RANDOM user with ID {unique_id}")

    def decide_to_buy(self, VTHO_LOB, VET_LOB):
        """Decides whether or not it is time to buy.

        Args:
            VTHO_LOB (List): LOB of the VTHO/USDT pair.
            VET_LOB (List): LOB of the VET/USDT pair.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        if self.model.schedule.steps == self.day_of_buying:
            return True
        else:
            return False

    def OG_decide_to_buy(self):
        """Signals whether or not it is time to buy.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        if self.model.schedule.steps == self.day_of_buying:
            return True
        else:
            return False
