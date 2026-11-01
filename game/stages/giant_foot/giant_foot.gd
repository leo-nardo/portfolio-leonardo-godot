class_name GiantFootStage
extends StageBase
## Cena 1: o guia (miniatura) chega ao pé do Leonardo gigante (~50x), abre a porta do elevador, entra e as portas fecham.

const DOOR_X := 2900.0                  ## centro da porta, em coordenadas do mundo
const NEAR := 420.0                     ## distância para o aviso/tecla "entrar"
const PANEL_SLIDE := 118.0
const DOOR_RECT_POS := Vector2(2730.0, 414.0)
const DOOR_RECT_SIZE := Vector2(340.0, 540.0)

@onready var _waiting: Sprite2D = $Door/Waiting
@onready var _panel_l: Sprite2D = $Door/PanelL
@onready var _panel_r: Sprite2D = $Door/PanelR
@onready var _prompt: Label = $Hud/Prompt
@onready var _fade: ColorRect = $Hud/Fade
@onready var _end_label: Label = $Hud/EndLabel

var _state := &"idle"                   ## idle -> opening -> walking_in -> closing -> done


func _ready() -> void:
	super()
	_player.get_node("PlayerInput").interact_pressed.connect(_on_interact)
	_fade.color.a = 0.0
	_end_label.visible = false


func _process(_delta: float) -> void:
	var dx := absf(_player.global_position.x - DOOR_X)
	_prompt.visible = _state == &"idle" and dx < NEAR
	if _state == &"approaching" and dx < 150.0:
		_start()


## Clicar no elevador: o personagem anda até ele e, ao chegar, a porta abre.
func _unhandled_input(event: InputEvent) -> void:
	if _state != &"idle" or not (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT):
		return
	var p := get_global_mouse_position()
	if Rect2(DOOR_RECT_POS, DOOR_RECT_SIZE).has_point(p):
		_state = &"approaching"
		_player.get_node("PlayerInput").target_x = DOOR_X - 90.0
		get_viewport().set_input_as_handled()


func _on_interact() -> void:
	if _state == &"idle" and absf(_player.global_position.x - DOOR_X) < NEAR:
		_start()


func _start() -> void:
	_state = &"opening"
	_prompt.visible = false
	var t := create_tween().set_parallel(true)
	t.tween_property(_panel_l, "position:x", _panel_l.position.x - PANEL_SLIDE, 0.9).set_trans(Tween.TRANS_SINE)
	t.tween_property(_panel_r, "position:x", _panel_r.position.x + PANEL_SLIDE, 0.9).set_trans(Tween.TRANS_SINE)
	t.chain().tween_callback(_walk_in)


func _walk_in() -> void:
	_state = &"walking_in"
	_player.get_node("PlayerInput").target_x = DOOR_X
	while absf(_player.global_position.x - DOOR_X) > 14.0:
		await get_tree().process_frame
	_player.controllable = false
	# troca o sprite de perfil pelo de frente (parado no fundo do elevador)
	var visual: Node2D = _player.get_node("Visual")
	_waiting.visible = true
	_waiting.modulate.a = 0.0
	_waiting.position = Vector2(DOOR_X, _player.global_position.y)
	var t := create_tween().set_parallel(true)
	t.tween_property(visual, "modulate:a", 0.0, 0.35)
	t.tween_property(_waiting, "modulate:a", 1.0, 0.35)
	await t.finished
	var back := create_tween().set_parallel(true)
	back.tween_property(_waiting, "position:y", 930.0, 0.8).set_trans(Tween.TRANS_SINE)
	back.tween_property(_waiting, "scale", Vector2(0.26, 0.26), 0.8).set_trans(Tween.TRANS_SINE)
	await back.finished
	await get_tree().create_timer(0.8).timeout
	_state = &"closing"
	var c := create_tween().set_parallel(true)
	c.tween_property(_panel_l, "position:x", _panel_l.position.x + PANEL_SLIDE, 0.9).set_trans(Tween.TRANS_SINE)
	c.tween_property(_panel_r, "position:x", _panel_r.position.x - PANEL_SLIDE, 0.9).set_trans(Tween.TRANS_SINE)
	await c.finished
	await get_tree().create_timer(0.5).timeout
	var f := create_tween()
	f.tween_property(_fade, "color:a", 1.0, 1.0)
	await f.finished
	_state = &"done"
	await get_tree().create_timer(0.6).timeout
	get_tree().change_scene_to_file("res://game/stages/elevator/elevator.tscn")
