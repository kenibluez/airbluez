import math

import pygame

from airbluez.state.app_state import AppState


class ChordWheel:
    def __init__(self, center: tuple[int, int], radius: int = 150):
        self.center = center
        self.radius = radius
        self.roots = ["C", "G", "D", "A", "E", "B", "Gb", "Db", "Ab", "Eb", "Bb", "F"]
        self.num_segments = len(self.roots)
        self.segment_angle = 360 / self.num_segments

        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20, bold=True)

    def draw(self, surface: pygame.Surface, state: AppState):
        cx, cy = self.center

        # Draw the segments
        for i, root in enumerate(self.roots):
            start_angle = math.radians(i * self.segment_angle - 90 - (self.segment_angle / 2))
            end_angle = math.radians((i + 1) * self.segment_angle - 90 - (self.segment_angle / 2))

            # Determine segment color
            is_active = root == state.chord_root
            color = (0, 200, 100, 150) if is_active else (50, 50, 50, 100)

            # We use pygame.gfxdraw for filled polygons or just standard polygon math
            points = [(cx, cy)]
            # Approximate arc with lines
            for step in range(0, 11):
                theta = start_angle + (end_angle - start_angle) * (step / 10.0)
                px = int(cx + self.radius * math.cos(theta))
                py = int(cy + self.radius * math.sin(theta))
                points.append((px, py))

            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (200, 200, 200), points, 2)  # Outline

            # Draw text label in the middle of the segment
            mid_angle = math.radians(i * self.segment_angle - 90)
            tx = cx + (self.radius * 0.75) * math.cos(mid_angle)
            ty = cy + (self.radius * 0.75) * math.sin(mid_angle)

            text_color = (255, 255, 255) if is_active else (150, 150, 150)
            text_surf = self.font.render(root, True, text_color)
            text_rect = text_surf.get_rect(center=(tx, ty))
            surface.blit(text_surf, text_rect)
