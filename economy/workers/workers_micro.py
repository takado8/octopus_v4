from sc2.ids.unit_typeid import UnitTypeId as unit


class WorkersMicro:
    def __init__(self, ai):
        self.ai = ai

    def execute(self):
        workers = self.ai.workers
        enemy = self.ai.enemy_units()
        enemy.extend(self.ai.enemy_structures(unit.BUNKER))
        if enemy:
            for worker in workers:
                close_enemy = enemy.closer_than(16, worker)
                if close_enemy and worker.shield_percentage < 1 or close_enemy.amount >= 3 or \
                        close_enemy.filter(lambda x: x.type_id in {unit.WIDOWMINE, unit.WIDOWMINEBURROWED} and
                                     x.distance_to(worker) <= 6):
                    safe_townhall = self.ai.townhalls.filter(lambda x: not enemy.closer_than(16, x).exists)
                    if self.ai.townhalls.amount == 1 or not safe_townhall.exists:
                        worker.move(worker.position.towards(enemy.closest_to(worker), -6))
                    else:
                        worker.gather(self.ai.mineral_field.closest_to(safe_townhall.closest_to(worker)))
