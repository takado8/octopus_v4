import json
from collections import defaultdict

from matplotlib import pyplot as plt


class IncomeStatistics:
    def __init__(self, ai):
        self.ai = ai
        self.workers_amount = []
        self.income_rate = []
        self.last_log_time = 0

    def log(self):
        if self.last_log_time != self.ai.time:
            self.workers_amount.append(len(self.ai.workers))
            self.income_rate.append(self.ai.state.score.collection_rate_minerals)
            self.last_log_time = self.ai.time

    def eval_income_per_worker(self):
        workers_amount_income_dict = {}
        i = 0
        end_i = 0
        current_workers_amount = self.workers_amount[0]
        while end_i < len(self.income_rate):
            start_i = i
            while end_i < len(self.workers_amount) and self.workers_amount[i] == current_workers_amount:
                end_i += 1
                i += 1

            workers_amount_income_dict[current_workers_amount] = round(
                sum(self.income_rate[start_i:end_i]) / (end_i - start_i), 2)
            if i < len(self.workers_amount):
                current_workers_amount = self.workers_amount[i]
        return workers_amount_income_dict

    @staticmethod
    def write_dict_to_file(filename, data):
        try:
            with open(filename, 'a') as file:
                file.write(json.dumps(data) + '\n')
        except Exception as e:
            print(f"Error writing to file: {e}")

    @staticmethod
    def read_dict_from_file(filename):
        data = []
        try:
            with open(filename, 'r') as file:
                for line in file:
                    entry = json.loads(line)
                    data.append(entry)
        except Exception as e:
            print(f"Error reading from file: {e}")
        return data

    @staticmethod
    def plot_data(data):
        xs, ys = IncomeStatistics.calculate_average(data)
        for i in range(len(xs)):
            print(f'{xs[i]}: {ys[i]}')
        plt.figure()
        plt.plot(xs, ys)
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.title('Data Plot')
        plt.show()

    @staticmethod
    def calculate_average(data):
        x_to_y = defaultdict(list)
        for entry in data:
            for x, y in entry.items():
                x_to_y[x].append(y)

        x_values = list(x_to_y.keys())
        avg_y_values = [sum(y_values) / len(y_values) for y_values in x_to_y.values()]

        return x_values, avg_y_values