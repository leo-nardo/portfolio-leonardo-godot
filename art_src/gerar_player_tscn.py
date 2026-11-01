"""Gera game/actors/player/player.tscn (rig com braços separados) a partir dos dados do rig."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "game/art/characters/leo_ai"
info = json.load(open(D / "rig/info.json"))
order = json.load(open(D / "ordem_pernas.json"))["ordem"]
IDLE = 8
bodies = sorted(set(order + [IDLE]))
L = ["[gd_scene load_steps=60 format=3]", "",
     '[ext_resource type="Script" path="res://game/actors/player/player.gd" id="1_player"]',
     '[ext_resource type="Script" path="res://game/actors/player/player_input.gd" id="2_input"]']
for n in bodies:
    L.append(f'[ext_resource type="Texture2D" path="res://game/art/characters/leo_ai/quadro_sem_cabeca/q{n:02d}.png" id="b{n:02d}"]')
for nome in ("braco_tras", "braco_perto"):
    for parte in ("cima", "baixo"):
        L.append(f'[ext_resource type="Texture2D" path="res://game/art/characters/leo_ai/rig/{nome}_{parte}.png" id="{nome}_{parte}"]')
L.append('[ext_resource type="Texture2D" path="res://game/art/props/prop_prancheta.png" id="prop_prancheta"]')
L.append('[ext_resource type="Texture2D" path="res://game/art/props/prop_dedos.png" id="prop_dedos"]')
L += ["", '[sub_resource type="CapsuleShape2D" id="CapsuleShape2D_body"]', "radius = 50.0", "height = 330.0", ""]
walk = ", ".join('{\n"duration": 1.0,\n"texture": ExtResource("b%02d")\n}' % n for n in order)
L += ['[sub_resource type="SpriteFrames" id="SpriteFrames_leo"]', 'animations = [{',
      '"frames": [{\n"duration": 1.0,\n"texture": ExtResource("b%02d")\n}],' % IDLE, '"loop": true,', '"name": &"idle",', '"speed": 5.0', '}, {',
      f'"frames": [{walk}],', '"loop": true,', '"name": &"walk",', '"speed": 10.0', '}]', ""]
L += ['[node name="Player" type="CharacterBody2D"]', 'script = ExtResource("1_player")', '',
      '[node name="CollisionShape2D" type="CollisionShape2D" parent="."]', 'position = Vector2(0, -165)', 'shape = SubResource("CapsuleShape2D_body")', '',
      '[node name="Visual" type="Node2D" parent="."]', '',
      '[node name="Shadow" type="Polygon2D" parent="Visual"]', 'position = Vector2(0, -2)', 'color = Color(0, 0, 0, 0.22)',
      'polygon = PackedVector2Array(-90, 0, -66, -11, 0, -14, 66, -11, 90, 0, 66, 11, 0, 14, -66, 11)', '',
      '[node name="Rig" type="Node2D" parent="Visual"]', 'scale = Vector2(0.46, 0.46)', '']
def braco(nome_no, nome):
    k = "tras" if "tras" in nome else "perto"
    i = info[k]; sh = i["ombro"]; eu = i["cotovelo_em_cima"]; el = i["cotovelo_em_baixo"]
    return [f'[node name="{nome_no}" type="Node2D" parent="Visual/Rig"]', '',
          f'[node name="Upper" type="Sprite2D" parent="Visual/Rig/{nome_no}"]', f'position = Vector2({-sh[0]}, {-sh[1]})', f'texture = ExtResource("{nome}_cima")', 'centered = false', '',
          f'[node name="Fore" type="Node2D" parent="Visual/Rig/{nome_no}"]', f'position = Vector2({eu[0]-sh[0]}, {eu[1]-sh[1]})', '',
          f'[node name="Sprite" type="Sprite2D" parent="Visual/Rig/{nome_no}/Fore"]', f'position = Vector2({-el[0]}, {-el[1]})', f'texture = ExtResource("{nome}_baixo")', 'centered = false', ''] + ([f'[node name="HandPoint" type="Marker2D" parent="Visual/Rig/{nome_no}/Fore"]', f'position = Vector2({-el[0]+37}, {-el[1]+88})', ''] if nome_no == "ArmNear" else [])
L += braco("ArmNear", "braco_perto")
L += ['[node name="Clip" type="Node2D" parent="Visual/Rig"]', '',
      '[node name="Board" type="Sprite2D" parent="Visual/Rig/Clip"]', 'position = Vector2(-124, -128)', 'texture = ExtResource("prop_prancheta")', 'centered = false', '',
      '[node name="Fingers" type="Sprite2D" parent="Visual/Rig/Clip"]', 'position = Vector2(-16, -22)', 'texture = ExtResource("prop_dedos")', 'centered = false', '']
L += ['[node name="Body" type="AnimatedSprite2D" parent="Visual/Rig"]', 'sprite_frames = SubResource("SpriteFrames_leo")', 'animation = &"idle"', 'autoplay = "idle"', 'centered = false', f'offset = Vector2(-450, -{json.load(open(D / "corpo_fixo.json"))["alvo_pe"]})', '']
L += ['[node name="Face" type="Node2D" parent="Visual/Rig"]', f'position = Vector2(-450, -{json.load(open(D / "corpo_fixo.json"))["alvo_pe"]})', '']
for _n in ("Base", "EyeL", "EyeR", "Nose", "Mouth", "Helmet"):
    L += [f'[node name="{_n}" type="Sprite2D" parent="Visual/Rig/Face"]', 'centered = false', '']
L += braco("ArmBack", "braco_tras")
L += [
      '[node name="PlayerInput" type="Node" parent="."]', 'script = ExtResource("2_input")', '',
      '[node name="Camera2D" type="Camera2D" parent="."]', 'position = Vector2(0, -200)', 'position_smoothing_enabled = true', 'position_smoothing_speed = 6.0', '']
(ROOT / "game/actors/player/player.tscn").write_text("\n".join(L), encoding="utf-8")
print("player.tscn gerado")
