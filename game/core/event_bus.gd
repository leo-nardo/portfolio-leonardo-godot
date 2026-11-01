extends Node
## Barramento de eventos globais. Sistemas conversam por aqui, nunca por caminhos de nó.

signal stage_requested(stage_id: StringName, spawn_id: StringName)
signal stage_changed(stage_id: StringName)
signal interaction_started(interactable: Node)
signal interaction_finished(interactable: Node)
