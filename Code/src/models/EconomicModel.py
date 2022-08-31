import logging
from mesa import Model
from mesa.datacollection import DataCollector
import pandas as pd
import pickle


class EconomicModel(Model):
    """Model of the money.

    Args:
        Model (Mesa model): Models.
    """

    def __init__(self,
                 economic_influences,
                 price_trend_setting,
                 price_trend_length,
                 steps_between_price_trend,
                 VET_starting_price,
                 VTHO_starting_price,
                 total_starting_VET,
                 total_starting_VTHO,
                 VET_liquidity_ratio,
                 VTHO_liquidity_ratio):
        """Initializes the economy.

        Args:
            VET_starting_price (float): Starting price of the VET token.
            VTHO_starting_price (float): Starting price of the VTHO token.
        """

        # Set the model settings.
        self.network_step = 0
        self.economic_influences = economic_influences
        self.VET_price = VET_starting_price
        self.VTHO_price = VTHO_starting_price

        # Totals on chain
        self.circulating_VET = total_starting_VET
        self.circulating_VTHO = total_starting_VTHO
        self.VET_liquidity_ratio = VET_liquidity_ratio
        self.VTHO_liquidity_ratio = VTHO_liquidity_ratio

        # Totals in the orderbooks
        self.liquidity_VET = self.VET_liquidity_ratio * self.circulating_VET
        self.liquidity_VTHO = self.VTHO_liquidity_ratio * self.circulating_VTHO

        # Initialize the LOB's
        self.LOB_VET = pd.read_csv(
            "Model/Code/src/LOB/LOB_VET.csv").iloc[:, 1:]
        self.LOB_VTHO = pd.read_csv(
            "Model/Code/src/LOB/LOB_VTHO.csv").iloc[:, 1:]
        self.VET_LOB_tick_size = 0.00426
        self.VTHO_LOB_tick_size = 0.00684

        # Initialize price trends
        self.price_trend_setting = price_trend_setting
        self.price_trend_length = price_trend_length
        self.steps_between_price_trend = steps_between_price_trend
        self.initialize_price_trend()

        # Initialize the data collection
        self.datacollector = DataCollector(
            model_reporters={
                "network_step": "network_step",
                "circulating_VET": "circulating_VET",
                "circulating_VTHO": "circulating_VTHO",
                "liquidity_VET": "liquidity_VET",
                "liquidity_VTHO": "liquidity_VTHO",
                "VET_price": "VET_price",
                "VTHO_price": "VTHO_price"},
            agent_reporters={}
        )

        # Collect intial data
        self.datacollector.collect(self)

        # Logging
        logging.warning("Initialized the economic model.")

    def initialize_price_trend(self):
        """Initializes the external price trend.
        """
        if self.price_trend_setting == "VET-up" or self.price_trend_setting == "BOTH-up":
            filehandler = open("Model/Code/src/price_trends/VET-up.pkl", "rb")
            self.VET_trend = pickle.load(filehandler)
            filehandler.close()

        elif self.price_trend_setting == "VET-down" or self.price_trend_setting == "BOTH-down":
            filehandler = open(
                "Model/Code/src/price_trends/VET-down.pkl", "rb")
            self.VET_trend = pickle.load(filehandler)
            filehandler.close()
        else:
            self.VET_trend = 0

        if self.price_trend_setting == "VTHO-up" or self.price_trend_setting == "BOTH-up":
            filehandler = open("Model/Code/src/price_trends/VTHO-up.pkl", "rb")
            self.VTHO_trend = pickle.load(filehandler)
            filehandler.close()
        elif self.price_trend_setting == "VTHO-down" or self.price_trend_setting == "BOTH-down":
            filehandler = open(
                "Model/Code/src/price_trends/VTHO-down.pkl", "rb")
            self.VTHO_trend = pickle.load(filehandler)
            filehandler.close()
        else:
            self.VTHO_trend = 0

    def VET_order(self, amount, LOB, order_type, influence_price=True):
        """Determines the type of VET order that is placed and executes it.

        Args:
            amount (int): The amount of VET to buy when positive or sell when negative.
            order_type (String): Either `SELL' or `BUY'.
        Returns:
            float: The FIAT price that is paid/earned.
        """

        # BUY
        if order_type == "BUY":
            _LOB_orders = LOB[50:]
        # SELL
        elif order_type == "SELL":
            _LOB_orders = LOB[:50][::-1]

        # Calculate how much to buy/sell and the effect on price
        _relative_order_size = amount / self.liquidity_VET
        _tick_change = _LOB_orders.cumsum().searchsorted(_relative_order_size)

        # Calculate how much to buy from the last of the i orders
        _amount_from_last_order = amount - \
            sum([_LOB_orders[i]*self.liquidity_VET for i in range(_tick_change)])

        # Calculate total price paid
        _price_paid_last_order = _amount_from_last_order * \
            (self.VET_price + (_tick_change * self.VET_LOB_tick_size))
        _price_paid = sum([_LOB_orders[i]*self.liquidity_VET*(self.VET_price + (
            i * self.VET_LOB_tick_size)) for i in range(_tick_change)]) + _price_paid_last_order

        # if self.economic_influences in ["ADOPTION", "TREND", "BOTH"]:
        if influence_price:
            # Calculate and log the new VET price
            if order_type == "BUY":
                _new_price = self.VET_price + \
                    (_tick_change * self.VET_LOB_tick_size)
            elif order_type == "SELL":
                _new_price = self.VET_price - \
                    (_tick_change * self.VET_LOB_tick_size)

            # Update the price of VET
            if amount == 0:
                logging.info("No VET was bough or sold")
            else:
                self.update_VET_price(_new_price)

        return _price_paid

    def VTHO_order(self, amount, LOB, order_type, influence_price=True):
        """Determines the type of VTHO order that is placed and executes it.

        Args:
            amount (int): The amount of VTHO to buy when positive or sell when negative.
            order_type (String): Either `SELL' or `BUY'.
        Returns:
            float: The FIAT price that is paid/earned.
        """

        # BUY
        if order_type == "BUY":
            _LOB_orders = LOB[50:]
        # SELL
        elif order_type == "SELL":
            _LOB_orders = LOB[:50][::-1]

        # Calculate how much to buy/sell and the effect on price
        _relative_order_size = amount / self.liquidity_VTHO
        _tick_change = _LOB_orders.cumsum().searchsorted(_relative_order_size)
        logging.warning(f"Tick change = {_tick_change}")

        # Calculate how much to buy from the last of the i orders
        _amount_from_last_order = amount - \
            sum([_LOB_orders[i]*self.liquidity_VTHO for i in range(_tick_change)])

        # Calculate total price paid
        if order_type == "BUY":
            _price_paid_last_order = _amount_from_last_order * \
                (self.VTHO_price * (1 + (_tick_change * self.VTHO_LOB_tick_size)))
            _price_paid = sum([_LOB_orders[i]*self.liquidity_VTHO*(self.VTHO_price * (
                1 + (i * self.VTHO_LOB_tick_size))) for i in range(_tick_change)]) + _price_paid_last_order
        elif order_type == "SELL":
            _price_paid_last_order = _amount_from_last_order * \
                (self.VTHO_price * (1 - (_tick_change * self.VTHO_LOB_tick_size)))
            _price_paid = sum([_LOB_orders[i]*self.liquidity_VTHO*(self.VTHO_price * (
                1 - (i * self.VTHO_LOB_tick_size))) for i in range(_tick_change)]) + _price_paid_last_order

        # if self.economic_influences in ["ADOPTION", "TREND", "BOTH"]:
        if influence_price:
            # Calculate and log the new VTHO price
            if order_type == "BUY":
                _new_price = self.VTHO_price * \
                    (1 + (_tick_change * self.VTHO_LOB_tick_size))
            elif order_type == "SELL":
                _new_price = self.VTHO_price * \
                    (1 - (_tick_change * self.VTHO_LOB_tick_size))

            # Update the price of VTHO
            if amount == 0:
                logging.info("No VTHO was bough or sold")
            else:
                self.update_VTHO_price(_new_price)

        return _price_paid

    def handle_price_trends(self):
        if self.network_step <= self.price_trend_length:
            if self.network_step != 0 and self.network_step % self.steps_between_price_trend == 0:
                _VET_trends = ["VET-up", "VET-down", "BOTH-up", "BOTH-down"]
                _VTHO_trends = ["VTHO-up", "VTHO-down", "BOTH-up", "BOTH-down"]
                if self.price_trend_setting in _VET_trends:
                    self.VET_price = self.VET_price * \
                        self.VET_trend[round(
                            self.network_step/self.steps_between_price_trend)-1]
                if self.price_trend_setting in _VTHO_trends:
                    self.VTHO_price = self.VTHO_price * \
                        self.VTHO_trend[round(
                            self.network_step/self.steps_between_price_trend)-1]

    def increase_circulating_VTHO(self, amount):
        """Increases the amount of existing VTHO by the given amount.

        Args:
            amount (int): Amount to increase the total by
        """
        # Increase total
        self.circulating_VTHO += amount

        # Recalculate orderbook totals
        self.liquidity_VTHO = self.VTHO_liquidity_ratio * self.circulating_VTHO

    def decrease_circulating_VTHO(self, amount):
        """Decreases the amount of existing VTHO by the given amount.

        Args:
            amount (int): Amount to decrease the total by
        """
        # Decrease total
        self.circulating_VTHO -= amount

        # Recalculate orderbook totals
        self.liquidity_VTHO = self.VTHO_liquidity_ratio * self.circulating_VTHO

    def decrease_circulating_VET(self, amount):
        """
        """
        # Decrease total
        self.circulating_VET -= amount

        # Recalculate orderbook totals
        self.liquidity_VET = self.VET_liquidity_ratio * self.circulating_VET

    def increase_circulating_VET(self, amount):
        """
        """
        # Increase total
        self.circulating_VET += amount

        # Recalculate orderbook totals
        self.liquidity_VET = self.VET_liquidity_ratio * self.circulating_VET

    def increase_network_step(self):
        """Increases the network step by one.
        """
        self.network_step += 1

    def update_VET_price(self, new_price):
        """Updates the price of a single VET.

        Args:
            new_price (float ): New price of a single VET
        """
        self.update_VET_liquidity(new_price)
        self.VET_price = new_price

    def update_VTHO_price(self, new_price):
        """Updates the price of a single VTHO.

        Args:
            new_price (float ): New price of a single VTHO
        """
        self.update_VTHO_liquidity(new_price)
        self.VTHO_price = new_price

    def update_VET_liquidity(self, new_price):
        _change = 1 - (self.VET_price/new_price)
        self.VET_liquidity_ratio *= (1+(_change/5))

    def update_VTHO_liquidity(self, new_price):
        _change = 1 - (self.VTHO_price/new_price)
        self.VTHO_liquidity_ratio *= (1+(_change/5))
