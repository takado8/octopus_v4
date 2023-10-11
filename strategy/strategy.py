from builder.building_spot_validator import BuildingSpotValidator
from builder.builder import Builder
from builder.pylon_builder import PylonBuilder
from opening.opening_service import OpeningService
from opening.openings.opening import Opening


class Strategy:
    def __init__(self, ai):
        self.ai = ai
        self.building_spot_validator = BuildingSpotValidator(ai)
        self.builder = Builder(ai)
        self.pylon_builder = PylonBuilder(ai)
        self.opening_service: OpeningService = OpeningService(ai)
        self.opening: Opening = self.opening_service.choose_opening()(ai)

    async def execute(self):
        raise NotImplementedError()