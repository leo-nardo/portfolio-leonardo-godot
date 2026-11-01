class_name Player
extends CharacterBody2D
## Personagem. Movimento lateral; a intenção vem do PlayerInput.
## Visual: ciclo de andar de 14 poses (game/art/characters/leo_v3/andar). Sem braços por enquanto.
## A versão anterior (rig com braços, prancheta e rosto trocável) está em art_src/player_antigo/.

const SPEED := 420.0
const ACCELERATION := 2600.0
const GRAVITY := 2400.0

## Falso durante diálogos/cutscenes: trava o controle.
var controllable := true

@onready var _input: PlayerInput = $PlayerInput
@onready var _sprite: AnimatedSprite2D = $Visual/Sprite


func _physics_process(delta: float) -> void:
	var dir := _input.read_direction(global_position.x) if controllable else 0.0
	velocity.x = move_toward(velocity.x, dir * SPEED, ACCELERATION * delta)
	if not is_on_floor():
		velocity.y += GRAVITY * delta
	move_and_slide()
	if dir != 0.0:
		_sprite.flip_h = dir < 0.0
	var moving := absf(velocity.x) > 30.0
	var wanted := &"walk" if moving else &"idle"
	if _sprite.animation != wanted:
		_sprite.play(wanted)
	_sprite.speed_scale = clampf(absf(velocity.x) / SPEED, 0.5, 1.0) if moving else 1.0
