<h1 align="center">multiAgentesDemo</h1>
<h3 align="center">Multiagentes com SPADE + XMPP (Openfire) + Pidgin + GPT</h3>

<p align="center">
Demo prática de <b>orquestração de agentes</b> usando SPADE (XMPP) com um agente atendente que aciona agentes especialistas (cadastro, cobrança, qualidade) e consolida o retorno via GPT.
</p>

<p align="center">
<a href="https://www.youtube.com/watch?v=8nHcDpd8yFY&t=907s">
  <img src="https://img.youtube.com/vi/8nHcDpd8yFY/hqdefault.jpg" width="760" alt="Arquitetura de Multiagentes: Como Orquestrar IA para Resolver Problemas Reais (Projeto Completo)"/>
</a>
</p>

<p align="center">
<b>Arquitetura de Multiagentes: Como Orquestrar IA para Resolver Problemas Reais (Projeto Completo)</b><br/>
<sub>Clique para assistir o walkthrough do projeto</sub>
</p>

---

## O que este repositório implementa

Você conversa via XMPP (cliente Pidgin) com um agente <b>atendente</b>. Ao receber sua mensagem, ele dispara consultas paralelas para três agentes especialistas:

- <b>cadastro</b>: verifica se o ID existe e retorna dados do cliente
- <b>cobrança</b>: verifica status da assinatura
- <b>qualidade</b>: avalia qualidade de rede por um threshold

Os agentes especialistas consultam a base local `clientes_streaming.csv`. O agente atendente recebe as respostas e usa a API da OpenAI para transformar o retorno em uma orientação curta e prática.

---

## Stack (o que você precisa ter)

<b>Aplicação</b>
- Python 3.x
- SPADE (framework de agentes sobre XMPP)
- pandas (leitura da base `clientes_streaming.csv`)
- openai (SDK para chamar GPT)

<b>Infra local (XMPP)</b>
- Openfire (servidor XMPP)
- Pidgin (cliente XMPP para simular o “humano”)
- Java/JRE (para rodar o Openfire; no Windows o setup original usa Adoptium JRE 8)

---

## Estrutura do projeto (como está hoje)

```text
.
├─ abc_agents.py              # Implementação dos agentes + main() (ponto de entrada)
├─ test_agent.py              # Exemplo mínimo de envio de mensagem via SPADE
├─ clientes_streaming.csv     # Base de clientes usada pelos agentes especialistas
├─ setup.txt                  # Checklist de instalação (Openfire/Pidgin/JRE + configuração)
├─ README.md
├─ LICENSE
└─ .gitignore
```

---

## Pré-requisitos (XMPP local)

Este projeto foi pensado para rodar com Openfire + Pidgin. O caminho “mais fiel ao repo” é:

1) Instalar Java/JRE (no Windows: Adoptium JRE 8 LTS)
2) Instalar Openfire (servidor XMPP)
3) Instalar Pidgin (cliente XMPP)
4) Configurar o domínio (no setup original, `localhost`)
5) Criar usuários no Openfire e conectar via Pidgin
6) Iniciar os agentes SPADE e conversar com `usuario@dominio/recurso`

O checklist original está em `setup.txt`.

---

## Como rodar (quickstart)

### 1) Instalar libs Python

```bash
pip install spade pandas openai
```

Se você preferir, crie um `requirements.txt` depois.

### 2) Configurar a chave OpenAI

O código lê a chave do arquivo `openai_key.txt` no diretório do projeto. Crie o arquivo:

```bash
echo "SUA_CHAVE_AQUI" > openai_key.txt
```

### 3) Criar usuários no Openfire

O código inicia estes agentes (JIDs exatamente como estão no script):

- `atendente@localhost/agentic` senha `ate`
- `cadastro@localhost/agentic` senha `cad`
- `cobranca@localhost/agentic` senha `cob`
- `qualidade@localhost/agentic` senha `qua`

Crie os usuários correspondentes no Openfire (mesmo username e senha).

### 4) Subir os agentes

```bash
python abc_agents.py
```

Você deve ver logs do tipo “Atendente Online” e “Agentes iniciados”.

### 5) Conectar o “humano” via Pidgin

No Pidgin, conecte com um usuário humano criado no Openfire e defina o <b>resource</b> como `humano`.
O atendente identifica mensagens de cliente quando o sender contém `humano`.

### 6) Conversar enviando um ID

Envie para o atendente uma mensagem com o <b>ID</b> (campo `ID` do `clientes_streaming.csv`).
Exemplo: `123`.

O atendente acionará os agentes especialistas e você receberá uma resposta consolidada.

---

## Como o fluxo funciona (no código)

- Os agentes especialistas herdam `agente_suporte` e implementam `processa_base(id_cliente)` para consultar `clientes_streaming.csv`.
- O comportamento `reportar_status` recebe a mensagem, executa a consulta e responde para o remetente.
- O atendente (behaviour `interagir`) dispara mensagens para `cadastro`, `cobranca`, `qualidade`.
- Quando recebe respostas dos especialistas, ele chama GPT com um contexto curto e devolve uma recomendação para o humano.

---

## Ajustes rápidos para deixar a demo mais “produto”

1) Colocar `requirements.txt` e/ou `pyproject.toml`.
2) Trocar `openai_key.txt` por variável de ambiente (`OPENAI_API_KEY`) e ignorar no git.
3) Padronizar mensagens entre agentes (ex.: JSON) em vez de concatenar `cliente-mensagem`.
4) Adicionar um “roteador” (dispatcher) com regras explícitas (e logs) para observabilidade.
5) Criar testes de regressão com IDs conhecidos do CSV.

---

## Licença

GPL-3.0 (ver `LICENSE`).
