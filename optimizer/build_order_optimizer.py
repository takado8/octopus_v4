import random

from leap_ec import Representation
from leap_ec.algorithm import generational_ea
from leap_ec.real_rep.ops import mutate_gaussian

import leap_ec.ops as ops
from leap_ec.problem import FunctionProblem
import numpy as np


class BuildOrderOptimizer:
    def __init__(self, ai):
        self.ai = ai

    def evaluate_build_order(self, individual):
        pass

    def run(self):
        pop_size = 100
        final_pop = generational_ea(max_generations=600, pop_size=pop_size,
                                    problem=FunctionProblem(self.my_eval, True),
                                    representation=Representation(
                                        initialize=self.genome_init
                                    ),
                                    # The operator pipeline
                                    pipeline=[
                                        ops.tournament_selection,  # Select parents via tournament selection
                                        ops.clone,  # Copy them (just to be safe)
                                        mutate_gaussian(std=1, expected_num_mutations=1),
                                        # Basic mutation with a 1/L mutation rate
                                        ops.UniformCrossover(p_swap=0.4),
                                        # Crossover with a 40% chance of swapping each gene
                                        ops.evaluate,  # Evaluate fitness
                                        ops.pool(size=pop_size)  # Collect offspring into a new population
                                    ])
        print(max(final_pop))
        print(final_pop[:10])

    @staticmethod
    def my_eval(phenome):
        return sum(-4 * x**2 + 4 * x + 1 for x in phenome)

    @staticmethod
    def genome_init():
        return np.array([random.uniform(-5, 5) for _ in range(1)])


if __name__ == '__main__':
    import time
    start = time.time()
    opt = BuildOrderOptimizer(None)
    opt.run()
    stop = time.time()
    elapsed = stop - start
    print(f'Time: {elapsed}')
