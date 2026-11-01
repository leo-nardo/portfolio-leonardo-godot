class_name ElevatorStage
extends Node2D
## Cena 2: dentro da perna do gigante. O elevador fica na perna (lado direito); no lado esquerdo, o espaço
## "cósmico" fora do corpo, com fios de luz descendo, e a área onde vão aparecer as informações.
## Atrás do elevador há um poço de concreto (paredes grossas nas laterais, placas descendo no meio, cabos de aço
## puxando a cabine), mostrando que a cabine sobe.

const SHAFT_SPEED := 300.0            ## px/s das placas descendo
const PANEL_H := 330.0                ## altura de uma placa; todas iguais, então o laço é contínuo
const SHAFT_W := 690.0
const SHAFT_X := 1150.0
const CABLE_X := [1450.0, 1550.0]
const CABLE_BOTTOM := 175.0           ## os cabos entram atrás do topo da cabine
const STRAND_H := 26.0                ## passo do trançado dos cabos

const INK := Color(0.09, 0.08, 0.07)

@onready var _fade: ColorRect = $Hud/Fade
@onready var _panels: Node2D = $Leg/Shaft/Panels
var _strands: Array[Node2D] = []
var _scroll := 0.0
var _strand_scroll := 0.0


func _ready() -> void:
	_fade.color.a = 1.0
	create_tween().tween_property(_fade, "color:a", 0.0, 1.2)
	_build_shaft()
	_build_walls()
	_build_cables()


func _process(delta: float) -> void:
	_scroll = fmod(_scroll + SHAFT_SPEED * delta, PANEL_H)
	_panels.position.y = _scroll - PANEL_H
	_strand_scroll = fmod(_strand_scroll + SHAFT_SPEED * delta, STRAND_H)
	for s in _strands:
		s.position.y = _strand_scroll - STRAND_H


func _rect(parent: Node, pos: Vector2, sz: Vector2, col: Color) -> ColorRect:
	var r := ColorRect.new()
	r.position = pos
	r.size = sz
	r.color = col
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(r)
	return r


## Placas de concreto idênticas empilhadas (por isso a rolagem emenda sem pulo): junta horizontal, duas juntas verticais, parafusos.
func _build_shaft() -> void:
	for i in range(5):
		var y := float(i) * PANEL_H
		_rect(_panels, Vector2(0, y), Vector2(SHAFT_W, PANEL_H), Color(0.39, 0.39, 0.38))
		_rect(_panels, Vector2(0, y + 10.0), Vector2(SHAFT_W, 8.0), Color(1, 1, 1, 0.06))
		_rect(_panels, Vector2(0, y - 5.0), Vector2(SHAFT_W, 10.0), INK)
		for x in [230.0, 460.0]:
			_rect(_panels, Vector2(x, y + 5.0), Vector2(5.0, PANEL_H - 10.0), Color(INK, 0.8))
		for sx in [40.0, SHAFT_W - 40.0]:
			_rect(_panels, Vector2(sx - 6.0, y + 24.0 - 6.0), Vector2(12.0, 12.0), Color(0.22, 0.22, 0.21))


## Paredes grossas e fixas nas laterais do túnel (a divisória entre o lado de fora e o poço) + trilhos-guia da cabine.
func _build_walls() -> void:
	var leg: Node2D = $Leg
	var wall_col := Color(0.24, 0.24, 0.23)
	var left := Polygon2D.new()                  # acompanha a borda levemente curva da perna
	left.polygon = PackedVector2Array([Vector2(1070, -20), Vector2(1060, 540), Vector2(1090, 1100), Vector2(SHAFT_X, 1100), Vector2(SHAFT_X, -20)])
	left.color = wall_col
	leg.add_child(left)
	var right := ColorRect.new()
	right.position = Vector2(SHAFT_X + SHAFT_W, -20)
	right.size = Vector2(1920.0 - SHAFT_X - SHAFT_W + 20.0, 1120)
	right.color = wall_col
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	leg.add_child(right)
	_rect(leg, Vector2(SHAFT_X - 34.0, -20), Vector2(10, 1120), Color(1, 1, 1, 0.05))      # reflexo na parede
	_rect(leg, Vector2(SHAFT_X + SHAFT_W + 24.0, -20), Vector2(10, 1120), Color(1, 1, 1, 0.05))
	_rect(leg, Vector2(SHAFT_X, -20), Vector2(8, 1120), INK)                                # sombra da quina
	_rect(leg, Vector2(SHAFT_X + SHAFT_W - 8.0, -20), Vector2(8, 1120), INK)
	for rx in [SHAFT_X + 8.0, SHAFT_X + SHAFT_W - 32.0]:                                    # trilhos de aço
		_rect(leg, Vector2(rx, -20), Vector2(24, 1120), Color(0.30, 0.31, 0.33))
		_rect(leg, Vector2(rx + 4.0, -20), Vector2(5, 1120), Color(1, 1, 1, 0.14))
	leg.move_child($Leg/Edge, leg.get_child_count() - 1)


## Cabos de aço do topo da cabine para cima; o trançado desce, como se a cabine estivesse subindo.
func _build_cables() -> void:
	var leg: Node2D = $Leg
	for cx in CABLE_X:
		var clip := Control.new()
		clip.clip_contents = true
		clip.position = Vector2(cx - 9.0, -20)
		clip.size = Vector2(18, CABLE_BOTTOM + 20.0)
		clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		leg.add_child(clip)
		_rect(clip, Vector2(0, 0), clip.size, INK)
		_rect(clip, Vector2(3, 0), Vector2(12, clip.size.y), Color(0.50, 0.51, 0.53))
		var strands := Node2D.new()
		clip.add_child(strands)
		_strands.append(strands)
		for k in range(int(clip.size.y / STRAND_H) + 3):
			var m := Polygon2D.new()                  # trançado em diagonal
			var y := float(k) * STRAND_H
			m.polygon = PackedVector2Array([Vector2(3, y + 14), Vector2(15, y + 4), Vector2(15, y + 9), Vector2(3, y + 19)])
			m.color = Color(0.22, 0.22, 0.24)
			strands.add_child(m)
