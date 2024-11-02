import asyncio

from sc2.bot_ai import BotAI


class WorkerRushBot(BotAI):
    async def on_step(self, iteration: int):
        all_tasks = await asyncio.gather(
            self.distribute_workers(),
        )