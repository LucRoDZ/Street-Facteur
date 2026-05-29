from ursina import camera, Vec3, lerp, clamp, time
import config
from game.states import PlayerState

class CameraRig:
    def __init__(self):
        camera.orthographic = True
        camera.fov = config.CAM_BASE_FOV
        camera.position = Vec3(0, 3, -20)

    def update(self, players):
        active_players = [p for p in players if p.state != PlayerState.KO]
        if len(active_players) == 0:
            return
            
        if len(active_players) == 1:
            target_x = active_players[0].x
            target_fov = config.CAM_BASE_FOV
            camera.fov = lerp(camera.fov, target_fov, config.CAM_LERP_SPEED * time.dt)
        else:
            p1 = active_players[0]
            p2 = active_players[1]
            target_x = (p1.x + p2.x) / 2
            dist = abs(p1.x - p2.x)
            target_fov = clamp(config.CAM_BASE_FOV + dist * 0.4, config.CAM_MIN_FOV, config.CAM_MAX_FOV)
            camera.fov = lerp(camera.fov, target_fov, config.CAM_LERP_SPEED * time.dt)

        target_x = clamp(
            target_x,
            config.STAGE_LEFT + config.CAM_LEFT_CLAMP,
            config.STAGE_RIGHT - config.CAM_RIGHT_CLAMP
        )
                         
        camera.x = lerp(camera.x, target_x, config.CAM_LERP_SPEED * time.dt)
        camera.y = lerp(camera.y, 3.0, config.CAM_LERP_SPEED * time.dt)
