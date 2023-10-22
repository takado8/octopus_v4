from sc2.constants import PROTOSS_TECH_REQUIREMENT
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.ids.unit_typeid import UnitTypeId as unit_id

from optimizer.creation_time_simulator import CreationTimeSimulator
from optimizer.income_simulator import IncomeSimulator

PRODUCTION_STRUCTURES_IDS = {unit_id.GATEWAY, unit_id.WARPGATE, unit_id.ROBOTICSFACILITY, unit_id.STARGATE,
                             unit_id.NEXUS}


class BuildOrderSimulator:
    def __init__(self, ai, max_duration=None):
        self.ai = ai
        self.income_simulator = IncomeSimulator(ai)
        self.creation_simulator = CreationTimeSimulator(ai)
        self.max_duration = max_duration
        self.created_units = {unit_id.PROBE: 12}
        self.units_in_creation = {}
        self.production_structures = {unit_id.NEXUS: 1}
        self.production_structures_busy = {}

    def simulate_build_order(self, build_order):
        self.cleanup()
        build_order = [unit_id(x) for x in build_order]
        simulation_time = 0
        for unit in build_order:
            # print('new unit.')
            self.collect_created_units(simulation_time)
            self.release_production(simulation_time)
            if self.max_duration and simulation_time >= self.max_duration:
                break

            if not self.is_tech_requirement_met(unit):
                tech_requirement = self.get_tech_requirement(unit)
                if tech_requirement in self.units_in_creation:
                    time_when_ready = min(self.units_in_creation[tech_requirement])
                    simulation_time = time_when_ready
                    self.collect_created_units(simulation_time)
                    self.release_production(simulation_time)
                else:
                    continue

            cost = self.income_simulator.get_unit_cost(unit)

            if cost[1] > 0 and unit_id.ASSIMILATOR not in self.created_units:
                continue

            if unit_id.ASSIMILATOR in self.created_units:
                assimilators_amount = self.created_units[unit_id.ASSIMILATOR]
                if assimilators_amount > 2:
                    assimilators_amount = 2
                gas_workers = 3 * assimilators_amount
            else:
                gas_workers = 0
            if gas_workers and cost[1] > 0:
                available_gas = self.income_simulator.get_available_gas(simulation_time, gas_workers)
                # print(f'gas: {available_gas}, spent: {self.income_simulator.spent_gas}')

                if available_gas < cost[1]:
                    time_till_available = self.income_simulator.get_time_till_gas_available(
                        cost[1], simulation_time, 3)
                    simulation_time += time_till_available
                    self.collect_created_units(simulation_time)
                    self.release_production(simulation_time)
            elif cost[1] > 0:
                continue
            available_workers = min(self.created_units[unit_id.PROBE] - gas_workers, 18)
            available_minerals = self.income_simulator.get_available_minerals(simulation_time,
                                                    available_workers)
            if available_minerals < cost[0]:
                time_till_available = self.income_simulator.get_time_till_minerals_available(
                    cost[0], simulation_time, available_workers)

                simulation_time += time_till_available

            creation_time = self.creation_simulator.get_unit_creation_time(unit)
            completion_time = simulation_time + creation_time

            units_trained_from = UNIT_TRAINED_FROM[unit]
            production_ready = None
            for unit_trained_from in units_trained_from:
                if unit_trained_from in PRODUCTION_STRUCTURES_IDS:
                    if unit_trained_from in self.production_structures:
                        if self.production_structures[unit_trained_from] > 0:
                            production_ready = True
                        else:
                            if unit_trained_from in self.production_structures_busy:
                                production_idling_time = min(self.production_structures_busy[unit_trained_from])
                                if unit_trained_from in self.units_in_creation and self.units_in_creation[unit_trained_from]:
                                    production_creation_time = min(self.units_in_creation[unit_trained_from])
                                    time_when_production_ready = min(production_creation_time, production_idling_time)
                                else:
                                    time_when_production_ready = production_idling_time
                                simulation_time = time_when_production_ready
                                self.collect_created_units(simulation_time)
                                self.release_production(simulation_time)
                                production_ready = True
                            else:
                                production_ready = False
                                continue
                    else:
                        production_ready = False
                        continue
                    if production_ready:
                        self.production_structures[unit_trained_from] -= 1
                        if unit_trained_from in self.production_structures_busy:
                            self.production_structures_busy[unit_trained_from].append(completion_time)
                        else:
                            self.production_structures_busy[unit_trained_from] = [completion_time]
                        break
            if production_ready is False:
                continue

            self.income_simulator.subtract_spent_minerals(cost[0])
            self.income_simulator.subtract_spent_gas(cost[1])
            # print(f'adding unit to creation: {unit}')
            if unit in self.units_in_creation:
                self.units_in_creation[unit].append(completion_time)
            else:
                self.units_in_creation[unit] = [completion_time]

        last_creation_time = simulation_time
        for pending_unit_id in self.units_in_creation:
            units_times = self.units_in_creation[pending_unit_id]
            if units_times:
                max_time = max(units_times)
                if max_time > last_creation_time:
                    last_creation_time = max_time

        if self.max_duration and last_creation_time > self.max_duration:
            last_creation_time = self.max_duration
        simulation_time = last_creation_time
        self.collect_created_units(simulation_time)
        self.release_production(simulation_time)
        # print(f'simulation time: {simulation_time}')
        # print(f'build: {build_order}\nsimulation time: {simulation_time}\ncreated_units: {self.created_units}'
        #       f'\nunits_in_creation: {self.units_in_creation}\nproduction_structures: {self.production_structures}'
        #       f'\nproduction_structures_busy: {self.production_structures_busy}')
        return self.count_units_value()

    def count_units_value(self):
        army_value = 0
        for unit_type in self.created_units:
            if unit_type == unit_id.STALKER:
                try:
                    unit_cost = self.ai.calculate_cost(unit_type)
                    army_value += (unit_cost.minerals + unit_cost.vespene) * self.created_units[unit_type]
                except Exception as ex:
                    print(ex)
                    print('cannot get unit value: {}'.format(unit_type))
        return army_value

    def collect_created_units(self, simulation_time):
        for pending_unit_id in self.units_in_creation:
            units_times = self.units_in_creation[pending_unit_id]
            not_ready = []
            for unit_completion_time in units_times:
                if unit_completion_time <= simulation_time:
                    # print(f'created: {pending_unit_id}')

                    if pending_unit_id in PRODUCTION_STRUCTURES_IDS:
                        if pending_unit_id in self.production_structures:
                            self.production_structures[pending_unit_id] += 1
                        else:
                            self.production_structures[pending_unit_id] = 1
                    else:
                        if pending_unit_id in self.created_units:
                            self.created_units[pending_unit_id] += 1
                        else:
                            self.created_units[pending_unit_id] = 1
                else:
                    # print(f'not ready created: {pending_unit_id}')

                    not_ready.append(unit_completion_time)
            self.units_in_creation[pending_unit_id] = not_ready

    def release_production(self, simulation_time):
        for busy_unit in self.production_structures_busy:
            units_times = self.production_structures_busy[busy_unit]
            not_ready = []
            for unit_idling_time in units_times:
                if unit_idling_time <= simulation_time:
                    # print(f'releasing: {busy_unit}')
                    if busy_unit in self.production_structures:
                        self.production_structures[busy_unit] += 1
                    else:
                        self.production_structures[busy_unit] = 1
                else:
                    # print(f'not ready: {busy_unit}')
                    not_ready.append(unit_idling_time)
            self.production_structures_busy[busy_unit] = not_ready

    def is_tech_requirement_met(self, unit_type_id):
        if unit_type_id in PROTOSS_TECH_REQUIREMENT:
            required_unit_id = PROTOSS_TECH_REQUIREMENT[unit_type_id]
            if required_unit_id not in self.created_units and required_unit_id not in self.production_structures:
                # print("cannot produce unit {} tech requirement is not met: {}".format(unit_type_id, required_unit_id))
                return False
        return True

    @staticmethod
    def get_tech_requirement(unit_type_id):
        return PROTOSS_TECH_REQUIREMENT[unit_type_id]

    def cleanup(self):
        self.income_simulator = IncomeSimulator(self.ai)
        self.creation_simulator = CreationTimeSimulator(self.ai)
        self.created_units = {unit_id.PROBE: 12}
        self.units_in_creation = {}
        self.production_structures = {unit_id.NEXUS: 1}
        self.production_structures_busy = {}
