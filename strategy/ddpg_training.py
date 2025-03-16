import asyncio

from builder.validation_level_enum import Validation
from game_data.cnn_input import SC2InputGenerator
from micro.stalker import StalkerBlinkMicro
from strategy.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId as unit_id
from sc2.ids.upgrade_id import UpgradeId as upgrade
from sc2.ids.ability_id import AbilityId

action_dict = {'pass': 0, 'attack': 1}


class DDPGTraining(Strategy):
    def __init__(self, ai):
        super().__init__(ai)
        self.pylons_out = False
        self.expansion_locations = None
        self.natural_location = None
        self.micro = StalkerBlinkMicro(ai)
        self.attack = False
        self.last_attack_time_start = 0
        self.last_attack_time_stop = 0
        self.lost_minerals_before_fight = 0
        self.lost_gas_before_fight = 0
        input_size = 64
        self.generator = SC2InputGenerator(input_size, ai)

    async def execute(self):
        if not self.expansion_locations:
            self.expansion_locations = sorted(self.ai.expansion_locations_list, key=lambda x: self.ai.start_location.distance_to(x))
            self.natural_location = self.expansion_locations[1]
        all_tasks = await asyncio.gather(
            self.handle_workers(),
        )
        if self.ai.workers.amount < 20:
            if self.ai.townhalls.idle.exists:
                self.ai.train(unit_id.PROBE)

        if not self.pylons_out and self.ai.supply_left < 3 and not self.ai.already_pending(unit_id.PYLON):
            if self.ai.can_afford(unit_id.PYLON):
                next_pylon_position = await self.pylon_builder.get_next_pylon_position()
                if next_pylon_position:
                    await self.builder.build(unit_id.PYLON, next_pylon_position, validation=Validation.NONE)
                else:
                    self.pylons_out = True
        cyber = self.ai.structures(unit_id.CYBERNETICSCORE)

        gateways = self.ai.structures({unit_id.GATEWAY, unit_id.WARPGATE})
        if (not gateways.exists or cyber.exists and gateways.amount < 4) and not self.ai.already_pending(unit_id.GATEWAY):
            await self.builder.build(unit_id.GATEWAY, self.ai.start_location)

        for gateway in self.ai.structures(unit_id.GATEWAY).ready:
            abilities = await self.ai.get_available_abilities(gateway)
            if AbilityId.MORPH_WARPGATE in abilities:
                gateway(AbilityId.MORPH_WARPGATE)

        if self.ai.structures({unit_id.GATEWAY, unit_id.WARPGATE}).ready.exists and not self.ai.already_pending(unit_id.CYBERNETICSCORE) and not self.ai.structures(unit_id.CYBERNETICSCORE).exists:
            await self.builder.build(unit_id.CYBERNETICSCORE, self.ai.start_location)
        assimilators = self.ai.structures(unit_id.ASSIMILATOR)
        if self.ai.structures({unit_id.GATEWAY, unit_id.WARPGATE}).exists and not self.ai.already_pending(unit_id.ASSIMILATOR) and assimilators.amount < 2:
            await self.ai.build(unit_id.ASSIMILATOR, self.ai.vespene_geyser.closest_n_units(self.ai.start_location, 2).filter(lambda x: assimilators.amount == 0 or assimilators.closest_to(x).distance_to(x) > 5).first)

        if cyber.exists:
            if upgrade.WARPGATERESEARCH not in self.ai.state.upgrades and \
                    not self.ai.already_pending_upgrade(upgrade.WARPGATERESEARCH) and \
                    self.ai.can_afford(upgrade.WARPGATERESEARCH):
                cyber.random.research(upgrade.WARPGATERESEARCH)


        if not self.attack and cyber.ready.exists and self.ai.units(unit_id.STALKER).amount < 7 and self.ai.can_afford(unit_id.STALKER):
            self.ai.train(unit_id.STALKER)


        if self.ai.army.amount > 6 and self.ai.time - self.last_attack_time_stop > 40 and not self.attack:
            self.attack = True
            self.last_attack_time_start = self.ai.time
            self.lost_minerals_before_fight = self.ai.state.score.lost_minerals_army
            self.lost_gas_before_fight = self.ai.state.score.lost_vespene_army
            print(f'Attacking at t={self.ai.time}')
        if self.ai.time - self.last_attack_time_start > 60 and self.attack:
            self.attack = False
            self.last_attack_time_stop = self.ai.time
            lost_minerals = self.ai.state.score.lost_minerals_army - self.lost_minerals_before_fight
            lost_gas = self.ai.state.score.lost_vespene_army - self.lost_gas_before_fight
            print(f'Stop attacking at t={self.ai.time}')
            print(f'stalkers amount: {self.ai.army.amount}')
            print(f'losses: minerals: {lost_minerals} gas: {lost_gas}')


        if self.attack:
            for stalker in self.ai.army:
                if not self.ai.enemy_units.filter(lambda x: x.distance_to(stalker) < 12).exists and stalker.distance_to(self.ai.game_info.map_center) > 7:
                    stalker.attack(self.ai.game_info.map_center)
            await self.micro.do_micro()
        else:
            for stalker in self.ai.army:
                if stalker.distance_to(self.ai.start_location) > 10:
                    stalker.move(self.ai.start_location)
        if (self.ai.minerals < 125 or self.ai.vespene < 50) and self.ai.time > 300:
            print(f'Exiting after {self.ai.time}s')
            exit(7)

        own_units = [{'x': stalker.position.x, 'y': stalker.position.y, 'hp': stalker.shield_health_percentage, 'cooldown': stalker.weapon_cooldown} for stalker in self.ai.army]
        enemy_units = [{'x': enemy.position.x, 'y': enemy.position.y, 'hp': enemy.shield_health_percentage} for enemy in self.ai.enemy_units]

        if self.ai.start_location == (170.5, 67.5):
            input_tensors = [self.generator.generate_input(own_units, enemy_units, (stalker.position.x, stalker.position.y)) for stalker in self.ai.army]
            if input_tensors:
                self.generator.visualize_input(input_tensors[0])
