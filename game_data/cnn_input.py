import json

import cv2
import numpy as np

class SC2InputGenerator:
    def __init__(self, input_size):
        self.input_size = input_size  # (H, W) window size

    def world_to_grid(self, x, y, relative_center, world_scale=1.0):
        """
        Converts world coordinates to grid indices for the input tensor.

        Args:
            x, y: World coordinates of the unit.
            relative_center: The (cx, cy) world coordinate that maps to the center of the grid.
            input_size: The (H, W) size of the input grid.
            world_scale: Scale factor to convert world distance to grid cells.

        Returns:
            (grid_x, grid_y): The coordinates in the input tensor.
        """
        H, W = self.input_size, self.input_size
        cx, cy = relative_center

        # Compute relative position
        rel_x = (x - cx) / world_scale
        rel_y = (y - cy) / world_scale

        # Convert to grid indices
        grid_x = int(W // 2 + rel_x)
        grid_y = int(H // 2 + rel_y)

        # Clamp to ensure valid indices
        grid_x = max(0, min(W - 1, grid_x))
        grid_y = max(0, min(H - 1, grid_y))

        return grid_x, grid_y

    def generate_input(self, own_units, enemy_units, unmovable_terrain, relative_center):
        """Creates an input tensor with explicit one-hot encoding for terrain and units."""
        C, H, W = 6, self.input_size, self.input_size  # (HP %, 4 one-hot channels, Weapon cooldown %)
        input_tensor = np.zeros((C, H, W), dtype=np.float32)

        center_x, center_y = relative_center

        # Initialize the entire battlefield as movable terrain
        input_tensor[4, :, :] = 1  # Movable terrain (default)

        # Encode own units
        for unit in own_units:
            grid_x, grid_y = self.world_to_grid(unit['x'], unit['y'], relative_center)
            if 0 <= grid_x < W and 0 <= grid_y < H:
                input_tensor[0, grid_y, grid_x] = unit['hp']  # HP %
                input_tensor[1, grid_y, grid_x] = 1  # Own unit (one-hot)
                input_tensor[4, grid_y, grid_x] = 0  # Not just movable terrain anymore
                input_tensor[5, grid_y, grid_x] = unit['cooldown']  # Weapon cooldown %

        # Encode enemy units
        for unit in enemy_units:
            grid_x, grid_y = self.world_to_grid(unit['x'], unit['y'], relative_center)
            if 0 <= grid_x < W and 0 <= grid_y < H:
                input_tensor[0, grid_y, grid_x] = unit['hp']  # HP %
                input_tensor[2, grid_y, grid_x] = 1  # Enemy unit (one-hot)
                input_tensor[4, grid_y, grid_x] = 0  # Not just movable terrain anymore
                input_tensor[5, grid_y, grid_x] = unit['cooldown']  # Weapon cooldown %

        # Encode unmovable terrain
        for pos in unmovable_terrain:
            grid_x, grid_y = self.world_to_grid(pos[0], pos[1], relative_center)
            if 0 <= grid_x < W and 0 <= grid_y < H:
                input_tensor[3, grid_y, grid_x] = 1  # Unmovable terrain (one-hot)
                input_tensor[4, grid_y, grid_x] = 0  # Not movable terrain anymore

        return input_tensor

    @staticmethod
    def visualize_input(input_tensor, magnification=10):
        """Displays the battlefield using OpenCV with color-coded units and terrain.

        Args:
            input_tensor: The (C, H, W) tensor representing the battlefield.
            magnification: Scaling factor for display size.
        """
        H, W = input_tensor.shape[1], input_tensor.shape[2]

        # Create a grayscale base where 255 = movable terrain, 0 = unmovable
        img = np.ones((H, W, 3), dtype=np.uint8) * 255  # Default white (movable terrain)

        # Unmovable terrain (black)
        img[input_tensor[3] == 1] = [0, 0, 0]

        # Own units (blue, brightness scaled by HP)
        own_units = input_tensor[1] == 1
        img[own_units, 0] = (255 * input_tensor[0][own_units]).astype(np.uint8)  # Blue channel
        img[own_units, 1] = 0  # Green channel
        img[own_units, 2] = 0  # Red channel

        # Enemy units (red, brightness scaled by HP)
        enemy_units = input_tensor[2] == 1
        img[enemy_units, 0] = 0  # Blue channel
        img[enemy_units, 1] = 0  # Green channel
        img[enemy_units, 2] = (255 * input_tensor[0][enemy_units]).astype(np.uint8)  # Red channel

        # Resize for better visibility
        img = cv2.resize(img, (W * magnification, H * magnification), interpolation=cv2.INTER_NEAREST)

        # Show the image
        flipped = cv2.flip(img, 0)
        cv2.imshow("SC2 Battlefield", flipped)
        cv2.waitKey(1)
        # cv2.destroyAllWindows()



if __name__ == '__main__':
    own_units = [{'x': 210, 'y': 210, 'hp': 0.8, 'cooldown': 0.2}]
    enemy_units = [{'x': 215, 'y': 217, 'hp': 0.6, 'cooldown': 0.5}]
    unmovable_terrain = [(211, 216), (210, 216)]
    relative_center = (216, 216)
    input_size = 32

    generator = SC2InputGenerator(input_size)
    input_tensor = generator.generate_input(own_units, enemy_units, unmovable_terrain, relative_center)
    generator.visualize_input(input_tensor)