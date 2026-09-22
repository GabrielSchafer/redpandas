# Roteiro do vídeo — 5 minutos, sem narração

Vídeo mudo: o painel roda sozinho e as legendas explicam. Este arquivo tem a sequência,
as legendas sugeridas e o vocabulário para escrever a descrição ou gravar uma narração depois.

## Preparação

| Item | Valor |
| --- | --- |
| Terminal | 120×40 no mínimo, fonte 16–18pt, tema escuro |
| Painéis | Monitor ocupando ~70% da tela, tráfego embaixo |
| Prompt | `export PS1="$ "` |
| Log limpo | `make down && make up`, esperar os 6 containers |
| Ritmo | `python scripts/traffic.py --interval 2.5` |
| Gravação | QuickTime (janela do terminal) ou `asciinema rec` |

Deixe os comandos no histórico para não digitar ao vivo.

## Sequência

| Tempo | Na tela | Comando | Legenda sugerida |
| --- | --- | --- | --- |
| 0:00 | Lista de containers | `docker compose ps` | "6 processos: 1 broker, 1 API, 3 workers" |
| 0:20 | Painel vazio, contadores em zero | `make monitor` | "Nenhum evento ainda — o painel é o log" |
| 0:50 | Bots começam a publicar | `make traffic` | "3 bots enviando 1 ordem a cada 2,5s" |
| 1:10 | Contadores subindo em cascata | — | "orders.commands → orders.events → trades.events" |
| 1:40 | Fita rolando | — | "Cada linha é um evento real no log" |
| 2:10 | Fita, linhas verdes | — | "Verde = negócio executado" |
| 2:30 | Painel BOOK | — | "Book reconstruído: venda em cima, compra embaixo" |
| 2:50 | Painel ACCOUNTS, coluna `reserved` | — | "Ordem aceita trava o dinheiro, não gasta" |
| 3:10 | Coluna da posição mudando | — | "Posição só muda depois do negócio liquidar" |
| 3:25 | Linha vermelha na fita | — | "Risco recusou: saldo insuficiente" |
| 3:50 | Um serviço morre | `docker compose stop matching-worker` | "Matando o serviço de matching" |
| 4:05 | trades.events congela, resto continua | — | "Ordens seguem entrando, nada quebra" |
| 4:25 | Serviço volta | `docker compose start matching-worker` | "Ele volta e processa a fila acumulada" |
| 4:45 | Painel normalizado | — | "O log é a fonte da verdade" |
| 5:00 | Fim | — | "Redpanda · Python · zero banco de dados" |

O bloco de 3:50 é o mais importante do vídeo: é a única parte que mostra algo que um
diagrama não mostra. Se faltar tempo, corte o trecho de 2:30 e preserve esse.

## Vocabulário

Termos para as legendas, a descrição do vídeo ou uma narração posterior.

| Termo | Uma linha |
| --- | --- |
| Redpanda | Broker compatível com a API do Kafka, um binário só, sem JVM |
| Tópico | Log append-only com nome; só se escreve no fim |
| Partição | Fatia do tópico; a ordem é garantida dentro de uma partição |
| Chave | Campo que decide a partição — aqui `account_id` ou `symbol` |
| Offset | Posição da mensagem na partição; ler é avançar offset |
| Consumer group | Nome sob o qual um serviço lê e guarda offset |
| Lag | Quantas mensagens o grupo ainda não processou |
| Comando | Pedido que pode ser recusado (`order.requested`) |
| Evento | Fato consumado (`trade.executed`) |
| Envelope | Formato único: tipo, chave, `correlation_id`, payload |
| Correlation id | Liga todos os eventos originados do mesmo comando |
| Projeção | Estado de leitura construído dobrando o log |
| Réplica | Cópia local do saldo que o risk monta lendo eventos |
| Reserva | Dinheiro travado (`reserved`) enquanto a ordem está no book |
| Book | Ofertas de compra e venda, ordenadas por preço e chegada |
| Fill parcial | Execução de parte da ordem; o resto continua no book |
| Liquidação | Troca de dinheiro por ativo depois do negócio |
| At-least-once | Mensagem pode chegar repetida; nunca sumir |
| Replay | Reler o tópico do início para reconstruir estado |

## Frases de apoio

Para descrição do vídeo ou legenda de abertura:

- "Mock de um banco de trade orientado a eventos, em Python, sobre Redpanda."
- "Nenhum serviço chama outro: todos reagem ao mesmo log."
- "Três workers independentes — risco, matching e ledger — cada um com seu estado em memória."
- "Sem banco de dados: o log é a fonte da verdade."
