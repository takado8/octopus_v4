import asyncio

from builder.validation_level_enum import Validation
from game_data.cnn_input import SC2InputGenerator
from strategy.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId as unit_id

action_dict = {'pass': 0, 'attack': 1}


class Gate(Strategy):
    def __init__(self, ai):
        super().__init__(ai)
        self.pylons_out = False
        self.expansion_locations = None
        self.natural_location = None

    async def execute(self):
        if not self.expansion_locations:
            self.expansion_locations = sorted(self.ai.expansion_locations_list, key=lambda x: self.ai.start_location.distance_to(x))
            self.natural_location = self.expansion_locations[1]
        # self.probe_scouting.scout()
        all_tasks = await asyncio.gather(
            self.handle_workers(),
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

        if self.ai.structures(unit_id.CYBERNETICSCORE).ready.idle.exists and self.ai.units(unit_id.STALKER).amount < 1 and self.ai.can_afford(unit_id.STALKER):
            self.ai.train(unit_id.STALKER)
        elif self.ai.structures({unit_id.GATEWAY, unit_id.WARPGATE}).ready.idle.exists and self.ai.units(unit_id.ZEALOT).amount < 2 and  self.ai.can_afford(unit_id.ZEALOT):
            self.ai.train(unit_id.ZEALOT)


        zealot = self.ai.units(unit_id.ZEALOT)
        zealot = zealot.first if zealot else None

        stalker = self.ai.units(unit_id.STALKER)
        stalker = stalker.first if stalker else None

        if zealot and zealot.distance_to(self.natural_location) > 4:
            zealot.move(self.natural_location)

        action = 'pass'
        if stalker and zealot:
            if zealot.distance_to(self.natural_location) < 5 and stalker.distance_to(zealot) > 7:
                stalker.move(zealot.position.towards(self.ai.start_location, 5))
            elif stalker.distance_to(zealot) < 7 and zealot.distance_to(self.natural_location) < 2:
                stalker.attack(zealot)
                action = 'attack'

            own_units = [{'x': stalker.position.x, 'y': stalker.position.y, 'hp': 0.8, 'cooldown': 0.2}]
            enemy_units = [{'x': zealot.position.x, 'y': zealot.position.y, 'hp': 0.6, 'cooldown': 0.5}]
            unmovable_terrain = []
            relative_center = self.natural_location.x, self.natural_location.y
            input_size = 32

            generator = SC2InputGenerator(input_size)
            input_tensor = generator.generate_input(own_units, enemy_units, unmovable_terrain, relative_center)
            generator.visualize_input(input_tensor)