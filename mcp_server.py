import argparse
import asyncio
import os
import platform
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import psutil
from fastmcp import FastMCP


SYSTEM = platform.system()
ROOT = os.environ["SystemDrive"] + "\\" if SYSTEM == "Windows" else "/"
PROC = Path("/proc")


@asynccontextmanager
async def lifespan(_server: FastMCP):
    if SYSTEM == "Windows":
        # O psutil leva cinco segundos para coletar a primeira amostra no Windows.
        psutil.getloadavg()
        await asyncio.sleep(5)
    yield {}


mcp = FastMCP(
    name="Monitoramento do Computador",
    instructions="Consulta métricas do Windows ou Linux em que o servidor está rodando.",
    lifespan=lifespan,
)


@mcp.tool(name="cpuName")
def cpu_name() -> str:
    """Devolve o modelo do processador ou sua arquitetura se o modelo estiver indisponível."""
    if SYSTEM == "Windows":
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            ) as key:
                name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        except OSError:
            name = ""
        return name.strip() or platform.processor() or platform.machine()

    model_fields = {"model name", "Processor", "cpu", "uarch"}
    with (PROC / "cpuinfo").open(encoding="utf-8") as cpuinfo:
        for line in cpuinfo:
            field, _, value = line.partition(":")
            model = value.strip()
            if field.strip() in model_fields and model:
                return model

    # shortcut: usa a arquitetura se o kernel omitir o modelo; amplie para SoCs específicos se necessário.
    return platform.machine()


@mcp.tool(name="availableRoot")
def available_root() -> dict[str, int]:
    """Devolve o espaço disponível, em bytes, na unidade do Windows ou na raiz / do Linux."""
    return {"bytes": shutil.disk_usage(ROOT).free}


@mcp.tool(name="sizeRoot")
def size_root() -> dict[str, int]:
    """Devolve a capacidade total, em bytes, da unidade do Windows ou da raiz / do Linux."""
    return {"bytes": shutil.disk_usage(ROOT).total}


@mcp.tool(name="kernelVersion")
def kernel_version() -> str:
    """Devolve a versão e build do Windows NT ou a versão do kernel Linux."""
    return platform.version() if SYSTEM == "Windows" else platform.release()


@mcp.tool(name="availableRAM")
def available_ram() -> dict[str, int]:
    """Devolve, em bytes, a RAM estimada para novas aplicações sem usar swap."""
    return {"bytes": psutil.virtual_memory().available}


@mcp.tool
def tasks() -> int:
    """Devolve o número de processos do sistema, incluindo os que estão aguardando."""
    return len(psutil.pids())


@mcp.tool(name="systemLoad")
def system_load() -> dict[str, float]:
    """Devolve a carga média em 1, 5 e 15 minutos, estimada pela fila de CPU no Windows."""
    one, five, fifteen = psutil.getloadavg()
    return {"min_1": one, "min_5": five, "min_15": fifteen}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inicia o servidor MCP de monitoramento para Windows e Linux."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta do servidor.")
    args = parser.parse_args()
    if SYSTEM not in {"Windows", "Linux"}:
        parser.exit(1, "Execute o servidor em Windows ou Linux.\n")

    mcp.run(transport="http", host=args.host, port=9000, path="/mcp")


if __name__ == "__main__":
    main()
