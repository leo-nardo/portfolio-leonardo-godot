class_name StageBase
extends Node2D
## Base de cenário: define a largura jogável e limita a câmera do player.

@export var stage_id: StringName = &"stage"
@export var stage_width := 4000.0

@onready var _player: Player = $Player


func _ready() -> void:
	var camera: Camera2D = _player.get_node("Camera2D")
	camera.limit_left = 0
	camera.limit_right = int(stage_width)
	camera.limit_top = 0
	camera.limit_bottom = 1080
	_build_walls()
	GameState.mark_visited(stage_id)
	EventBus.stage_changed.emit(stage_id)


## Paredes invisíveis nas pontas do cenário, para o personagem não cair do mundo.
func _build_walls() -> void:
	for x in [-60.0, stage_width + 60.0]:
		var wall := StaticBody2D.new()
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = Vector2(120, 4000)
		shape.shape = rect
		wall.add_child(shape)
		wall.position = Vector2(x, 500)
		add_child(wall)
