from sc2.bot_ai import BotAI

from strategy.gate import Gate
from strategy.strategy import Strategy


class OctopusV4(BotAI):
    def __init__(self):
        self.strategy: Strategy = None

    async def on_start(self):
        self.strategy = Gate(self)

    async def on_step(self, iteration: int):
        await self.strategy.execute()
