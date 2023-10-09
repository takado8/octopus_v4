class Strategy:
    def __init__(self, ai):
        self.ai = ai

    async def execute(self):
        raise NotImplementedError()