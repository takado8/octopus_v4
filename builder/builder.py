import math

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from typing import Union, Optional

from builder.building_spot_validator import BuildingSpotValidator
from builder.structures_radius import STRUCTURES_RADIUS, STRUCTURE_MAX_RADIUS
from builder.validation_level_enum import Validation

GAP_SIZE = 0.5


class Builder:
    def __init__(self, ai, building_spot_validator: BuildingSpotValidator):
        self.ai = ai
        self.transport_area_validator: BuildingSpotValidator = building_spot_validator
        self.main_base_z = self.ai.get_terrain_z_height(self.ai.mineral_field.closest_to(self.ai.start_location))
        self.natural_z = self.ai.get_terrain_z_height(self.ai.main_base_ramp.bottom_center.towards(
            self.ai.main_base_ramp.top_center, -1))

    async def build(self,
                    building: UnitTypeId,
                    near: Union[Unit, Point2],
                    build_worker: Optional[Unit] = None,
                    validation: Validation = Validation.PLACEMENT_STEP
                    ) -> bool:
        if not self.ai.can_afford(building):
            return False

        if validation > Validation.NONE:
            position: Point2 = await self.find_placement(True, building, validation)
        else:
            position = near
        if not position:
            return False
        builder = build_worker or self.ai.select_build_worker(position)
        if builder is None:
            return False
        builder.build(building, position)
        return True

    async def find_placement(self, on_main_level: bool, unit_type_id: UnitTypeId, validation: Validation):
        pylon = self.get_pylon_with_least_neighbours()
        if not pylon:
            return False
        try:
            radius = STRUCTURES_RADIUS[unit_type_id] + GAP_SIZE
        except:
            radius = STRUCTURE_MAX_RADIUS + GAP_SIZE

        n = 200
        while True:
            n += 1
            distance = math.ceil(n / 50)
            if distance > 7:
                return False
            position = pylon.position.random_on_distance(distance)

            if not self.ai.in_map_bounds(position):
                continue
            if on_main_level and not self.is_on_main_base_lvl(position):
                continue
            if validation >= Validation.MINERAL_PATH:
                closest_expansion = min(self.ai.expansion_locations_list, key=lambda x: x.distance_to(position))
                if not self.transport_area_validator.is_valid_location(position.x, position.y, closest_expansion):
                    continue
            if validation >= Validation.PLACEMENT_STEP:
                too_close = self.ai.structures.filter(lambda x: x.distance_to(position) < x.radius + radius)
                if too_close.amount > 1:
                    continue
            if await self.ai.can_place_single(unit_type_id, position):
                return position

    def get_pylon_with_least_neighbours(self, in_main_base=True):
        if in_main_base:
            pylons = self.ai.structures.filter(lambda x: x.type_id == UnitTypeId.PYLON and x.is_ready and
                                                         self.is_on_main_base_lvl(x.position))
        else:
            pylons = self.ai.structures.filter(lambda x: x.type_id == UnitTypeId.PYLON and x.is_ready)
        if pylons:
            return min(pylons, key=lambda x: self.ai.structures.closer_than(6, x).amount)

    def is_on_main_base_lvl(self, position):
        position_z_height = self.ai.get_terrain_z_height(position)
        return abs(self.main_base_z - position_z_height) < \
            abs(self.natural_z - position_z_height)
