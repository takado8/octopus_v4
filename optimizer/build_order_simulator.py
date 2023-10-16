from sc2.ids.unit_typeid import UnitTypeId as unit_id


class BuildOrderSimulator:
    def income_function(self, time):
        pass

    @staticmethod
    def simulate_build_order(build_order):
        build_order = [unit_id(x) for x in build_order]
        gate_done = False
        cyber_done = False
        stalkers_amount = 0
        for unit in build_order:
            if unit == unit_id.GATEWAY:
                gate_done = True
            elif unit == unit_id.CYBERNETICSCORE:
                if gate_done:
                    cyber_done = True
            elif unit == unit_id.STALKER:
                if cyber_done:
                    stalkers_amount += 1
        return stalkers_amount
