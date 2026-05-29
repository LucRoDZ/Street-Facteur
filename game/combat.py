import config

def check_melee_hit(attacker, targets):
    hit_targets = []
    for target in targets:
        offset = target.position.x - attacker.position.x
        if offset * attacker.facing > 0 and abs(offset) < config.ATTACK_RANGE and abs(target.y - attacker.y) < 1.5:
            hit_targets.append(target)
    return hit_targets

def apply_knockback(target, attacker, force):
    target_x = target.position.x if hasattr(target, 'position') else target.x
    attacker_x = attacker.position.x if hasattr(attacker, 'position') else attacker.x
    direction = 1 if target_x > attacker_x else -1
    target.velocity_x = direction * force
