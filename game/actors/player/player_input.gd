class_name PlayerInput
extends Node
## Converte teclado, mouse/toque e controle numa única intenção de movimento.
## O player só lê `read_direction()`; não sabe de onde a entrada veio.

signal interact_pressed

const STOP_DISTANCE := 12.0

## Destino definido por clique/toque. NAN = sem destino.
var target_x: float = NAN


## Retorna -1..1. Teclado/controle têm prioridade e cancelam o destino do mouse.
func read_direction(from_x: float) -> float:
	var axis := Input.get_axis(&"move_left", &"move_right")
	if axis != 0.0:
		target_x = NAN
		return axis
	if is_nan(target_x):
		return 0.0
	var dx := target_x - from_x
	if absf(dx) <= STOP_DISTANCE:
		target_x = NAN
		return 0.0
	return signf(dx)


func clear_target() -> void:
	target_x = NAN


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"point"):
		var viewport := get_viewport()
		var world_pos := viewport.get_canvas_transform().affine_inverse() * viewport.get_mouse_position()
		target_x = world_pos.x
	elif event.is_action_pressed(&"interact"):
		interact_pressed.emit()
