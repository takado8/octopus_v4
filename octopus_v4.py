from typing import Union, Optional

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from economy.income_statistics import IncomeStatistics
from optimizer.build_order_optimizer import BuildOrderOptimizer
from strategy.gate import Gate
from strategy.strategy import Strategy
import matplotlib.pyplot as plt
import time


class OctopusV4(BotAI):
    def __init__(self):
        self.strategy: Strategy = None

    async def on_start(self):
        self.strategy = Gate(self)
        start = time.time()
        optimizer = BuildOrderOptimizer(self)
        # build = [UnitTypeId.GATEWAY, UnitTypeId.ASSIMILATOR, UnitTypeId.GATEWAY,
        #          UnitTypeId.CYBERNETICSCORE, UnitTypeId.GATEWAY, UnitTypeId.GATEWAY, UnitTypeId.STALKER,
        #
        #          UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER,
        #          UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER,
        #          UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER,
        #          UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER,
        #          UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER, UnitTypeId.STALKER,
        #          UnitTypeId.STALKER, UnitTypeId.STALKER]

        # print(optimizer.evaluate_build_order(build))

        optimizer.run()
        stop = time.time()
        elapsed = stop - start
        print(f'Time: {elapsed}')
        exit(7)

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
