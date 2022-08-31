from Model.Code.src.agents.User import User
import logging


class DeterministicUser(User):
    """ User of the network that uses the deterministic "break-even" algorithm to determine when to buy VET.

    Args:
        User (class): Base class for a user in the model.
    """

    def __init__(self, unique_id, model, user_size):
        """Initializes a DeterministicUser agent.

        Args:
            unique_id (int): Unique identifier of the agent.
            model (Model): Model in which the agent acts.
            user_size (float): Amount of VTHO that the user uses each day.
        """

        # Initialize a User class
        super().__init__(unique_id, model, user_size)

        logging.debug(f"Initialized a DETERMINISTIC user with ID {unique_id}")

    def decide_to_buy(self, VTHO_LOB, VET_LOB):
        """Decides whether or not it is time to buy.

        Args:
            VTHO_LOB (List): LOB of the VTHO/USDT pair.
            VET_LOB (List): LOB of the VET/USDT pair.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        # Estimate the cost of buying and renting
        _estimated_cost_of_renting = self.estimate_rent_cost(VTHO_LOB)
        _estimated_cost_of_buying = self.estimate_buy_cost(VET_LOB)

        # Update the user's buy-to-rent ratio
        self.buy_to_rent = _estimated_cost_of_buying / _estimated_cost_of_renting

        # Buy when FIAT spent on rent >= buying price for all VET needed to generate enough VTHO
        return self.total_FIAT_spent_rent >= _estimated_cost_of_buying

    def OG_decide_to_buy(self):
        """Decides whether or not it is time to buy in the OG setting.

        Returns:
            Boolean: TRUE when the user needs to buy. False otherwise.
        """

        # Estimate the cost of buying
        _estimated_cost_of_buying = self.VET_needed * self.model.economy.VET_price

        # Buy when FIAT spent on rent >= buying price for all VET needed to generate enough VTHO
        return self.total_FIAT_spent_rent >= _estimated_cost_of_buying
