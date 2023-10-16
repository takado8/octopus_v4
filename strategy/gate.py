from builder.validation_level_enum import Validation
from strategy.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId as unit_id


class Gate(Strategy):
    def __init__(self, ai):
        super().__init__(ai)
        self.pylons_out = False

    async def execute(self):
        await self.ai.distribute_workers()
        if self.ai.workers.amount < 11 + 1 * self.ai.time/60:
            if self.ai.townhalls.idle.exists:
                self.ai.train(unit_id.PROBE)
        if not self.pylons_out and self.ai.supply_left < 3 and not self.ai.already_pending(unit_id.PYLON):
            if self.ai.can_afford(unit_id.PYLON):
                next_pylon_position = await self.pylon_builder.get_next_pylon_position()
                if next_pylon_position:
                    await self.builder.build(unit_id.PYLON, next_pylon_position, validation=Validation.NONE)
                else:
                    self.pylons_out = True

        # await self.builder.build(unit_id.GATEWAY, self.ai.start_location)
