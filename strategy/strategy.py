from builder.building_spot_validator import BuildingSpotValidator
from builder.builder import Builder
from builder.pylon_builder import PylonBuilder
from opening.opening_service import OpeningService
from opening.openings.opening import Opening


class Strategy:
    def __init__(self, ai):
        self.ai = ai
        building_spot_validator: BuildingSpotValidator = BuildingSpotValidator(ai)
        self.builder = Builder(ai, building_spot_validator)
        self.pylon_builder = PylonBuilder(ai, building_spot_validator)
        self.opening_service: OpeningService = OpeningService(ai)
        self.opening: Opening = self.opening_service.choose_opening()(ai)

    async def execute(self):
        raise NotImplementedError()