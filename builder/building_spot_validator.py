class BuildingSpotValidator:
    def __init__(self, ai):
        self.ai = ai
        # linear function coefficients for build spot validation
        self.validation_coefficients = {}

    def is_valid_location(self, x, y, expansion_location):
        """
        :return: True if location is outside of minerals and gas transport area in main base, False otherwise.
        """
        if expansion_location in self.validation_coefficients:
            coe_a1, coe_b1, coe_a2, coe_b2, r, linear_function = self.validation_coefficients[expansion_location]
        else:
            coe_a1, coe_b1, coe_a2, coe_b2, r, linear_function = self.compute_coefficients(expansion_location)
            self.validation_coefficients[expansion_location] = coe_a1, coe_b1, coe_a2, coe_b2, r, linear_function

        condition1 = self.in_circle(x, y, expansion_location, r)
        if not condition1:
            return True  # outside of circle is a valid location for sure
        condition2 = linear_function(x, y, coe_a1, coe_b1)
        if not condition2:
            return True
        condition3 = linear_function(x, y, coe_a2, coe_b2)
        if not condition3:
            return True
        return False

    def compute_coefficients(self, expansion_location):
        n = expansion_location
        vespenes = self.ai.vespene_geyser.closer_than(9, n)
        g1 = vespenes.pop(0).position
        g2 = vespenes.pop(0).position

        delta1 = (g1.x - n.x)
        if delta1 == 0:
            print('delta == 0 !')
            delta1 = 1
        coe_a1 = (g1.y - n.y) / delta1
        coe_b1 = n.y - coe_a1 * n.x

        delta2 = (g2.x - n.x)
        if delta2 == 0:
            print('delta == 0 !')
            delta2 = 1
        coe_a2 = (g2.y - n.y) / delta2
        coe_b2 = n.y - coe_a2 * n.x

        max_ = 0
        minerals = self.ai.mineral_field.closer_than(9, n)
        minerals.append(g1)
        minerals.append(g2)
        for field in minerals:
            d = n.distance_to(field)
            if d > max_:
                max_ = d
        r = int(max_) ** 2

        if self.line_less_than(minerals[0].position.x, minerals[0].position.y, coe_a1, coe_b1):
            linear_function = self.line_less_than
        else:
            linear_function = self.line_bigger_than

        return coe_a1, coe_b1, coe_a2, coe_b2, r, linear_function

    @staticmethod
    def in_circle(x, y, n, r):
        return (x - n.x) ** 2 + (y - n.y) ** 2 < r

    @staticmethod
    def line_less_than(x, y, a, b):
        return y < a * x + b

    @staticmethod
    def line_bigger_than(x, y, a, b):
        return y > a * x + b
