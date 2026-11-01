## Gerado por art_src/gerar_player_tscn.py — não editar à mão.
class_name LeoFaceData

# posições no canvas do corpo (o nó Face usa o mesmo deslocamento do corpo)
const BASE_POS := Vector2(225, 41)
const HELMET_POS := Vector2(221, 10)
const PART_POS := {&"olho_e": Vector2(310, 160), &"olho_d": Vector2(462, 140), &"nariz": Vector2(418, 228), &"boca": Vector2(392, 284)}
const BASE: Texture2D = preload("res://game/art/characters/leo_rostos/partes/base.png")
const HELMET: Texture2D = preload("res://game/art/characters/leo_rostos/partes/capacete.png")

## Peças disponíveis por encaixe. Cada nome vem de uma expressão do desenho.
const PARTS := {
	&"olho_e": {
		&"fala": preload("res://game/art/characters/leo_rostos/partes/olho_e/fala.png"),
		&"desconfiado": preload("res://game/art/characters/leo_rostos/partes/olho_e/desconfiado.png"),
		&"bocejo": preload("res://game/art/characters/leo_rostos/partes/olho_e/bocejo.png"),
		&"surpreso": preload("res://game/art/characters/leo_rostos/partes/olho_e/surpreso.png"),
		&"furioso": preload("res://game/art/characters/leo_rostos/partes/olho_e/furioso.png"),
		&"irritado": preload("res://game/art/characters/leo_rostos/partes/olho_e/irritado.png"),
		&"debochado": preload("res://game/art/characters/leo_rostos/partes/olho_e/debochado.png"),
		&"preocupado": preload("res://game/art/characters/leo_rostos/partes/olho_e/preocupado.png"),
		&"animado": preload("res://game/art/characters/leo_rostos/partes/olho_e/animado.png"),
		&"lendo": preload("res://game/art/characters/leo_rostos/partes/olho_e/lendo.png"),
		&"normal": preload("res://game/art/characters/leo_rostos/partes/olho_e/normal.png"),
	},
	&"olho_d": {
		&"fala": preload("res://game/art/characters/leo_rostos/partes/olho_d/fala.png"),
		&"desconfiado": preload("res://game/art/characters/leo_rostos/partes/olho_d/desconfiado.png"),
		&"bocejo": preload("res://game/art/characters/leo_rostos/partes/olho_d/bocejo.png"),
		&"surpreso": preload("res://game/art/characters/leo_rostos/partes/olho_d/surpreso.png"),
		&"furioso": preload("res://game/art/characters/leo_rostos/partes/olho_d/furioso.png"),
		&"irritado": preload("res://game/art/characters/leo_rostos/partes/olho_d/irritado.png"),
		&"debochado": preload("res://game/art/characters/leo_rostos/partes/olho_d/debochado.png"),
		&"preocupado": preload("res://game/art/characters/leo_rostos/partes/olho_d/preocupado.png"),
		&"animado": preload("res://game/art/characters/leo_rostos/partes/olho_d/animado.png"),
		&"lendo": preload("res://game/art/characters/leo_rostos/partes/olho_d/lendo.png"),
		&"normal": preload("res://game/art/characters/leo_rostos/partes/olho_d/normal.png"),
	},
	&"nariz": {
		&"fala": preload("res://game/art/characters/leo_rostos/partes/nariz/fala.png"),
		&"desconfiado": preload("res://game/art/characters/leo_rostos/partes/nariz/desconfiado.png"),
		&"bocejo": preload("res://game/art/characters/leo_rostos/partes/nariz/bocejo.png"),
		&"surpreso": preload("res://game/art/characters/leo_rostos/partes/nariz/surpreso.png"),
		&"furioso": preload("res://game/art/characters/leo_rostos/partes/nariz/furioso.png"),
		&"irritado": preload("res://game/art/characters/leo_rostos/partes/nariz/irritado.png"),
		&"debochado": preload("res://game/art/characters/leo_rostos/partes/nariz/debochado.png"),
		&"preocupado": preload("res://game/art/characters/leo_rostos/partes/nariz/preocupado.png"),
		&"animado": preload("res://game/art/characters/leo_rostos/partes/nariz/animado.png"),
		&"lendo": preload("res://game/art/characters/leo_rostos/partes/nariz/lendo.png"),
		&"normal": preload("res://game/art/characters/leo_rostos/partes/nariz/normal.png"),
	},
	&"boca": {
		&"fala": preload("res://game/art/characters/leo_rostos/partes/boca/fala.png"),
		&"desconfiado": preload("res://game/art/characters/leo_rostos/partes/boca/desconfiado.png"),
		&"bocejo": preload("res://game/art/characters/leo_rostos/partes/boca/bocejo.png"),
		&"surpreso": preload("res://game/art/characters/leo_rostos/partes/boca/surpreso.png"),
		&"furioso": preload("res://game/art/characters/leo_rostos/partes/boca/furioso.png"),
		&"irritado": preload("res://game/art/characters/leo_rostos/partes/boca/irritado.png"),
		&"debochado": preload("res://game/art/characters/leo_rostos/partes/boca/debochado.png"),
		&"preocupado": preload("res://game/art/characters/leo_rostos/partes/boca/preocupado.png"),
		&"animado": preload("res://game/art/characters/leo_rostos/partes/boca/animado.png"),
		&"lendo": preload("res://game/art/characters/leo_rostos/partes/boca/lendo.png"),
		&"normal": preload("res://game/art/characters/leo_rostos/partes/boca/normal.png"),
	},
}
