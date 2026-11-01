# Prompt inicial para a nova sessão

Cole o texto abaixo na nova sessão do Claude Code. Abra a sessão com o Godot e o Blender já abertos e com os MCPs carregados.

---

Oi! Vamos construir meu portfólio imersivo em Godot. Antes de escrever qualquer coisa, leia o contexto abaixo e depois o documento `C:\Users\leona\projetos\projetos\portfolio-godot\docs\ARQUITETURA.md`.

## A visão
Quero um portfólio pessoal para web que seja uma **experiência imersiva**, não um jogo de verdade. Meu personagem caminha por cenários cartoon, se apresenta e interage com os objetos, com vários conceitos legais pelo caminho. A inspiração é o estilo de Cartoon Network, e eu já vi portfólios interativos incríveis que me motivaram. Não quero copiar nada deles, quero configurar cada detalhe do meu jeito. Vou refazer todas as artes.

O que importa é a **exatidão do que está na minha cabeça**, não a velocidade. Pense como arquiteto de software: modular, adaptável, fácil de manter e de crescer, para caber ideias novas que eu ainda nem tive. Você não vai saber tudo que imagino, então me faça perguntas em vez de supor.

## Estado atual
- **Projeto Godot:** `C:\Users\leona\projetos\jogo-godot`, Godot **4.7.2 estável**, renderizador Compatibility (o da versão web), plugin `godot_ai` instalado. O nome "Jogo" é provisório. O projeto está vazio.
- **Blender:** 5.2.3 LTS, aberto. Uso só se for necessário, o caminho principal de arte é vetor.
- **Documento de arquitetura (rascunho v0.1):** `C:\Users\leona\projetos\projetos\portfolio-godot\docs\ARQUITETURA.md`. Está no meu PC mas ainda fora do projeto Godot. Quero juntar os dois num lugar só (sugestão: mover `docs` para dentro de `jogo-godot` ou renomear o projeto).
- **Portfólio antigo, só como referência:** repositório privado `leo-nardo/port-folio`, clonado em `C:\Users\leona\projetos\projetos\port-folio` (Vite + React). Tem as artes atuais (`src/assets/character.png`, `forest-background.png`, `tree-house-background.png`), os textos e a lista de projetos. As artes serão refeitas. O conteúdo (bio, projetos, contato) pode ser reaproveitado.
- **Outro portfólio meu, minimalista:** `C:\Users\leona\projetos\projetos\portfolio`. Não é o que quero agora.
- O `gh` está logado como `leo-nardo`.

## Decisões já tomadas
- Motor: **Godot**, exportado para web.
- Linguagem: **GDScript** (a confirmar se C# exporta para web na 4.7).
- Conteúdo separado do código, cenas independentes, composição em vez de herança, interações como `Resource` configuráveis no inspetor, cenários cadastrados em registro, entrada abstraída (teclado, toque e controle), página HTML de reserva para quem não tem WebGL.

## O que fazer primeiro
1. Leia `ARQUITETURA.md` e **confira nas notas oficiais do Godot 4.7** o que o documento assume, principalmente o export web (single-thread, tamanho, áudio), `Parallax2D` e a possibilidade de C#. Corrija o documento onde estiver errado e atualize a versão fixada para 4.7.2.
2. Verifique se os MCPs do Godot e do Blender estão disponíveis nesta sessão. Se não estiverem, me avise antes de seguir.
3. Faça as **9 perguntas em aberto** do final do documento, uma a uma ou em pequenos grupos, e registre minhas respostas no documento. Comece pelas três primeiras (estrutura da jornada, cenários, personagem).
4. Só depois de eu aprovar a arquitetura, monte o esqueleto do marco **M1** (pastas, autoloads, git, export web de teste) e depois o **M2** (personagem andando com placeholder).

## Como quero trabalhar
- Responda em português do Brasil, de forma direta e sem enrolação.
- Mostre o plano antes de mexer em muita coisa e peça minha confirmação nas decisões que mudam a direção do projeto.
- Registre decisões importantes em `docs/decisoes/` (um arquivo curto por decisão).
- Não apague nada e não faça commit ou push sem eu pedir. Pode criar o repositório git local se eu autorizar.
- Teste o que construir (rodar no editor ou no navegador) antes de dizer que está pronto, e diga claramente o que não conseguiu verificar.
- Eu costumo falar pelo celular, então resuma resultados e mande prints quando for útil.
