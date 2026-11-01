extends Node
## Progresso do visitante: cenários visitados e flags ("já falou com X").

signal flag_changed(flag: StringName, value: Variant)

var visited_stages: Dictionary = {}
var _flags: Dictionary = {}


func mark_visited(stage_id: StringName) -> void:
	visited_stages[stage_id] = true


func has_visited(stage_id: StringName) -> bool:
	return visited_stages.has(stage_id)


func set_flag(flag: StringName, value: Variant = true) -> void:
	_flags[flag] = value
	flag_changed.emit(flag, value)


func get_flag(flag: StringName, default: Variant = false) -> Variant:
	return _flags.get(flag, default)
