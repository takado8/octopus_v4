
class CreationTimeSimulator:
    def __init__(self, ai):
        self.ai = ai

    def get_unit_creation_time(self, unit_type_id):
        unit_type_data = self.ai._game_data.units[unit_type_id.value]
        return round(unit_type_data.cost.time / 22.4)
