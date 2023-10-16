INCOME_AT_WORKER_COUNT = {12: 602.3945833333333,
                          13: 740.4170833333333,
                          14: 795.3775000000002,
                          15: 845.9104166666666,
                          16: 899.4545833333335,
                          17: 950.379583333333,
                          18: 974.5195833333332}


class IncomeSimulator:
    def __init__(self):
        self.spent_minerals = 0
        self.minerals_per_second = 15

    def get_available_minerals(self, time):
        return int(time * self.minerals_per_second - self.spent_minerals)

    def get_time_till_minerals_available(self, minerals_amount, time_now):
        return int((minerals_amount + self.spent_minerals) / self.minerals_per_second - time_now)

    def subtract_spent_minerals(self, minerals_amount):
        self.spent_minerals += minerals_amount
