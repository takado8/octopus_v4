from sc2.ids.unit_typeid import UnitTypeId as unit
import math


class PylonBuilder:
    def __init__(self, ai):
        self.ai = ai
        self.main_base_z = self.ai.get_terrain_z_height(self.ai.mineral_field.closest_to(self.ai.start_location))
        self.natural_z = self.ai.get_terrain_z_height(self.ai.main_base_ramp.bottom_center.towards(
            self.ai.main_base_ramp.top_center, -1))

    async def get_next_pylon_position(self):
        if self.ai.can_afford(unit.PYLON):
            pylons = self.ai.structures(unit.PYLON)
            n = 200
            while True:
                n += 1
                distance = math.ceil(n / 50)
                if distance > 45:
                    return False
                position = self.ai.start_location.position.random_on_distance(distance)
                is_in_bounds = self.ai.in_map_bounds(position)
                if not is_in_bounds:
                    continue
                if self.is_on_main_base_lvl(position):
                    if pylons.closer_than(7, position).exists:
                        continue
                    elif await self.ai.can_place_single(unit.PYLON, position):
                        return position

    def is_on_main_base_lvl(self, position):
        position_z_height = self.ai.get_terrain_z_height(position)
        return abs(self.main_base_z - position_z_height) < \
            abs(self.natural_z - position_z_height)
