from sc2.unit import Unit


class MicroABS:
    def __init__(self, name, ai):
        self.ai = ai
        self.name = name

    def in_grid(self, pos):
        try:
            if isinstance(pos, Unit):
                pos = pos.position
            if not self.ai.in_map_bounds(pos):
                return
            return self.ai.in_pathing_grid(pos)
        except:
            return False

    async def do_micro(self):
        raise NotImplementedError

    def __str__(self):
        return self.name