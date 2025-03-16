import random
from sc2 import maps
from sc2.unit import Unit
from sc2.data import Race, AIBuild, Difficulty, Result
from sc2.main import run_game
from sc2.player import Bot, Computer
# from test_bots.terran_stalker_defense import TerranStalkerDefense

from economy.income_statistics import IncomeStatistics
from machine_learning.sc2_actor.actor_bot import ActorBot
# from octopus_v4 import OctopusV4
from tests.bots.worker_rush import WorkerRushBot


def run(real_time=0):
    if real_time:
        real_time = True
    else:
        real_time = False

    maps_list = ["GoldenAura513AIE"]
    races = [Race.Protoss, Race.Zerg, Race.Terran]
    computer_builds = [AIBuild.Rush]
    # computer_builds = [AIBuild.Timing, AIBuild.Rush, AIBuild.Power, AIBuild.Macro]
    # computer_builds = [AIBuild.Timing]
    # computer_builds = [AIBuild.Air]
    # computer_builds = [AIBuild.Power]
    # computer_builds = [AIBuild.Macro]
    build = random.choice(computer_builds)

    # map_index = random.randint(0, 5)
    # race_index = random.randint(0, 2)
    # CheatMoney   VeryHard CheatInsane VeryEasy CheatMoney
    # a_map = maps_list[0]
    a_map = random.choice(maps_list)
    result = run_game(map_settings=maps.get(a_map), players=[
        Bot(race=Race.Protoss, ai=ActorBot(), name='actor'),
        Bot(race=Race.Protoss, ai=ActorBot(), name='Octopus'),
        # Bot(race=Race.Terran, ai=WorkerRushBot(), name='TerranStalkerDefense')
        # Computer(race=races[0], difficulty=Difficulty.Hard, ai_build=build)
    ], realtime=real_time)


if __name__ == '__main__':
    try:
        run(real_time=1)
    except Exception as e:
        print(e)
    # income = IncomeStatistics(None)
    # income.plot_data(income.read_dict_from_file('eval_data.json'))
