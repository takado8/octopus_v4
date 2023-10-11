from typing import Union, Optional

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from strategy.gate import Gate
from strategy.strategy import Strategy


class OctopusV4(BotAI):
    def __init__(self):
        self.strategy: Strategy = None

    async def on_start(self):
        self.strategy = Gate(self)

    async def on_step(self, iteration: int):
        await self.strategy.execute()

    async def build(
        self,
        building: UnitTypeId,
        near: Union[Unit, Point2],
        max_distance: int = 20,
        build_worker: Optional[Unit] = None,
        random_alternative: bool = True,
        placement_step: int = 2,
    ) -> bool:
        return await self.strategy.builder.build()
