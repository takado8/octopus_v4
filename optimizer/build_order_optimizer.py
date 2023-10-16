import random

from leap_ec import Representation
from leap_ec.algorithm import generational_ea
from leap_ec.real_rep.ops import mutate_gaussian

import leap_ec.ops as ops
from leap_ec.problem import FunctionProblem
import numpy as np
from sc2.ids.unit_typeid import UnitTypeId as unit_id

from optimizer.build_order_simulator import BuildOrderSimulator


class BuildOrderOptimizer:
    available_genes = [unit_id.GATEWAY, unit_id.CYBERNETICSCORE, unit_id.STALKER]
    genome_length = 20

    def __init__(self, ai):
        self.ai = ai

    @staticmethod
    def evaluate_build_order(individual):
        return BuildOrderSimulator.simulate_build_order(individual)

    def initialize_genome(self):
        genome = []
        # max_idx = len(self.available_genes) - 1
        for _ in range(self.genome_length):
            genome.append(random.choice(self.available_genes).value)
        return np.array(genome)

    def mutation(self):
        pass

    def run(self):
        pop_size = 100
        final_pop = generational_ea(max_generations=100, pop_size=pop_size,
                                    problem=FunctionProblem(self.evaluate_build_order, True),
                                    representation=Representation(
                                        initialize=self.initialize_genome
                                    ),
                                    # The operator pipeline
                                    pipeline=[
                                        ops.tournament_selection,  # Select parents via tournament selection
                                        ops.clone,  # Copy them (just to be safe)
                                        # mutate_gaussian(std=1, expected_num_mutations=1),
                                        # Basic mutation with a 1/L mutation rate
                                        ops.UniformCrossover(p_swap=0.4),
                                        # Crossover with a 40% chance of swapping each gene
                                        ops.evaluate,  # Evaluate fitness
                                        ops.pool(size=pop_size)  # Collect offspring into a new population
                                    ])
        best = max(final_pop)
        print(best)
        print([unit_id(x) for x in best.genome])

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
    print(opt.initialize_genome())
    opt.run()
    stop = time.time()
    elapsed = stop - start
    print(f'Time: {elapsed}')
