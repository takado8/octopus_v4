from sc2.constants import PROTOSS_TECH_REQUIREMENT
from sc2.ids.unit_typeid import UnitTypeId as unit_id

from optimizer.creation_time_simulator import CreationTimeSimulator
from optimizer.income_simulator import IncomeSimulator


class BuildOrderSimulator:
    def __init__(self, ai):
        self.ai = ai
        self.income_simulator = IncomeSimulator(ai)
        self.creation_simulator = CreationTimeSimulator(ai)
        self.created_units = {}
        self.units_in_creation = {}

    def income_function(self, time):
        pass

    def simulate_build_order(self, build_order):
        build_order = [unit_id(x) for x in build_order]
        simulation_time = 0
        for unit in build_order:
            for pending_unit_id in self.units_in_creation:
                units_times = self.units_in_creation[pending_unit_id]
                not_ready = []
                for unit_completion_time in units_times:
                    if unit_completion_time <= simulation_time:
                        if pending_unit_id in self.created_units:
                            self.created_units[pending_unit_id] += 1
                        else:
                            self.created_units[pending_unit_id] = 1
                    else:
                        not_ready.append(unit_completion_time)
                self.units_in_creation[pending_unit_id] = not_ready

            if not self.is_tech_requirement_met(unit):
                tech_requirement = self.get_tech_requirement(unit)
                if tech_requirement in self.units_in_creation:
                    time_when_ready = min(self.units_in_creation[tech_requirement])
                    simulation_time = time_when_ready
                else:
                    continue
            available_minerals = self.income_simulator.get_available_minerals(simulation_time,
                                                                        self.created_units[unit_id.PROBE])
            cost = self.income_simulator.get_unit_cost(unit)
            if available_minerals < cost[0]:
                time_till_available = self.income_simulator.get_time_till_minerals_available(
                    cost[0], simulation_time, self.created_units[unit_id.PROBE])

                simulation_time += time_till_available
                self.income_simulator.subtract_spent_minerals(cost[0])

                creation_time = self.creation_simulator.get_unit_creation_time(unit)
                completion_time = simulation_time + creation_time

                if unit in self.units_in_creation:
                    self.units_in_creation[unit].append(completion_time)
                else:
                    self.units_in_creation[unit] = [completion_time]

    def is_tech_requirement_met(self, unit_type_id):
        if unit_type_id in PROTOSS_TECH_REQUIREMENT:
            required_unit_id = PROTOSS_TECH_REQUIREMENT[unit_type_id]
            if required_unit_id not in self.created_units:
                return False
                # print("cannot produce unit {} tech requirement is not met: {}".format(unit_type, unit_info_id))
        return True

    @staticmethod
    def get_tech_requirement(unit_type_id):
        return PROTOSS_TECH_REQUIREMENT[unit_type_id]
