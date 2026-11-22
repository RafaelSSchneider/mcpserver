# Monitoramento do computador com MCP

O servidor roda no Windows e no Linux e expõe sete ferramentas FastMCP via Streamable HTTP em `/mcp`. As métricas descrevem o sistema em que o servidor está rodando.

| Ferramenta | Resultado |
| --- | --- |
| `cpuName` | Modelo do processador obtido do Registro do Windows ou de `/proc/cpuinfo` no Linux. |
| `availableRoot` | Espaço disponível na unidade do Windows (por exemplo, `C:\`) ou na raiz `/` do Linux, em bytes. |
| `sizeRoot` | Capacidade total dessa unidade ou sistema de arquivos, em bytes. |
| `kernelVersion` | Versão e build do Windows NT ou versão do kernel Linux, equivalente a `uname -r` no Linux. |
| `availableRAM` | RAM disponível para novas aplicações sem usar swap, em bytes. |
| `tasks` | Número de processos do sistema, incluindo os que estão aguardando. |
| `systemLoad` | Carga média em 1, 5 e 15 minutos nos campos `min_1`, `min_5` e `min_15`. No Windows, a estimativa usa a fila de CPU. No Linux, é a carga média nativa. |

## Executar e testar no Windows

Na pasta do projeto, use o PowerShell com Python 3.10 ou posterior. Se a pasta `.venv` já existir, pule o primeiro comando.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe mcp_server.py
```

O servidor aguarda cerca de cinco segundos para coletar a primeira amostra de carga no Windows. Depois que ele iniciar, use outro PowerShell na mesma pasta para testar as sete ferramentas. O modo `--check` valida os resultados sem usar LLM nem chave de API.

```powershell
.\.venv\Scripts\python.exe mcp_client.py --check
```

No Linux ou WSL, crie o ambiente com `python3 -m venv .venv-linux` e use `.venv-linux/bin/python` para instalar as dependências e executar os scripts.

Também é possível usar o [MCP Inspector](https://github.com/modelcontextprotocol/inspector) com `npx @modelcontextprotocol/inspector`. Escolha **Streamable HTTP**, conecte a `http://127.0.0.1:9000/mcp` e execute as ferramentas na aba **Tools**. Todas as chamadas usam `{}` como argumentos.

Para aceitar conexões de outra máquina na rede local, inicie o servidor com `--host 0.0.0.0` e execute o cliente com `--check --url http://IP_DO_SERVIDOR:9000/mcp`.

## Chat com OpenRouter

Cole sua [chave do OpenRouter](https://openrouter.ai/settings/keys) após `OPENROUTER_API_KEY=` no arquivo `.env` ao lado de `mcp_client.py`. No ambiente virtual do cliente, com Python 3.11 ou posterior, instale as dependências e inicie o chat.

```powershell
.\.venv\Scripts\python.exe -m pip install -U langchain langchain-mcp-adapters langchain-openrouter python-dotenv
.\.venv\Scripts\python.exe mcp_client.py
```

O padrão é [`openrouter/free`](https://openrouter.ai/openrouter/free), que seleciona um modelo gratuito compatível com chamadas de ferramentas. Para fixar um modelo gratuito específico, defina `OPENROUTER_MODEL` no `.env` com o identificador `:free` de um modelo que aceite ferramentas. Variáveis já definidas no ambiente têm prioridade sobre o arquivo.
