from Model.Code.src.agents.User import User
import logging


class KeepRentingUser(User):
    """ User of the network that keeps renting

    Args:
        User (class): Base class for a user in the model.
    """

    def __init__(self, unique_id, model, user_size):
        """Initializes a KeepRentingUser agent.

        Args:
            unique_id (int): Unique identifier of the agent.
            model (Model): Model in which the agent acts.
            user_size (float): Amount of VTHO that the user uses each day.
        """
        super().__init__(unique_id, model, user_size)

        logging.debug(f"Initialized a KEEP RENTING user with ID {unique_id}")

    def decide_to_buy(self, VTHO_LOB, VET_LOB):
        """Decides whether or not it is time to buy.

        Args:
            VTHO_LOB (List): LOB of the VTHO/USDT pair.
            VET_LOB (List): LOB of the VET/USDT pair.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        return False

    def OG_decide_to_buy(self):
        """Signals whether or not it is time to buy.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        return False
