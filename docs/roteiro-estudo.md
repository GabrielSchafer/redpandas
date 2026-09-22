# Roteiro de estudo e apresentação — 30 minutos

Sequência para entender o projeto e explicá-lo para outra pessoa. Seis blocos, do problema até
os trade-offs. Cada bloco tem o que mostrar, a ideia central e as analogias que funcionam.

## Antes: uma hora de leitura

Leia o código nesta ordem — ela vai do vocabulário para a cola, não de cima para baixo:

| Ordem | Arquivo | O que entender |
| --- | --- | --- |
| 1 | `events/envelope.py` | O formato único de toda mensagem |
| 2 | `events/topics.py`, `events/types.py` | O vocabulário inteiro do sistema |
| 3 | `messaging/producer.py`, `consumer.py` | As únicas linhas que falam com o broker |
| 4 | `services/ledger.py`, `services/matching.py` | Regra de negócio pura, sem Kafka |
| 5 | `workers/base.py` + um worker | A cola: consome, chama o serviço, publica |
| 6 | `api/routes/orders.py`, `store/projections.py` | Escrita vira comando, leitura vem da projeção |

Deixe a stack rodando ao lado (`make up`, `make monitor`, `make traffic`) enquanto lê.

## Bloco 1 · O problema (0:00 – 0:04)

Comece pelo jeito convencional: API que recebe a ordem, chama o serviço de risco por HTTP, que
consulta o banco, que chama o matching, que grava, que avisa o ledger. Pergunte o que acontece se
o matching estiver fora do ar. Resposta: a chamada falha e o usuário vê erro, mesmo que a ordem
fosse perfeitamente válida.

> Ideia central: o problema não é a lentidão, é o **acoplamento temporal** — todo mundo precisa
> estar vivo no mesmo instante.

## Bloco 2 · Log, Kafka e Redpanda (0:04 – 0:10)

| Conceito | Analogia que funciona |
| --- | --- |
| Log append-only | Extrato bancário: você não edita uma linha, lança outra |
| Tópico | Um extrato com nome, por assunto |
| Partição e chave | Filas de caixa no mercado: mesma chave sempre no mesmo caixa, então a ordem é preservada ali dentro |
| Offset | Marcador de página |
| Consumer group | Um leitor com seu próprio marcador; vários leitores, mesmo livro, marcadores independentes |
| Lag | Quantas páginas o leitor ainda não leu |

Mostre no painel: os sete tópicos e os contadores subindo. Depois `rpk group describe
risk-worker-group` para ver offset e lag de verdade.

Sobre o Redpanda, três frases bastam: implementa a **API do Kafka**, é um binário em C++ sem JVM e
sem coordenador externo, e por isso sobe em um container. O cliente Python é um cliente Kafka
comum — trocar de broker é mudar uma variável de ambiente.

> Ideia central: o log não é fila. Na fila a mensagem some quando é lida; no log ela fica, e cada
> leitor tem seu próprio marcador.

## Bloco 3 · Comando e evento (0:10 – 0:14)

| | Comando | Evento |
| --- | --- | --- |
| Analogia | Pedido no balcão | Nota fiscal emitida |
| Pode ser recusado? | Sim | Não, já aconteceu |
| Exemplo | `order.requested` | `trade.executed` |
| Tópico | `*.commands` | `*.events` |

Mostre o `POST /orders` respondendo `202` e o `GET` ainda devolvendo 404 por um instante. Esse
intervalo é a arquitetura aparecendo: a escrita só garante que o pedido entrou no log.

Mostre um envelope no Console: `type`, `key`, `correlation_id`, `payload`. Explique que o
`correlation_id` é o que permite seguir uma ordem por quatro tópicos.

> Ideia central: separar quem pede de quem decide. O comando é um pedido; o evento é o que o dono
> daquela decisão respondeu.

## Bloco 4 · A arquitetura do mock (0:14 – 0:21)

Abra o diagrama de `docs/architecture.md` e o painel lado a lado.

| Serviço | Responsabilidade | Estado próprio |
| --- | --- | --- |
| `ledger-worker` | Fonte da verdade de caixa e posição, liquidação | Saldos e posições |
| `risk-worker` | Reserva dinheiro ou ativo e aceita/recusa | Réplica dos saldos |
| `matching-worker` | Book por símbolo, cruzamento, fills | Book |
| `api` | Publica comandos e serve leitura | Read models |

Percorra a vida de uma ordem na tabela **Trigger and reaction** de `docs/architecture.md`,
apontando cada passo na fita do painel: `order.requested` → `order.accepted` → `trade.executed` →
`ledger.entry_recorded`.

Termine matando o matching: `docker compose stop matching-worker`. Ordens continuam sendo aceitas,
`trades.events` congela, nada quebra. Suba de volta e ele processa a fila. É a resposta visual à
pergunta do Bloco 1.

> Ideia central: cada serviço é uma dobra do log. Nenhum chama o outro.

## Bloco 5 · As decisões (0:21 – 0:27)

Esta é a parte que diferencia quem montou de quem copiou. Uma frase por decisão:

| Decisão | Por quê | O preço |
| --- | --- | --- |
| Réplica de saldo dentro do risk | Decide sem chamada síncrona ao ledger | Consistência eventual: a réplica pode estar milissegundos atrás |
| Ledger como fonte única da verdade | Alguém precisa ter a palavra final sobre dinheiro | Duas cópias da mesma lógica de liquidação |
| Comandos e eventos em tópicos separados | Recusar um pedido é normal; recusar um fato não faz sentido | Mais tópicos para administrar |
| Chave por `account_id` nos comandos | Garante ordem dos comandos de uma mesma conta | Conta muito ativa concentra carga numa partição |
| Chave por `symbol` nos eventos de ordem | O book de um papel precisa de ordem total | Um símbolo não escala além de uma partição |
| Estado em memória, sem banco | Deixa claro que o log é a verdade | Restart perde o estado; precisa de snapshot |
| Commit manual do offset após o handler | Nunca perde mensagem | At-least-once: pode reprocessar, e os handlers ainda não são idempotentes |
| `Decimal` em todo lugar, serializado como string | Dinheiro com float é bug garantido | Conversão explícita em toda fronteira |
| `available` e `reserved` separados | O estado intermediário fica visível | Mais campos para manter coerentes |
| Regra de negócio fora dos workers | `services/` é testável sem broker | Uma camada a mais de indireção |
| Leitura pela projeção, escrita por comando | Leitura não compete com escrita | A leitura é eventual: `202` e espere |

Se tiver que escolher três para aprofundar: réplica no risk, chave de partição e at-least-once.

## Bloco 6 · Limites e próximos passos (0:27 – 0:30)

| Limite atual | Caminho |
| --- | --- |
| Estado perdido no restart | Snapshot em tópico compactado |
| Handlers não idempotentes | Deduplicação por `event_id` |
| JSON cru no payload | Avro ou Protobuf no Schema Registry |
| Fills emitidos só para o agressor | Emitir também para o passivo |
| Sem tratamento de erro fatal | Enviar para `trading.dead.letter` |

Feche com a frase que resume o projeto: **o log é a fonte da verdade, e todo serviço é uma dobra
sobre ele.**

## Perguntas que vão aparecer

| Pergunta | Resposta curta |
| --- | --- |
| "Se dois serviços leem o mesmo tópico, um rouba a mensagem do outro?" | Não. Grupos diferentes leem tudo, cada um no seu offset. Dentro de um grupo, cada partição tem um dono só |
| "Perde mensagem se o serviço cair no meio?" | Não. O offset só avança depois que o handler termina |
| "E mensagem repetida?" | Pode acontecer — é at-least-once. Hoje é dívida conhecida; a solução é deduplicar por `event_id` |
| "Como escala o matching?" | Particionando por símbolo: cada partição tem um dono, e o book vive nesse dono |
| "Por que não usar banco?" | O mock existe para mostrar o log como verdade. Em produção teria snapshot e banco de leitura |
| "Kafka ou Redpanda?" | Mesma API. Trocar é mudar `REDPANDA_BROKERS` |
| "Existe ordem entre tópicos diferentes?" | Não. Só dentro de uma partição |
| "Como se debuga isso?" | `correlation_id` no Console: uma ordem inteira aparece atravessando os tópicos |
| "Por que 202 e não 201?" | A API não sabe se a ordem foi aceita; ela só garante que o pedido entrou no log |
