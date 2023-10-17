INCOME_AT_WORKER_COUNT = {12: 600,
                          13: 740,
                          14: 795,
                          15: 845,
                          16: 900,
                          17: 950,
                          18: 975}


class IncomeSimulator:
    def __init__(self, ai):
        self.spent_minerals = 0
        self.ai = ai

    def get_available_minerals(self, time, workers_amount):
        minerals_per_second = round(INCOME_AT_WORKER_COUNT[workers_amount] / 60)
        return int(time * minerals_per_second - self.spent_minerals)

    def get_time_till_minerals_available(self, minerals_amount, time_now, workers_amount):
        minerals_per_second = round(INCOME_AT_WORKER_COUNT[workers_amount] / 60)
        return int((minerals_amount + self.spent_minerals) / minerals_per_second - time_now)

    def subtract_spent_minerals(self, minerals_amount):
        self.spent_minerals += minerals_amount

    def get_unit_cost(self, unit_type_id):
        unit_type_data = self.ai._game_data.units[unit_type_id.value]
        return unit_type_data.cost[0], unit_type_data.cost[1]