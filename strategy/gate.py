from strategy.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId as unit_id


class Gate(Strategy):
    def __init__(self, ai):
        super().__init__(ai)

    async def execute(self):
        await self.ai.distribute_workers()
        next_pylon_position = await self.pylon_builder.get_next_pylon_position()
        if next_pylon_position:
            await self.builder.build(unit_id.PYLON, next_pylon_position)
