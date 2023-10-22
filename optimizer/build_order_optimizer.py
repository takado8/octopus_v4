import random
from typing import Iterator

from leap_ec import Representation
from leap_ec.algorithm import generational_ea
from leap_ec.real_rep.ops import mutate_gaussian

import leap_ec.ops as ops
from leap_ec.problem import FunctionProblem
import numpy as np
from leap_ec.util import wrap_curry
from sc2.ids.unit_typeid import UnitTypeId as unit_id

from optimizer.build_order_simulator import BuildOrderSimulator


def mutate(genome, mutations=1):
    def swap(idx, idx_diff):
        temp = genome[idx]
        next_gen_idx = idx + idx_diff
        genome[idx] = genome[next_gen_idx]
        genome[next_gen_idx] = temp

    def duplicate(idx, idx_2):
        genome[idx_2] = genome[idx]

    gen_last_idx = len(genome) - 1
    if mutations < 1:
        mutations = 1
    for _ in range(mutations):
        gene_idx = random.randint(0, gen_last_idx)
        if random.uniform(0, 1) > 0.5:
            if gene_idx == 0:
                swap(0, 1)
            elif gene_idx == gen_last_idx:
                swap(gene_idx, -1)
            else:
                if random.uniform(0, 1) > 0.5:
                    swap(0, 1)
                else:
                    swap(0, -1)
        else:
            duplicate(gene_idx, random.randint(0, gen_last_idx))
    return genome


@wrap_curry
@ops.iteriter_op
def mutation(next_individual: Iterator, mutations=1):
    while True:
        individual = next(next_individual)
        if mutations >= 1 or random.uniform(0, 1) < mutations:
            individual.genome = mutate(individual.genome, mutations=mutations)
        # invalidate fitness since we have new genome
            individual.fitness = None

        yield individual


class BuildOrderOptimizer:
    available_genes = [unit_id.GATEWAY, unit_id.CYBERNETICSCORE, unit_id.STALKER, unit_id.PROBE,
                       unit_id.ASSIMILATOR]
    genome_length = 40

    def __init__(self, ai):
        self.ai = ai
        self.build_order_simulator = BuildOrderSimulator(ai, max_duration=300)

    def evaluate_build_order(self, individual):
        return self.build_order_simulator.simulate_build_order(individual)

    def initialize_genome(self):
        genome = []
        # max_idx = len(self.available_genes) - 1
        for _ in range(self.genome_length):
            genome.append(random.choice(self.available_genes).value)
        return np.array(genome)

    def run(self):
        pop_size = 100
        final_pop = generational_ea(max_generations=150, pop_size=pop_size,
                                    problem=FunctionProblem(self.evaluate_build_order, True),
                                    representation=Representation(
                                        initialize=self.initialize_genome
                                    ),
                                    # The operator pipeline
                                    pipeline=[
                                        ops.tournament_selection,  # Select parents via tournament selection
                                        ops.clone,  # Copy them (just to be safe)
                                        # mutate_gaussian(std=1, expected_num_mutations=1),
                                        mutation(mutations=0.1),
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

