from builder.building_spot_validator import BuildingSpotValidator
from builder.builder import Builder
from builder.pylon_builder import PylonBuilder
from economy.workers.distribute_workers import DistributeWorkers
from economy.workers.speed_mining import SpeedMining
from opening.opening_service import OpeningService
from opening.openings.opening import Opening
from scouting.probe_scouting import ProbeScouting


class Strategy:
    def __init__(self, ai):
        self.ai = ai
        building_spot_validator: BuildingSpotValidator = BuildingSpotValidator(ai)
        self.builder = Builder(ai, building_spot_validator)
        self.pylon_builder = PylonBuilder(ai, building_spot_validator)
        self.opening_service: OpeningService = OpeningService(ai)
        self.opening: Opening = self.opening_service.choose_opening()(ai)
        self.workers_distribution = DistributeWorkers(ai)
        self.speed_mining = SpeedMining(ai)
        self.probe_scouting = ProbeScouting(ai)

    async def execute(self):
        raise NotImplementedError()

    async def handle_workers(self):
        mineral_workers_tags = self.workers_distribution.get_mineral_workers_tags()
        scouting_probe_tag = self.probe_scouting.scout_tag
        self.workers_distribution.distribute_workers(excluded_tags={scouting_probe_tag})
        self.speed_mining.execute(mineral_workers_tags)
