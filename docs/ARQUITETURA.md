# Portfólio Imersivo — Arquitetura (rascunho v0.2)

> v0.2: premissas conferidas na documentação do Godot (versão fixada 4.7.2, C# não exporta para web, single-thread padrão), entrada por teclado + mouse definida. Falta responder as perguntas 1–3 e 5–9.

> Status: proposta para revisão. Nada aqui está implementado ainda.
> Objetivo: um portfólio web em Godot onde o personagem caminha por cenários cartoon,
> se apresenta e interage com objetos. Fidelidade à visão do autor > velocidade.

## 1. Princípios

1. **Dados separados de código.** Textos, projetos, falas e links vivem em arquivos de conteúdo, não dentro de scripts ou cenas. Mudar um texto não exige mexer em lógica.
2. **Cena = unidade independente.** Cada cenário, personagem e objeto é uma cena que funciona sozinha (dá para abrir e testar com F6).
3. **Composição em vez de herança.** Comportamentos viram componentes pequenos (nós) que se encaixam: `Interactable`, `Dialogue`, `Collectible`. Evitar árvores de herança profundas.
4. **Sinais para desacoplar.** Sistemas conversam por sinais/barramento de eventos, nunca por caminhos de nó (`get_node("../../x")`).
5. **Adicionar sem alterar.** Novo cenário, nova interação ou novo projeto = novo arquivo + registro, sem editar o núcleo (aberto para extensão).
6. **Decisões registradas.** Escolhas importantes vão em `docs/decisoes/` (ADR curtos), para não esquecer o porquê.

## 2. Decisões técnicas iniciais

| Tema | Decisão | Motivo |
|---|---|---|
| Versão do Godot | **4.7.2 estável, fixada** no projeto | Reprodutibilidade; `Parallax2D` e export web single-thread existem desde 4.3 (conferido) |
| Linguagem | **GDScript** | **Confirmado:** a documentação oficial (4.6 e "latest") diz que projetos C# do Godot 4 não exportam para web. Só há builds não oficiais da comunidade (ComplexRobot), experimentais |
| Renderizador | Compatibility (OpenGL/WebGL2) | Único suportado no export web |
| Export web | Single-thread (padrão desde 4.3) | Não exige cabeçalhos COOP/COEP; só o multi-thread exige. Comprimir `.wasm` e `.pck` no servidor (gzip ≈ 1/4 do tamanho, Brotli melhor) |
| Áudio web | Modo Sample (padrão) | Sem efeitos de áudio, reverb ou som posicional confiável; Stream restaura tudo, mas com latência. Música só após o primeiro clique/tecla |
| Entrada | Teclado **e** mouse, mais toque/controle depois | Ver seção 4.2 |
| Resolução base | 1920x1080, stretch `canvas_items`, aspect `expand` | Arte vetorial escala bem; a decidir comportamento em celular |
| Arte | Vetor (SVG) como fonte, exportada/importada em 2x | Estilo chapado com contorno grosso fica nítido |
| Idiomas | Tabela de traduções (CSV) desde o início, pt-BR primeiro | Encaixar inglês depois sem refazer |

## 3. Estrutura de pastas (por funcionalidade, não por tipo)

```
portfolio-godot/
├─ project.godot
├─ docs/                    # arquitetura, decisões (ADR), guia de estilo
├─ art_src/                 # FONTES editáveis (.svg/.ai/.blend/.kra) — fora do res://
├─ game/                    # tudo que o Godot enxerga (res://)
│  ├─ core/                 # autoloads e serviços globais
│  │   ├─ event_bus.gd          # sinais globais
│  │   ├─ scene_manager.gd      # trocar cenários, transições, loading
│  │   ├─ game_state.gd         # progresso, flags (ex.: "já falou com X")
│  │   ├─ audio_manager.gd      # música, efeitos, mute, desbloqueio no 1º clique
│  │   ├─ settings.gd           # idioma, volume, acessibilidade
│  │   └─ web_bridge.gd         # ponte com JavaScript (URL, links, analytics)
│  ├─ actors/
│  │   ├─ player/               # personagem: cena, máquina de estados, rig
│  │   └─ npcs/                 # figurantes, animais, objetos vivos
│  ├─ components/           # peças reutilizáveis
│  │   ├─ interactable/         # área + prompt + ação
│  │   ├─ state_machine/
│  │   └─ trigger_zone/         # gatilhos por posição (entrar na área → fala)
│  ├─ interactions/         # AÇÕES (Resources) executadas por Interactable
│  │   ├─ action_dialogue.gd
│  │   ├─ action_open_panel.gd
│  │   ├─ action_open_url.gd
│  │   ├─ action_change_stage.gd
│  │   └─ action_play_animation.gd
│  ├─ stages/               # cenários (cada um é uma pasta)
│  │   ├─ stage_base.tscn       # base: camadas de paralaxe, câmera, spawn, saídas
│  │   ├─ forest_start/
│  │   ├─ tree_house/
│  │   └─ ...
│  ├─ ui/                   # caixa de diálogo, painéis, menu, loading, tema
│  ├─ content/              # CONTEÚDO (editável sem programar)
│  │   ├─ dialogues/
│  │   ├─ projects/             # 1 arquivo por projeto (.tres)
│  │   ├─ profile/              # bio, stack, experiência
│  │   └─ translations/
│  ├─ audio/
│  └─ art/                  # arte já exportada/importada, espelha art_src
├─ web/                     # casca HTML, tela de loading, fallback sem JS/WebGL
├─ tests/                   # testes (GUT) dos sistemas, não da arte
└─ tools/                   # scripts de export, build, validação
```

Regra de dependência: `stages` e `actors` podem usar `components`, `interactions`, `ui` e `core`; **`core` e `components` não conhecem nenhum cenário específico**.

## 4. Peças principais

### 4.1 Stage (cenário)
- `stage_base.tscn`: câmera com limites, camadas `Parallax2D` nomeadas (`far`, `mid`, `ground`, `front`), `SpawnPoints`, `Exits`, `Interactables`.
- Cada cenário **herda** a base e só preenche arte e objetos.
- **Registro de cenários** (`stage_registry.tres`): lista ordenada com id, título, cena, música. Adicionar cenário = criar a cena e incluir no registro.
- Entradas e saídas por **ids de ponto** (`from: "forest_start/exit_right" → to: "tree_house/spawn_left"`), não por posições soltas.

### 4.2 Player
- `CharacterBody2D` com **máquina de estados**: `Idle`, `Walk`, `Interact`, `Cutscene` (controle travado).
- **Entrada abstraída** (`PlayerInput`): cada fonte produz a mesma **intenção** (`move_dir`, `interact`), e o player só lê a intenção. Mobile entra sem refazer o personagem.
  - **Teclado:** setas/WASD para andar, `E`/Espaço/Enter para interagir. Ações no `InputMap` (`move_left`, `move_right`, `interact`), nunca teclas fixas no código.
  - **Mouse (clicar para andar):** clique no chão define um `move_target`; o player caminha até lá e para. Clicar num objeto interativo faz o personagem andar até ele e então executar a ação. Passar o mouse sobre um objeto interativo destaca o objeto e muda o cursor.
  - **Arbitragem:** qualquer tecla de movimento cancela o destino do mouse; um novo clique substitui o destino. Em cutscene/diálogo, o clique avança a fala em vez de mover.
  - **Toque (celular):** o toque funciona como o clique do mouse (clicar para andar); joystick virtual opcional depois.
  - **Controle:** entra pelo mesmo `InputMap`, sem código novo.
  - Componentes: `KeyboardSource`, `PointerSource` (mouse+toque), `GamepadSource` → `PlayerInput` mescla com a regra acima.
- **Rig em recorte** (partes separadas) com `AnimationPlayer`/`AnimationTree`; trocar de arte não quebra a lógica, só os sprites.

### 4.3 Interações (o coração da imersão)
- `Interactable`: define **quando** (aproximar, clicar, tecla) e **qual ação** executar.
- **Ação** é um `Resource` configurável no inspetor: mostrar diálogo, abrir painel de projeto, abrir link, trocar de cenário, tocar animação, ou **sequência** de ações. Isso permite criar interações novas sem escrever código.
- Nova ideia de interação = nova classe de ação (1 arquivo), disponível em todos os cenários.

### 4.4 Diálogo e conteúdo
- Falas e textos em arquivos de conteúdo, com chaves de tradução. Avaliar um addon consolidado de diálogo (ex.: Dialogue Manager) contra um sistema próprio mínimo — registrar como ADR.
- Cada projeto do portfólio é um `ProjectEntry` (`.tres`): título, resumo, stack, links, imagens. A UI de "Projetos" lê da pasta; **adicionar projeto = adicionar arquivo**.
- Progresso/flags no `GameState`, para falas que mudam conforme o que o visitante já viu.

### 4.5 Web
- Tela de loading própria e leve (carrega antes do `.pck`).
- Áudio só inicia após o primeiro clique do visitante (regra do navegador).
- **Links diretos**: `#/projetos` leva ao cenário certo (via `JavaScriptBridge`).
- **Fallback**: página HTML simples com bio, projetos, currículo e contato, para quem não tem WebGL, para buscadores e para acessibilidade.
- Meta de peso inicial a definir (sugestão: < 25 MB), medindo desde o primeiro cenário.

## 5. Pipeline de arte
1. **Guia de estilo** (`docs/guia-de-estilo.md`): paleta, espessura do contorno, proporções, regras de sombra, referências.
2. Fontes em `art_src/` com **camadas nomeadas** (ex.: `braco_dir`, `cabeca`, `far/`, `mid/`) que viram arquivos separados.
3. Convenção de nomes: `snake_case`, prefixos por tipo (`bg_`, `prop_`, `char_`, `fx_`, `ui_`).
4. Exportação padronizada (tamanho, escala 2x, pivôs) para `game/art/`, idealmente com um script em `tools/`.
5. Blender fica opcional (animação 2D com Grease Pencil ou pré-renderizar props). Não é caminho obrigatório.

## 6. Qualidade e fluxo de trabalho
- **Git desde o dia 1**, em repositório novo; arquivos grandes de arte fonte com Git LFS ou fora do repositório.
- Convenções de código GDScript (guia oficial), tipagem estática ligada.
- Testes automatizados só para sistemas (estado, ações, registro de cenários); arte e "sensação" se validam jogando.
- Cena de **depuração** (`debug_stage`) com atalhos para pular de cenário e testar interações.
- CI opcional: exportar a versão web a cada push e publicar (Netlify/GitHub Pages/Cloudflare Pages).

## 7. Roadmap por marcos

| Marco | Entrega | Pronto quando |
|---|---|---|
| M0 | Guia de estilo + documento da visão (roteiro dos cenários e personagem) | Você aprova o rumo visual e narrativo |
| M1 | Esqueleto do projeto (pastas, autoloads, git, export web "vazio") | Roda no navegador com a tela de loading |
| M2 | Player andando com placeholder + `stage_base` + câmera | Anda em um cenário de teste, teclado e toque |
| M3 | Sistema de interação + diálogo + 1 projeto de exemplo | Conversa com objeto e abre painel de projeto |
| M4 | Primeiro cenário com arte final (paralaxe, sons, animações) | Cenário "de vitrine" aprovado por você |
| M5 | Demais cenários, tradução, fallback HTML, performance mobile | Versão publicada |

## 7.0 Conceito narrativo (anotado, a detalhar depois)

O visitante controla um **guia em miniatura** (o Leonardo em terceira pessoa) que apresenta "o Leonardo": um **gigante desenhado, parado**, de aparência normal. Uma escada/esteira rolante leva ao topo da cabeça, onde há uma porta; dentro da cabeça ficam as interações e o conteúdo. Detalhes e perguntas em `docs/decisoes/0001-conceito-leonardo-gigante.md`. Prioridade atual: **resolver o aspecto visual** antes de implementar isso.

## 7.1 Referência visual e de conteúdo (do autor)

- **Tema:** tudo no estilo **Cartoon Network** (contorno grosso e escuro, cores chapadas com sombreado simples, cenários de floresta/interior de madeira, personagem expressivo).
- **Fonte de referência:** o portfólio antigo `port-folio` (Vite + React). Serve só de **referência**; **personagem, cenários e tudo mais serão refeitos do zero** em Blender e/ou programa de vetor (VectorCraft — confirmar o programa). As artes antigas (`character.png/gif`, `forest-background.png`, `tree-house-background.png`) não vão para o projeto final.
- **O que o antigo mostra (a manter como ideia, redesenhado):**
  - Cabeçalho com logo "LV" e menu (Página inicial, Sobre mim, Projetos, Contatos), estilo "Portfolio Quest".
  - Cartão "NOVA PARTIDA" com nome, tagline e botões (Entrar, Projetos, Currículo).
  - Balão de fala do personagem ("Olá! Me chamo Leonardo Vinicius…").
  - Botões grandes em madeira/marrom com contorno, navegação Anterior/Próxima, ícones de teclas.
  - Cenas existentes: **Clareira Inicial** (floresta com casa na árvore), **Casa na Árvore** (interior, sobre mim), **Mural de Missões** (projetos), **Varanda de Contato**.
- **Conteúdo reaproveitável:** `port-folio/src/data/portfolio.ts` (perfil, sobre, habilidades, experiências, formação, 4 projetos, serviços, comunidade Devs Tocantins). Vai virar arquivos em `game/content/` (ProjectEntry `.tres` + tabela de traduções), sem copiar o formato do TypeScript.
- **Ferramentas de arte:** Blender (controlável pelo MCP nesta sessão). **VectorCraft 0.18.0** (open source, Rust) está em `C:\Users\leona\Downloads\vectorcraft-0.18.0\app\vectorcraft-0.18.0-windows-x64-portable\` e **tem servidor MCP próprio** (`vectorcraft-cli.exe mcp`), então dá para eu desenhar, editar e exportar SVG/PNG por ele, além de você desenhar à mão. Falta registrar o MCP no Claude Code (precisa da sua autorização). É alfa ("~65% pronto para trabalho real"): validar cedo se o traço Cartoon Network sai bem (contorno grosso, formas orgânicas) antes de depender dele; Blender e desenho manual são alternativas.

## 8. Perguntas em aberto (para você decidir)
1. ~~**Estrutura da jornada**~~ **Respondida: mapa com vários caminhos** (não linear). Implicações: cenários formam um grafo (cada saída aponta para um ponto de entrada de outro cenário, já previsto em 4.1); o `GameState` guarda o que foi visitado; vale um mapa/atalho de navegação e link direto por cenário. Ainda em aberto: existe um "fim" ou ponto central (hub)?
2. ~~**Cenários desejados**~~ **Respondida:** por enquanto só os 4 do portfólio antigo (Clareira Inicial, Casa na Árvore, Mural de Missões, Varanda de Contato); mais cenários depois, o que o registro de cenários já comporta. Jornada **livre, sem fim**. Ainda sem resposta: qual cenário é o ponto de partida/central (hipótese: Clareira Inicial).
3. **Personagem:** **refazer do zero** (visual redesenhado, pode se inspirar no atual). Em aberto: quais ações além de andar (acenar, pular, sentar…)?
4. **(navegação entre cenários)** **Respondida: os dois** — caminhando pelas saídas do cenário **e** por um mapa clicável para pular direto. Cada cenário é endereçável por id/link.
4b. ~~**Controle principal**~~ **Respondida:** teclado **e** mouse (clicar para andar e clicar em objetos). Celular: toque age como o clique. Detalhes na seção 4.2.
5. **Texto vs. fala:** diálogos só em balões de texto, ou terá voz/sons de "tagarelice"?
6. **Idiomas:** só pt-BR no início, ou já pt-BR + inglês?
7. **Onde publicar** e qual domínio?
8. **O que é imprescindível no conteúdo:** projetos, currículo, contato, o que mais?
9. **Referências visuais:** nomes de episódios/cenas/portfólios que você quer evocar (para o guia de estilo).
