from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from typing import Union, Optional

from builder.building_spot_validator import BuildingSpotValidator
from builder.validation_level_enum import Validation


class Builder:
    def __init__(self, ai, building_spot_validator: BuildingSpotValidator):
        self.ai = ai
        self.transport_area_validator: BuildingSpotValidator = building_spot_validator

    async def build(
            self,
            building: UnitTypeId,
            near: Union[Unit, Point2],
            max_distance: int = 20,
            build_worker: Optional[Unit] = None,
            random_alternative: bool = True,
            placement_step: int = 2,
            validation: Validation = Validation.PLACEMENT_STEP
    ) -> bool:
        if not self.ai.can_afford(building):
            return False

        if building != UnitTypeId.PYLON or validation > Validation.NONE:
            closest_expansion = min(self.ai.expansion_locations_list, key=lambda x: x.distance_to(near))
            if not self.transport_area_validator.is_valid_location(near.x, near.y, closest_expansion):
                return False

        builder = build_worker or self.ai.select_build_worker(near)
        if builder is None:
            return False
        builder.build(building, near)
        return True
