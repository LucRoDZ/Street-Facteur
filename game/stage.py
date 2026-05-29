from ursina import Entity, color
import config

class Stage:
    def __init__(self):
        # Buildings layer — 3D quad that follows camera_x each frame
        self.bg_buildings = Entity(
            model='quad',
            scale=(40, 12),
            color=color.rgb(60, 60, 90),
            position=(0, 3, 15)
        )

        # Street ambiance layer
        self.bg_street = Entity(
            model='quad',
            scale=(40, 4),
            color=color.rgb(50, 50, 50),
            position=(0, -0.5, 12)
        )

        # Ground
        self.ground = Entity(
            model='cube',
            scale=(55, 0.5, 2),
            position=(22, -0.25, 0),
            color=color.rgb(45, 45, 45),
            collider='box'
        )

        # Trottoir lines
        for i in range(5):
            Entity(
                model='cube',
                scale=(0.05, 0.05, 0.6),
                color=color.rgb(80, 80, 80),
                position=(8 + i * 8, 0.02, 0)
            )

        # Boundary walls — invisible, only for reference (no collider)
        self.wall_left = Entity(
            model='cube',
            scale=(0.5, 10, 2),
            position=(config.STAGE_LEFT, 4, 0),
            enabled=False
        )
        self.wall_right = Entity(
            model='cube',
            scale=(0.5, 10, 2),
            position=(config.STAGE_RIGHT, 4, 0),
            enabled=False
        )

    def update(self, camera_x):
        center = config.STAGE_RIGHT / 2
        # Follow camera with subtle parallax offset
        self.bg_buildings.x = camera_x + (camera_x - center) * 0.03
        self.bg_street.x    = camera_x + (camera_x - center) * 0.06
