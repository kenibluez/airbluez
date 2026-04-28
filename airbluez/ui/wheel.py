import math

import pygame

from airbluez.state.app_state import AppState


class ChordWheel:
    def __init__(self, center: tuple[int, int], radius: int = 150):
        self.center = center
        self.radius = radius
        # Same new array to match the mapper
        self.roots = ["C", "D", "E", "F", "G", "A", "B", "Db", "Eb", "Gb", "Ab", "Bb"]
        self.num_segments = len(self.roots)
        self.segment_angle = 360 / self.num_segments

        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20, bold=True)

    def draw(self, surface: pygame.Surface, state: AppState):
        cx, cy = self.center
        wheel_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for i, root in enumerate(self.roots):
            # Base angle starts at 180 degrees (Left) instead of -90 (Top)
            base_angle = i * self.segment_angle + 180
            start_angle = math.radians(base_angle - (self.segment_angle / 2))
            end_angle = math.radians(base_angle + (self.segment_angle / 2))

            is_active = root == state.chord_root
            color = (39, 231, 245, 120) if is_active else (40, 40, 40, 60)
            outline_color = (200, 200, 200, 80)

            points = [(cx, cy)]
            for step in range(0, 11):
                theta = start_angle + (end_angle - start_angle) * (step / 10.0)
                px = cx + self.radius * math.cos(theta)
                py = cy + self.radius * math.sin(theta)
                points.append((px, py))

            pygame.draw.polygon(wheel_surface, color, points)
            pygame.draw.polygon(wheel_surface, outline_color, points, 2)

            mid_angle = math.radians(base_angle)
            tx = cx + (self.radius * 0.75) * math.cos(mid_angle)
            ty = cy + (self.radius * 0.75) * math.sin(mid_angle)

            text_color = (255, 255, 255) if is_active else (150, 150, 150)
            text_surf = self.font.render(root, True, text_color)
            text_rect = text_surf.get_rect(center=(tx, ty))
            wheel_surface.blit(text_surf, text_rect)

        surface.blit(wheel_surface, (0, 0))
