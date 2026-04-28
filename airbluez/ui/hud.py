import pygame

from airbluez.state.app_state import AppState


class HUD:
    def __init__(self, width: int):
        self.width = width
        self.height = 40
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 24)

        # Instrument names matching our sample bank
        self.instruments = ["Pad", "Rhodes", "Piano", "Guitar"]

    def draw(self, surface: pygame.Surface, state: AppState):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with alpha
        surface.blit(overlay, (0, 0))

        play_status = "▶ PLAY" if state.play else "⏸ PAUSED"
        instrument = self.instruments[state.sample_id % len(self.instruments)]
        vol_pct = int(state.volume * 100)

        hud_text = f"{play_status}  |  Chord: {state.chord_root}{state.chord_quality}  |  Inst: {instrument}  |  Vol: {vol_pct}%"

        text_surface = self.font.render(hud_text, True, (255, 255, 255))
        surface.blit(text_surface, (20, 8))
