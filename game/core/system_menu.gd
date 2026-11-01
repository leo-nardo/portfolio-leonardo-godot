extends CanvasLayer
## Botões fixos em todas as cenas: "Voltar" (cena anterior) e "Sair" (fecha o jogo). Esc também sai.

## cena -> cena anterior (vazio = não há anterior)
const PREVIOUS := {
	"res://game/stages/elevator/elevator.tscn": "res://game/stages/giant_foot/giant_foot.tscn",
}

var _back: Button


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	var box := HBoxContainer.new()
	box.position = Vector2(24, 20)
	box.add_theme_constant_override("separation", 12)
	add_child(box)
	_back = _make_button("◀ Voltar")
	_back.pressed.connect(_go_back)
	box.add_child(_back)
	var quit := _make_button("✕ Sair")
	quit.pressed.connect(func() -> void: get_tree().quit())
	box.add_child(quit)


func _make_button(text: String) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(150, 52)
	b.add_theme_font_size_override("font_size", 26)
	return b


func _process(_delta: float) -> void:
	var scene := get_tree().current_scene
	_back.visible = scene != null and PREVIOUS.has(scene.scene_file_path)


func _go_back() -> void:
	var scene := get_tree().current_scene
	if scene and PREVIOUS.has(scene.scene_file_path):
		get_tree().change_scene_to_file(PREVIOUS[scene.scene_file_path])


func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		get_tree().quit()
