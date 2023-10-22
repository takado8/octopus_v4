MINERALS_INCOME_AT_WORKER_COUNT = {
    6: 300,
    7: 350,
    8: 400,
    9: 450,
    10: 500,
    11: 550,
    12: 600,
    13: 740,
    14: 795,
    15: 845,
    16: 900,
    17: 950,
    18: 975}

GAS_INCOME_AT_WORKER_COUNT = {0: 0, 1: 60, 2: 125, 3: 160, 6: 320}


class IncomeSimulator:
    def __init__(self, ai):
        self.spent_minerals = 0
        self.spent_gas = 0
        self.ai = ai

    def get_available_gas(self, time, workers_amount):
        gas_per_second = round(GAS_INCOME_AT_WORKER_COUNT[workers_amount] / 60)
        return int(time * gas_per_second - self.spent_gas)

    def get_available_minerals(self, time, workers_amount):
        minerals_per_second = round(MINERALS_INCOME_AT_WORKER_COUNT[workers_amount] / 60)
        return int(time * minerals_per_second - self.spent_minerals)

    def get_time_till_minerals_available(self, minerals_amount, time_now, workers_amount):
        minerals_per_second = round(MINERALS_INCOME_AT_WORKER_COUNT[workers_amount] / 60)
        return int((minerals_amount + self.spent_minerals) / minerals_per_second - time_now)

    def get_time_till_gas_available(self, gas_amount, time_now, workers_amount):
        gas_per_second = round(GAS_INCOME_AT_WORKER_COUNT[workers_amount] / 60)
        return int((gas_amount + self.spent_gas) / gas_per_second - time_now)

    def subtract_spent_minerals(self, minerals_amount):
        self.spent_minerals += minerals_amount

    def subtract_spent_gas(self, gas_amount):
        self.spent_gas += gas_amount

    def get_unit_cost(self, unit_type_id):
        unit_type_data = self.ai._game_data.units[unit_type_id.value]
        return unit_type_data.cost.minerals, unit_type_data.cost.vespene
