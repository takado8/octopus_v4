from sc2.ids.unit_typeid import UnitTypeId as unit
from utils.bot_math import points_on_circumference_sorted


class ProbeScouting:
    def __init__(self, ai):
        self.ai = ai
        self.scout_tag = None
        self.points_to_visit = points_on_circumference_sorted(self.ai.enemy_start_locations[0].towards(
            self.ai.game_info.map_center, 2), self.ai.start_location, 12, n=14)

    def scout(self):
        scouting_probe = self.get_scouting_probe()
        if not scouting_probe:
            scouting_probe = self.assign_scouting_probe()
            if not scouting_probe:
                return

        if not scouting_probe.is_moving:
            for point in self.points_to_visit:
                scouting_probe.move(point, queue=True)

    def assign_scouting_probe(self):
        workers_tags = self.ai.strategy.workers_distribution.get_distant_mining_workers_tags()
        if not workers_tags:
            workers_tags = self.ai.strategy.workers_distribution.get_mineral_workers_tags()
        if workers_tags:
            workers = self.ai.workers.filter(lambda x: x.tag in workers_tags)
        else:
            workers = self.ai.units(unit.PROBE)
        if workers:
            scout = workers.closest_to(self.ai.enemy_start_locations[0])
            self.scout_tag = scout.tag
            return scout

    def get_scouting_probe(self):
        if self.scout_tag:
            scouting_probe = self.ai.workers.find_by_tag(self.scout_tag)
            return scouting_probe
