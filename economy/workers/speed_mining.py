from typing import List
import math
from sc2.ids.ability_id import AbilityId
from typing import Dict
from sc2.position import Point2
from sc2.unit import Unit, UnitTypeId


MINING_RADIUS = 1.325


class SpeedMining:
    """ Make worker mine faster perhaps? """

    def __init__(self, ai, enable_on_return=True, enable_on_mine=True):
        self.ai = ai
        self.enable_on_return = enable_on_return
        self.enable_on_mine = enable_on_mine
        self.mineral_target_dict: Dict[Point2, Point2] = {}
        self.calculate_targets()

    def execute(self, mineral_workers_tags):
        mineral_workers = self.ai.workers.filter(lambda x: x.tag in mineral_workers_tags)
        self.speedmine(mineral_workers)

    def get_mineral_workers(self) -> List:
        bases = self.ai.townhalls.ready
        mineral_workers = []
        for base in bases:
            local_minerals_tags = {mineral.tag for mineral in self.ai.mineral_field
                                   if mineral.distance_to(base) <= 8}
            local_workers = self.ai.workers.filter(
                lambda unit: unit.order_target in local_minerals_tags
                             or (unit.is_carrying_minerals and unit.order_target == base.tag))
            mineral_workers.extend(local_workers)
        return mineral_workers

    def speedmine(self, workers: List):
        for worker in workers:
            self.speedmine_single(worker)

    def speedmine_single(self, worker: Unit):
        townhall = self.ai.townhalls.closest_to(worker)

        if len(worker.orders) == 1 and worker.is_carrying_minerals:
            target: Point2 = townhall.position
            target = target.towards(worker, townhall.radius + worker.radius + 0.5)
            if 0.75 < worker.distance_to(target) < 2:
                worker.move(target)
                worker(AbilityId.HARVEST_RETURN_PROBE, queue=True)
                return

        if (
                len(worker.orders) == 1
                and isinstance(worker.order_target, int)
        ):
            mineral_field = self.ai.mineral_field.find_by_tag(worker.order_target)
            if mineral_field is not None and mineral_field.is_mineral_field:

                target = self.mineral_target_dict.get(mineral_field.position)
                if 0.75 < worker.distance_to(target) < 2:
                    worker.move(target)
                    worker(AbilityId.SMART, mineral_field, True)

    def calculate_targets(self):
        # zone_manager = self.knowledge.get_required_manager(IZoneManager)
        # zones = zone_manager.expansion_zones
        centers: List[Point2] = [nexus.position for nexus in self.ai.structures(UnitTypeId.NEXUS).ready]

        # for zone in zones:
        #     centers.append(zone.center_location)

        for mineral_field in self.ai.mineral_field:
            target: Point2 = mineral_field.position
            center = target.closest(centers)
            target = target.towards(center, MINING_RADIUS)
            close = self.ai.mineral_field.closer_than(MINING_RADIUS, target)
            for mineral_field2 in close:
                if mineral_field2.tag != mineral_field.tag:
                    points = self.get_intersections(mineral_field.position, MINING_RADIUS, mineral_field2.position,
                        MINING_RADIUS)
                    if len(points) == 2:
                        target = center.closest(points)
            self.mineral_target_dict[mineral_field.position] = target

    @staticmethod
    def get_intersections(p0: Point2, r0: float, p1: Point2, r1: float) -> List[Point2]:
        return SpeedMining._get_intersections(p0.x, p0.y, r0, p1.x, p1.y, r1)

    @staticmethod
    def _get_intersections(x0: float, y0: float, r0: float, x1: float, y1: float, r1: float) -> List[Point2]:
        # circle 1: (x0, y0), radius r0
        # circle 2: (x1, y1), radius r1

        d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

        # non-intersecting
        if d > r0 + r1:
            return []
        # One circle within other
        if d < abs(r0 - r1):
            return []
        # coincident circles
        if d == 0 and r0 == r1:
            return []
        else:
            a = (r0 ** 2 - r1 ** 2 + d ** 2) / (2 * d)
            h = math.sqrt(r0 ** 2 - a ** 2)
            x2 = x0 + a * (x1 - x0) / d
            y2 = y0 + a * (y1 - y0) / d
            x3 = x2 + h * (y1 - y0) / d
            y3 = y2 - h * (x1 - x0) / d

            x4 = x2 - h * (y1 - y0) / d
            y4 = y2 + h * (x1 - x0) / d

            return [Point2((x3, y3)), Point2((x4, y4))]
