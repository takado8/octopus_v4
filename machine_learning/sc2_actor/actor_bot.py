from typing import Union, Optional

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

from strategy.ddpg_training import DDPGTraining
from strategy.strategy import Strategy
from utils.constants import BASES_IDS, OWN_ARMY_IDS, WORKERS_IDS


class ActorBot(BotAI):
    def __init__(self):
        super().__init__()
        self.strategy: Strategy = None
        self.iteration = 0
        self.bases_ids = BASES_IDS
        self.workers_ids = WORKERS_IDS
        self.army = []
        self.visual = None

    async def on_start(self):
        self.strategy = DDPGTraining(self)

    async def on_step(self, iteration: int):
        self.iteration = iteration
        self.army = self.units.filter(lambda u: u.type_id in OWN_ARMY_IDS)
        await self.strategy.execute()


    # async def build(
    #     self,
    #     building: UnitTypeId,
    #     near: Union[Unit, Point2],
    #     max_distance: int = 20,
    #     build_worker: Optional[Unit] = None,
    #     random_alternative: bool = True,
    #     placement_step: int = 2,
    # ) -> bool:
    #     return await self.strategy.builder.build()
