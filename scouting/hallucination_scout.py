from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2

from scouting.enemy_economy import *

LEAP_SIZE = 10

class Scouting:
    SCOUTING_COOLDOWN = 30

    def __init__(self, ai_object, enemy_economy):
        self.number_of_scoutings_done = 0
        self.ai: BotAI = ai_object
        self.scouting_index = -1
        self.scouting_positions = []
        self.scouting_positions_on_end = []
        self.enemy_economy: EnemyEconomy = enemy_economy
        self.last_scouting_time = 0
        self.last_print_time = 0
        self.visited_positions_count = {}
        self.scouting_active_after_s = 0
        self.enemy_value_lost_cached = 0
        self.killed_units_diff_cached = 0
        self.enemy_main_base_down = False

    def get_movement(self, scout, direction):
        p = scout.position
        if direction == 'UP':
            return Point2((p.x, p.y + LEAP_SIZE))
        elif direction == 'DOWN':
            return Point2((p.x, p.y - LEAP_SIZE))
        elif direction == 'LEFT':
            return Point2((p.x - LEAP_SIZE, p.y))
        elif direction == 'RIGHT':
            return Point2((p.x + LEAP_SIZE, p.y))
        elif direction == 'UP-RIGHT':
            return Point2((p.x + LEAP_SIZE, p.y + LEAP_SIZE))
        elif direction == 'UP-LEFT':
            return Point2((p.x - LEAP_SIZE, p.y + LEAP_SIZE))
        elif direction == 'DOWN-RIGHT':
            return Point2((p.x + LEAP_SIZE, p.y - LEAP_SIZE))
        elif direction == 'DOWN-LEFT':
            return Point2((p.x - LEAP_SIZE, p.y - LEAP_SIZE))
        else:
            return None  # Return None if direction is invalid

    def get_possible_movements(self, scout):
        p = scout.position
        return {
            'UP': Point2((p.x, p.y + LEAP_SIZE)),
            'DOWN': Point2((p.x, p.y - LEAP_SIZE)),
            'LEFT': Point2((p.x - LEAP_SIZE, p.y)),
            'RIGHT': Point2((p.x + LEAP_SIZE, p.y)),
            'UP-RIGHT': Point2((p.x + LEAP_SIZE, p.y + LEAP_SIZE)),
            'UP-LEFT': Point2((p.x - LEAP_SIZE, p.y + LEAP_SIZE)),
            'DOWN-RIGHT': Point2((p.x + LEAP_SIZE, p.y - LEAP_SIZE)),
            'DOWN-LEFT': Point2((p.x - LEAP_SIZE, p.y - LEAP_SIZE))
        }
        # Define potential moves as tuples
        # moves = {
        #     'UP': (p.x, p.y + LEAP_SIZE),
        #     'DOWN': (p.x, p.y - LEAP_SIZE),
        #     'LEFT': (p.x - LEAP_SIZE, p.y),
        #     'RIGHT': (p.x + LEAP_SIZE, p.y),
        #     'UP-RIGHT': (p.x + LEAP_SIZE, p.y + LEAP_SIZE),
        #     'UP-LEFT': (p.x - LEAP_SIZE, p.y + LEAP_SIZE),
        #     'DOWN-RIGHT': (p.x + LEAP_SIZE, p.y - LEAP_SIZE),
        #     'DOWN-LEFT': (p.x - LEAP_SIZE, p.y - LEAP_SIZE)
        # }

        # Filter moves that are within the map boundaries
        # valid_moves = {
        #     direction: Point2((x, y))
        #     for direction, (x, y) in moves.items()
            # if 0 <= x < self.ai.game_info.map_size.width and 0 <= y < self.ai.game_info.map_size.height
        # }
        # return valid_moves

    async def scan_middle_game(self, direction=None):
        self.gather_enemy_info()

        if self.ai.time < self.scouting_active_after_s:
            return
        if self.ai.time - self.last_scouting_time > self.SCOUTING_COOLDOWN:
            if self.create_scout():
                self.last_scouting_time = self.ai.time

        scouts = self.ai.units(unit.PHOENIX).filter(lambda z: z.is_hallucination)
        if scouts.exists:
            # if BASES not in self.enemy_economy.py.enemy_info or len(self.scouting_positions) <\
            #         len(self.enemy_economy.py.enemy_info[BASES]) + 2:
            if direction:
                for scout in scouts:
                    scout.move(self.get_movement(scout, direction))
                return
            self.scouting_positions.clear()
            self.scouting_positions = await self.create_scouting_positions_list()
            enemy = self.ai.enemy_units + self.ai.enemy_structures
            if enemy:
                threats = enemy.filter(lambda x: x.can_attack_air or x.type_id == unit.BUNKER)
                if threats:
                    for scout in scouts:
                        threats = threats.closer_than(12, scout)
                        close_threats = threats.closer_than(7, scout)
                        if close_threats:
                            scout.move(scout.position.towards(close_threats.closest_to(scout), -10))
                        elif threats:
                            center1 = Point2.center([t.position for t in threats] + [scout.position,
                                                            self.scouting_positions[self.scouting_index]])
                            center2 = Point2.center([scout.position, self.scouting_positions[self.scouting_index]])
                            dodge_position = center1.position.towards(center2, 9)
                            scout.move(dodge_position)

            for scout in scouts.filter(lambda x: x.is_idle or
                    (x.distance_to(self.scouting_positions[self.scouting_index]) <= 8)
                    if self.scouting_index < len(self.scouting_positions) else False):
                if self.scouting_index < len(self.scouting_positions):
                    position = self.scouting_positions[self.scouting_index]
                    if scout.distance_to(position) <= 8:
                        if position not in self.visited_positions_count:
                            self.visited_positions_count[position] = 1
                        else:
                            self.visited_positions_count[position] += 1
                        if enemy.exists and enemy.closer_than(14, position).amount >= 5:
                            self.number_of_scoutings_done += 1
                            await self.print_info()
                        self.scouting_index += 1

                else:
                    self.scouting_index = 0
                if len(self.scouting_positions) > 0 and self.scouting_index < len(self.scouting_positions):
                    scout.move(self.scouting_positions[self.scouting_index])
                else:
                    self.scouting_index = 0

    def clear_units(self):
        if self.ai.iteration % 1000 == 0:
            diff = self.enemy_economy.lost_units_value - self.enemy_value_lost_cached
            if diff > 1000:
                enemy_value = self.enemy_economy.army_value
                estimated = enemy_value - diff
                self.enemy_economy.enemy_army_value_estimated = estimated
                self.enemy_economy.clear_category(MILITARY)
                self.enemy_value_lost_cached = self.enemy_economy.lost_units_value
                self.killed_units_diff_cached = diff
                print('clearing units')


    def gather_enemy_info(self):
        self.clear_units()
        # bases
        enemy_bases = self.ai.enemy_structures.filter(lambda x: x.type_id in self.ai.bases_ids and x.is_visible)
        self.enemy_economy.add_units_to_enemy_info(BASES, enemy_bases)
        # production (only terran for now)
        terran_production_ids = {unit.BARRACKS, unit.FACTORY, unit.STARPORT}
        terran_production_buildings = self.ai.enemy_structures.filter(lambda x: x.type_id in terran_production_ids and
                                                                                  x.is_visible and not x.is_snapshot)
        self.enemy_economy.add_units_to_enemy_info(PRODUCTION, terran_production_buildings)
        # military units
        excluded = {unit.BROODLING, unit.OVERLORD, unit.OVERSEER, unit.ADEPTPHASESHIFT, unit.OVERLORDCOCOON,
                    unit.OVERLORDTRANSPORT, unit.WARPPRISM, unit.WARPPRISMPHASING, unit.OBSERVER}
        enemy_military_units = self.ai.enemy_units.filter(lambda x: x.type_id not in self.ai.workers_ids and
                                                                      x.type_id not in self.ai.units_to_ignore
                                                                      and x.type_id not in excluded and x.is_visible
                                                            and not x.is_snapshot and not x.is_hallucination)
        self.enemy_economy.add_units_to_enemy_info(MILITARY, enemy_military_units)

        if self.enemy_main_base_down or (
                self.ai.army.closer_than(17, self.ai.enemy_start_locations[0]).amount > 7 and
                (not self.ai.enemy_structures.exists or self.ai.enemy_structures.closer_than(20,
                                                                    self.ai.enemy_start_locations[0]).amount < 3)):
            if not self.enemy_main_base_down:
                print('enemy main base down.')
                self.enemy_main_base_down = True

    async def create_scouting_positions_list(self):
        scouting_positions = []
        # enemy_start_location = self.ai.enemy_start_locations[0]
        for expansion in self.ai.expansion_locations_list:
            if not self.ai.structures.closer_than(7, expansion).exists:
                scouting_positions.append(expansion)

        scouting_positions = sorted(scouting_positions, key=lambda x: self.ai.enemy_start_locations[0].distance_to(x))
        # position_distance_list = []
        # for expansion in scouting_positions:
        #     distance = await self.ai._client.query_pathing(enemy_start_location, expansion)
        #     if distance is not None:
        #         position_distance_list.append((distance, expansion))
        #
        # scouting_positions = sorted(position_distance_list, key=lambda x: x[0])
        # scouting_positions = [x for _, x in scouting_positions]
        if BASES in self.enemy_economy.enemy_info:
            most_distant_base_idx = len(self.enemy_economy.enemy_info[BASES]) + 2
        else:
            most_distant_base_idx = 3

        while most_distant_base_idx >= len(scouting_positions):
            most_distant_base_idx -= 1

        scouting_positions = scouting_positions[:most_distant_base_idx]
        # return scouting_positions
        return sorted(scouting_positions, key=lambda x: (self.visited_positions_count[x]
                                    if x in self.visited_positions_count else 0, scouting_positions.index(x)))

    def create_scout(self):
        sentries = self.ai.army(unit.SENTRY).ready
        if sentries.exists:
            sentries = sorted(sentries.filter(lambda z: z.energy >= (75 if self.number_of_scoutings_done < 5 else 150)),
                              key=lambda sent: sent.energy, reverse=True)

            for sentry in sentries:
                sentry(AbilityId.HALLUCINATION_PHOENIX)
                # self.number_of_scoutings_done += 1
                return True

    def scan_on_end(self):
        scouts = self.ai.units(unit.PHOENIX).filter(lambda z: z.is_hallucination)
        if scouts.amount < 3:
            snts = self.ai.army(unit.SENTRY)
            if snts.exists:
                snts = self.ai.army(unit.SENTRY).filter(lambda z: z.energy >= 75)
                if snts:
                    for se in snts:
                        se(AbilityId.HALLUCINATION_PHOENIX)
            else:
                scouts = self.ai.units({unit.WARPPRISM, unit.OBSERVER})
                if not scouts.exists:
                    scouts = self.ai.army.filter(lambda z: z.is_flying and int(str(z.tag)[-1]) % 3 == 0)
                    if not scouts.exists:
                        scouts = self.ai.units(unit.PROBE).closest_n_units(self.ai.enemy_start_locations[0], 3)
                        if not scouts.exists:
                            scouts = self.ai.units.closest_n_units(self.ai.enemy_start_locations[0], 3)
        if scouts.exists:
            self.scouting_positions_on_end.clear()
            for exp in self.ai.expansion_locations_list:
                if not self.ai.structures.closer_than(7, exp).exists:
                    self.scouting_positions_on_end.append(exp)
            if len(self.scouting_positions_on_end) < 2:
                self.scouting_positions_on_end.extend(self.ai.expansion_locations_list)
            self.scouting_positions_on_end = sorted(self.scouting_positions_on_end,
                                                    key=lambda x: self.ai.enemy_start_locations[0].distance_to(x))
            for px in scouts.idle:
                if self.scouting_index >= len(self.scouting_positions_on_end):
                    self.scouting_index = 0
                if self.scouting_index < len(self.scouting_positions_on_end):
                    px.move(self.scouting_positions_on_end[self.scouting_index])
                    self.scouting_index += 1
                else:
                    self.scouting_positions_on_end.extend(self.ai.expansion_locations_list)

    async def print_info(self):
        msg = "enemy army value {}".format(self.ai.strategy.enemy_economy.army_value)
        print(msg)
        await self.ai.chat_send(msg)
