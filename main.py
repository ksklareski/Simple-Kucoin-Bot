import os
from tracemalloc import start
import pytz
from datetime import datetime
from time import sleep
from kucoin_futures.client import Trade
from kucoin_futures.client import User
from kucoin_futures.client import Market
from dotenv import load_dotenv


class trade_bot:
    def __init__(
        self,
        pair,
        maxLeverage,
        takeProfitPercent,
        stopLossPercent,
        passphrase,
        key,
        secret,
        url,
    ):
        self.pair = pair
        self.maxLeverage = maxLeverage
        self.takeProfitPercent = (takeProfitPercent / maxLeverage) / 100.0
        self.stopLossPercent = (stopLossPercent / maxLeverage) / 100.0
        self.passphrase = passphrase
        self.key = key
        self.secret = secret
        self.url = url

        self.UTC = pytz.utc

        self.trade_client = Trade(
            key=self.key,
            secret=self.secret,
            passphrase=self.passphrase,
            is_sandbox=False,
            url=self.url,
        )
        self.user_client = User(self.key, self.secret, self.passphrase)
        self.market_client = Market()

    # TODO: This should be implemented as a decorator
    def safeWebCall(self, func, request_type="info"):
        success = False
        backoff = 0
        while not success:
            try:
                sleep(backoff)
                result = func()
                success = True
            except Exception as e:
                e = str(e).lower()
                if (
                    ("too many requests" in e)
                    or ("read timed out." in e)
                    or ("internal server error" in e)
                    or ("unavailable to proceed the operation." in e)
                ):
                    self.print_log("Got rate limited", lvl="WARN")
                    if backoff == 0:
                        backoff += 1
                    else:
                        backoff *= 2
                elif (request_type == "trade") and (
                    "current position size: 0, unable to close the position." in e
                ):
                    self.print_log("Attempted to create order too fast", lvl="WARN")
                    if backoff == 0:
                        backoff += 1
                    else:
                        backoff *= 2
        return result

    def roundToNearest(self, base, num):
        return self.truncateFloat(base * round(num / base), self.lenTick)

    def truncateFloat(self, num, n):
        assert type(n) == int
        integer = int(num * (10**n)) / (10**n)
        return float(integer)

    def cancelAllOrders(self):
        self.print_log("Canceling all limit orders", "INFO")
        self.safeWebCall(
            lambda: self.trade_client.cancel_all_limit_order(symbol=self.pair)
        )

        self.print_log("Canceling all stop orders", "INFO")
        self.safeWebCall(
            lambda: self.trade_client.cancel_all_stop_order(symbol=self.pair)
        )

    def print_log(self, msg: str, lvl="INFO"):
        print(f"{datetime.now(self.UTC)}: [{lvl}]: {msg}")

    def run(self):
        self.print_log("Starting bot", "INFO")

        # Get data about the contract
        data = self.safeWebCall(
            lambda: self.market_client.get_contract_detail(self.pair)
        )
        self.minPriceIncrement = float(data["tickSize"])
        self.lenTick = len(str(self.minPriceIncrement).split(".")[1])

        """
        DEV: This multiplier controls the minimum amount of an asset you can trade
            It gets nomalized as so:
                1/0.01 = 100
                2/1 = 0.5
        """
        self.minOrderSizeMultiplier = 1.0 / float(data["multiplier"])

        self.print_log(
            f"Leverage: {self.maxLeverage}, Take Profit Percent: {self.takeProfitPercent}, Stop Loss Percent: {self.stopLossPercent}, Min tick size: {self.minPriceIncrement}",
            "INFO",
        )

        # Init by canceling all open orders
        self.cancelAllOrders()

        ordersCreated = False
        posid = ""

        while True:
            posDeets = self.safeWebCall(
                lambda: self.trade_client.get_position_details(self.pair)
            )

            entryPrice = posDeets["avgEntryPrice"]
            posSize = posDeets["currentQty"]
            isOpen = posDeets["isOpen"]

            # TODO: Possibly close position before funding (if funding is positive)?

            # Enter a position
            if (posSize == 0) and (not isOpen):
                self.print_log("Position size is 0, entering new position", "INFO")
                self.cancelAllOrders()

                availableBalance = (
                    float(
                        self.user_client.get_account_overview(currency="USDT")[
                            "availableBalance"
                        ]
                    )
                    * 0.97
                )
                currPrice = float(
                    self.market_client.get_ticker(self.pair)["bestAskPrice"]
                )

                self.print_log(f"Available balance is: {availableBalance}")

                newPosSize = int(
                    self.truncateFloat(
                        ((availableBalance * (self.maxLeverage)) / currPrice)
                        * self.minOrderSizeMultiplier,
                        0,
                    )
                )

                self.print_log(
                    f"Submitting market order with size {newPosSize}", "INFO"
                )
                posid = self.safeWebCall(
                    lambda: self.trade_client.create_market_order(
                        symbol=self.pair,
                        side="buy",
                        lever=self.maxLeverage,
                        size=newPosSize,
                    ),
                    "trade",
                )["orderId"]

                # Wait for order to fill
                status = "open"
                while status != "done":
                    status = self.safeWebCall(
                        lambda: self.trade_client.get_order_details(orderId=posid)
                    )["status"]

                self.print_log("Position opened", "INFO")

                ordersCreated = False

            # Create close orders if position is open
            elif (posSize > 0) and (entryPrice > 0) and isOpen and (not ordersCreated):
                takeProfit = self.roundToNearest(
                    self.minPriceIncrement, entryPrice * (1.0 + self.takeProfitPercent)
                )
                stopPrice = self.roundToNearest(
                    self.minPriceIncrement,
                    entryPrice - (entryPrice * self.stopLossPercent),
                )
                self.print_log(
                    f"Position with size {posSize} opened at price {entryPrice} detected, creating limit at {takeProfit} and stop at {stopPrice}",
                    "INFO",
                )

                # Create limit order
                self.safeWebCall(
                    lambda: self.trade_client.create_limit_order(
                        symbol=self.pair,
                        side="sell",
                        lever=self.maxLeverage,
                        size=posSize,
                        price=takeProfit,
                        reduceOnly=True,
                    ),
                    request_type="trade",
                )

                # Create stop order
                self.safeWebCall(
                    lambda: self.trade_client.create_market_order(
                        symbol=self.pair,
                        side="sell",
                        lever=self.maxLeverage,
                        size=posSize,
                        stopPrice=stopPrice,
                        stop="down",
                        stopPriceType="TP",
                        reduceOnly=True,
                    ),
                    request_type="trade",
                )

                self.print_log("All orders created", "INFO")

                ordersCreated = True


if __name__ == "__main__":
    load_dotenv(override=True)

    client = trade_bot(
        pair=os.environ["KUCOIN_PAIR"],
        maxLeverage=float(os.environ["KUCOIN_MAX_LEVERAGE"]),
        takeProfitPercent=float(os.environ["KUCOIN_TAKE_PROFIT_PERCENT"]),
        stopLossPercent=float(os.environ["KUCOIN_STOP_LOSS_PERCENT"]),
        passphrase=os.environ["KUCOIN_API_PASSPHRASE"],
        key=os.environ["KUCOIN_API_KEY"],
        secret=os.environ["KUCOIN_API_SECRET"],
        url=os.environ["KUCOIN_API_URL"],
    )

    client.run()
