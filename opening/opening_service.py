from opening.openings.four_gate import FourGate


class OpeningService:
    def __init__(self, ai):
        self.ai = ai

    def choose_opening(self):
        return FourGate
