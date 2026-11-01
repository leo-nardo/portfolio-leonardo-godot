# 0001 — Conceito: o Leonardo gigante e o guia em miniatura

Status: **ideia anotada, ainda não implementada.** O foco agora é o visual (ver 0002 quando existir).

## A ideia (palavras do autor, organizadas)

- Existe uma versão do Leonardo **desenhada, gigantesca**, como um Megazord ou um colosso. A aparência é **normal, sem robotizar nada**. Ele está **totalmente parado**, como um monumento.
- Esse gigante **não é o personagem controlável**.
- O personagem controlável é o **Leonardo em terceira pessoa**: uma **versão miniatura**, que age como **guia/apresentador** e fala do Leonardo como de outra pessoa ("vamos conhecer o Leonardo").
- **Primeira tela:** o guia se apresenta. Algo como "eu sou o cara que vai te apresentar o Leonardo hoje; se você quer conhecê-lo melhor, vem comigo".
- O gigante tem uma **esteira ou escada rolante** que leva até o **topo da cabeça**, onde há uma **porta**. O visitante entra e conhece o Leonardo **por dentro da cabeça dele**.
- **Dentro da cabeça** acontecem as interações (sobre, projetos, contato etc.), no corpo principal do portfólio.

## Efeitos na arquitetura (rascunho, a confirmar)

- Duas camadas de narrativa: **exterior** (gigante, escada, guia) e **interior** (cabeça, onde ficam os conteúdos). Cada uma é um ou mais cenários no registro de cenários.
- O cenário exterior usa **rolagem vertical** (a subida pela escada rolante), além da horizontal. A câmera e os limites do `stage_base` precisam permitir isso.
- O guia fala em **terceira pessoa**: o texto dos diálogos fica em arquivos de conteúdo, escritos nesse tom.
- O gigante é um **prop enorme** composto de camadas (corpo, rosto, escada, porta), pensado desde já em partes para dar para animar leves detalhes (respiração mínima, piscar), se o autor quiser. Hoje ele é "totalmente parado".
- Os 4 cenários antigos (Clareira, Casa na Árvore, Mural, Varanda) provavelmente viram **ambientes dentro da cabeça** ou ficam como tema do interior. A definir.

## Perguntas em aberto (não responder agora)

1. O gigante fica numa paisagem (floresta, cidade, deserto)? Em que escala em relação ao guia?
2. A escada rolante é uma cena jogável (o guia anda nela) ou uma transição curta?
3. O interior da cabeça é um espaço único ou vários cômodos (memórias, projetos, contato)?
4. O guia e o Leonardo gigante têm o mesmo visual? (Hoje: guia = personagem atual, a redesenhar.)
