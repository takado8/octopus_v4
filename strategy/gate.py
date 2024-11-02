import asyncio

from builder.validation_level_enum import Validation
from strategy.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId as unit_id


class Gate(Strategy):
    def __init__(self, ai):
        super().__init__(ai)
        self.pylons_out = False

    async def execute(self):

        # self.probe_scouting.scout()
        all_tasks = await asyncio.gather(
            self.handle_workers(),
            self.scout_midgame()
        )
        if self.ai.workers.amount < 20:
            if self.ai.townhalls.idle.exists:
                self.ai.train(unit_id.PROBE)

        if not self.pylons_out and self.ai.supply_left < 3 and not self.ai.already_pending(unit_id.PYLON):
            if self.ai.can_afford(unit_id.PYLON):
                next_pylon_position = await self.pylon_builder.get_next_pylon_position()
                if next_pylon_position:
                    await self.builder.build(unit_id.PYLON, next_pylon_position, validation=Validation.NONE)
                else:
                    self.pylons_out = True


        if not self.ai.structures({unit_id.GATEWAY, unit_id.WARPGATE}).exists and not self.ai.already_pending(unit_id.GATEWAY):
            await self.builder.build(unit_id.GATEWAY, self.ai.start_location)

        if self.ai.structures({unit_id.GATEWAY, unit_id.WARPGATE}).ready.exists and not self.ai.already_pending(unit_id.CYBERNETICSCORE) and not self.ai.structures(unit_id.CYBERNETICSCORE).exists:
            await self.builder.build(unit_id.CYBERNETICSCORE, self.ai.start_location)

        if self.ai.structures({unit_id.GATEWAY, unit_id.WARPGATE}).exists and not self.ai.already_pending(unit_id.ASSIMILATOR) and not self.ai.structures(unit_id.ASSIMILATOR).exists:
            await self.ai.build(unit_id.ASSIMILATOR, self.ai.vespene_geyser.closest_to(self.ai.start_location))

        if self.ai.structures(unit_id.CYBERNETICSCORE).ready.exists and self.ai.units(unit_id.SENTRY).amount < 5 and self.ai.can_afford(unit_id.SENTRY):
            self.ai.train(unit_id.SENTRY)
