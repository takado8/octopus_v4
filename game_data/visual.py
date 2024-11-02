from collections import deque

import cv2
import numpy as np
from sc2.bot_ai import BotAI
from sc2.position import Point2


class Visual:
    def __init__(self, ai: BotAI):
        print('map size: ' + str(ai.game_info.map_size))
        self.map_size = ai.game_info.map_size
        self.ai = ai
        self.magnification = 6
        self.game_map = self.initialize_map()
        self.shade_path = deque(maxlen=12)


    def render(self, units, enemy_units, scout=None):
        game_map = self.game_map.copy()
        if not scout:
            scout = units.furthest_to(self.ai.start_location)
        if scout:
            position = scout.position
            scout_x = round(position[0] * self.magnification)
            scout_y = round(position[1] * self.magnification)

            for shade_point, iteration in self.shade_path:
                iteration = 20 + self.ai.iteration - iteration
                color = (iteration + 20, iteration, iteration + 20)
                cv2.circle(img=game_map, center=shade_point, radius=round(scout.sight_range * self.magnification), color=color, thickness=-1)  # BGR
            if self.ai.iteration % 10 == 0:
                self.shade_path.append(((scout_x, scout_y), self.ai.iteration))
            cv2.circle(game_map, (scout_x, scout_y), round(scout.radius * self.magnification), (80, 255, 0), -1)  # BGR
            cv2.circle(game_map, (scout_x, scout_y), round(scout.sight_range * self.magnification), (80, 255, 0), 1)  # BGR
        # draw resources
        self.draw_resources(game_map)
        # draw units
        for unit in units:
            position = unit.position
            cv2.circle(game_map,(round(position[0] * self.magnification),round(position[1] * self.magnification)), round(unit.radius *  self.magnification),(50,200,0),-1)  # BGR
        for unit in enemy_units:
            position = unit.position
            cv2.circle(game_map,(round(position[0] * self.magnification),round(position[1] * self.magnification)), round(unit.radius *  self.magnification),(50,0,200),-1)  # BGR

        # flip horizontally to make our final fix in visual representation:
        flipped = cv2.flip(game_map,0)
        # resized = cv2.resize(flipped,dsize=None,fx=4,fy=4)

        cv2.imshow('Visual',flipped)
        cv2.waitKey(1)

    def initialize_map(self):
        game_map = np.zeros((self.map_size[1] * self.magnification, self.map_size[0] * self.magnification, 3), np.uint8)
        # draw non-traversable areas
        for y in range(0, self.map_size[1] * self.magnification):
            for x in range(0, self.map_size[0] * self.magnification):
                if not self.ai.in_pathing_grid(Point2((x / self.magnification, y / self.magnification))):
                    game_map[y][x] = (255, 255, 255)

        # draw enemy location
        center = (round(self.ai.enemy_start_locations[0].x * self.magnification), round(self.ai.enemy_start_locations[0].y * self.magnification))
        cv2.circle(img=game_map, center=center, radius=1, color=(50, 10, 255), thickness=-1)  # BGR
        cv2.circle(img=game_map, center=center, radius=round(5 * self.magnification), color=(50, 10, 255), thickness=1)  # BGR

        return game_map

    def draw_resources(self, game_map):
        for r in self.ai.mineral_field + self.ai.vespene_geyser:
            cv2.circle(game_map, (round(r.position.x * self.magnification), round(r.position.y * self.magnification)), round(r.radius *  self.magnification), (255, 0, 0), -1)  # BGR
        return game_map