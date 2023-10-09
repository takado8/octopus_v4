from builder.pylon_builder import PylonBuilder
from opening.opening_service import OpeningService
from opening.openings.opening import Opening
from strategy.strategy import Strategy


class Gate(Strategy):
    def __init__(self, ai):
        super().__init__(ai)
        self.pylon_builder = PylonBuilder(ai)
        self.opening_service: OpeningService = OpeningService(ai)
        self.opening: Opening = self.opening_service.choose_opening()(ai)

    async def execute(self):
        await self.ai.distribute_workers()
        await self.pylon_builder.get_next_pylon_position()
