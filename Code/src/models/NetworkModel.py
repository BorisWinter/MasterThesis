import logging
# from random import randint
from Model.Code.src.agents.DeterministicUser import DeterministicUser
from Model.Code.src.agents.RandomizedUser import RandomizedUser
from Model.Code.src.agents.AAdaptedUser import AAdaptedUser
from Model.Code.src.agents.ATrendUser import ATrendUser
from Model.Code.src.agents.RandomUser import RandomUser
from Model.Code.src.agents.KeepRentingUser import KeepRentingUser
from Model.Code.src.agents.InstantBuyUser import InstantBuyUser
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
import numpy as np


class NetworkModel(Model):
    """Model of the VeChain network.

    Args:
        Model (Mesa model): Base model of the Mesa framework.
    """

    def __init__(self,
                 experiment_setting,
                 economic_model,
                 simulation_length,
                 generation_rate,
                 initial_VTHO_usage,
                 final_VTHO_usage,
                 small_user_size,
                 large_user_size,
                 usage_trend,
                 usage_trend_length,
                 starting_usage_trend_size,
                 user_strategies,
                 main_user_strategy):

        # Basic model settings
        self.running = True  # Necessary for the batchrunner to work.
        self.experiment_setting = experiment_setting
        self.economy = economic_model
        self.simulation_length = simulation_length
        self.current_id = 0

        # VTHO usage settings
        self.initial_VTHO_usage = initial_VTHO_usage
        self.current_VTHO_usage = initial_VTHO_usage
        self.final_VTHO_usage = final_VTHO_usage
        self.usage_trend = usage_trend
        self.current_usage_trend_size = starting_usage_trend_size

        self.steps_per_user_addition = 0
        self.VTHO_generation_rate = generation_rate
        self.daily_VTHO_generation = self.economy.circulating_VET * self.VTHO_generation_rate

        # User settings
        self.user_strategies = user_strategies
        self.main_user_strategy = main_user_strategy
        self.small_user_size = small_user_size
        self.large_user_size = large_user_size

        # Create the schedule
        self.schedule = RandomActivation(self)

        # Initialize the user(s).
        self.initialize_users()
        self.num_initial_users = self.schedule.get_agent_count()

        # Usage trend settings
        self.usage_trend_length = usage_trend_length
        self.usage_trend_step_size = (
            (self.final_VTHO_usage - self.initial_VTHO_usage)/self.simulation_length)/self.num_initial_users

        self.buy_to_rent = (self.economy.VET_price /
                            self.VTHO_generation_rate) / self.economy.VTHO_price

        self.datacollector = DataCollector(
            model_reporters={
                "VET_price": lambda m: m.economy.VET_price,
                "VTHO_price": lambda m: m.economy.VTHO_price,
                "num_active_users": lambda m: m.schedule.get_agent_count(),
                "daily_VTHO_generation": "daily_VTHO_generation",
                "current_VTHO_usage": "current_VTHO_usage",
                "current_usage_trend_size": "current_usage_trend_size",
                "usage_trend_step_size": "usage_trend_step_size",
                "buy_to_rent": "buy_to_rent",
                "adoption_ratio": lambda m: m.calculate_adoption_ratio(),
                "main_user_CR": lambda m: m.schedule.agents[0].CR,
            },
            agent_reporters={
                "active": "active",
                "state": "state",
                "bought_at_day": "bought_at_day",
                "max_days": "max_days",
                "VET": "VET",
                "VTHO": "VTHO",
                "user_size": "user_size",
                "VET_needed": "VET_needed",
                "rent_until_spent": "rent_until_spent",
                "potential_FIAT_spent_rent": "potential_FIAT_spent_rent",
                "VTHO_LOB_ID": "VTHO_LOB_ID",
                "total_FIAT_spent_rent": "total_FIAT_spent_rent",
                "VET_LOB_ID": "VET_LOB_ID",
                "total_FIAT_spent_buying": "total_FIAT_spent_buying",
                "initial_buy_price": "initial_buy_price",
                "b": "b",
                # "mean_a": lambda a: np.mean(a.alphas) if len(a.alphas) < 0 else 0,
                "max_a": "max_a",
                "y": "y",
                "CR": "CR",
                "optimal": "optimal"
            }
        )

        # Collect initial data
        self.datacollector.collect(self)
        self.economy.datacollector.collect(self.economy)

        logging.warning("Initialized the network model.")

    def step(self):
        """Advances the model by one day/step."""

        # if self.schedule.agents[0].active == True:

        # Let the economy know that a day has passed
        self.economy.increase_network_step()

        # Handle today's VTHO generation
        self.economy.increase_circulating_VTHO(
            self.VTHO_generation_rate * self.economy.circulating_VET)

        # Handle usage trend
        # self.handle_usage_trend()

        # Handle external price trends
        self.economy.handle_price_trends()

        # Let agents make their step
        self.schedule.step()

        # Update the general buy-to-rent ratio
        self.buy_to_rent = (self.economy.VET_price /
                            self.VTHO_generation_rate) / self.economy.VTHO_price

        # Collect network data
        self.datacollector.collect(self)

        # Collect economic data
        self.economy.datacollector.collect(self.economy)

    def initialize_users(self):
        """Initializes the correct amount of users based on the usage trend that is being simulated.
        """

        if self.usage_trend in ["STABLE-SMALL", "UP-SMALL", "DOWN-SMALL"]:
            # Calculate the total amount of users
            _num_total_users = round(self.initial_VTHO_usage /
                                     self.small_user_size)

            # Add the main user
            self.add_users(1, self.main_user_strategy, self.small_user_size)

            # Add the other users
            self.add_users(_num_total_users-1,
                           self.user_strategies, self.small_user_size)

        elif self.usage_trend in ["STABLE-LARGE", "UP-LARGE", "DOWN-LARGE"]:
            # Calculate the total amount of users
            _num_total_users = round(self.initial_VTHO_usage /
                                     self.large_user_size)

            # Add the main user
            self.add_users(1, self.main_user_strategy, self.large_user_size)

            # Add the other users
            self.add_users(_num_total_users-1,
                           self.user_strategies, self.large_user_size)

    # def handle_usage_trend(self):
    #     if self.usage_trend in ["UP-SMALL", "UP-LARGE"]:
    #         # Increase total daily usage from trend
    #         self.current_usage_trend_size += self.usage_trend_step_size
    #     elif self.usage_trend in ["DOWN-SMALL", "DOWN-LARGE"]:
    #         # Increase total daily usage from trend
    #         self.current_usage_trend_size -= self.usage_trend_step_size

    #     # Remove VTHO from circulating supply based on usage trend
    #     if self.current_usage_trend_size > 0:
    #         self.economy.decrease_circulating_VTHO(
    #             self.current_usage_trend_size)

    def add_users(self, num_users, user_strategies, user_size):
        """Adds users.

        Args:
            num_users (int): Number of users to add.
            user_strategies (String): Strategy that the to-be added users need to apply.
            user_size (int): Size of the users to add.
        """

        if user_strategies == "DET":
            # Only add DET users
            for i in range(num_users):
                id = self.next_id()
                user = DeterministicUser(id, self, user_size)
                self.schedule.add(user)
            logging.info(f"Added {num_users} deterministic users.")
        elif user_strategies == "RAND":
            # Only add RAND users
            for i in range(num_users):
                id = self.next_id()
                user = RandomizedUser(id, self, user_size)
                self.schedule.add(user)
            logging.info(f"Added {num_users} randomized users.")
        elif user_strategies == "A-ADAPTED":
            # Only add A-ADAPTED users
            for i in range(num_users):
                id = self.next_id()
                user = AAdaptedUser(id, self, user_size)
                self.schedule.add(user)
            logging.info(f"Added {num_users} A-ADAPTED users.")
        elif user_strategies == "A-TREND":
            # Only add A-TREND users
            for i in range(num_users):
                id = self.next_id()
                user = ATrendUser(id, self, user_size)
                self.schedule.add(user)
            logging.info(f"Added {num_users} A-TREND users.")
        elif user_strategies == "RANDOM":
            # Only add RANDOM users
            for i in range(num_users):
                id = self.next_id()
                user = RandomUser(id, self, user_size)
                self.schedule.add(user)
            logging.info(f"Added {num_users} random users.")
        elif user_strategies == "KEEP-RENTING":
            # Only add KEEP RENTING users
            for i in range(num_users):
                id = self.next_id()
                user = KeepRentingUser(id, self, user_size)
                self.schedule.add(user)
            logging.info(f"Added {num_users} keep-renting users.")
        elif user_strategies == "INSTANT-BUY":
            # Only add INSTANT-BUY users
            for i in range(num_users):
                id = self.next_id()
                user = InstantBuyUser(id, self, user_size)
                self.schedule.add(user)
            logging.info(f"Added {num_users} instant-buy users.")
        elif user_strategies == "UNIFORM":
            _all_users = ["RANDOM", "DET", "RAND", "A-ADAPTED"]
            _all_users.remove(self.main_user_strategy)
            # Add one of each user that is not the main user
            for user in _all_users:
                self.add_users(1, user, user_size)
            logging.info(
                f"Added one of each user that is not {self.main_user_strategy}.")
        elif user_strategies == "UNIFORM-A-TREND":
            _all_users = ["RANDOM", "DET", "RAND", "A-TREND"]
            _all_users.remove(self.main_user_strategy)
            # Add one of each user that is not the main user
            for user in _all_users:
                self.add_users(1, user, user_size)
            logging.info(
                f"Added one of each user that is not {self.main_user_strategy}.")

    def calculate_adoption_ratio(self):
        """Calculates the current long-term adoption ratio (the ratio of active users that have bought).

        Returns:
            float: Adoption ratio.
        """
        _renting_count = 0
        _bought_count = 0

        # Count the number of active agents and those that have bought
        for agent in self.schedule.agents:
            if agent.state == "BOUGHT":
                _bought_count += 1
            elif agent.state == "RENTING":
                _renting_count += 1

        if _bought_count > 0:
            # Return the adoption ratio
            # return _bought_count / self.schedule.get_agent_count()
            return _bought_count / self.num_initial_users
        else:
            return 0
