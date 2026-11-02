"""Explora e captura as telas do Airflow, usando o Edge instalado na maquina.

    python docs/capturar_telas.py descobrir
    python docs/capturar_telas.py capturar <dag_id> <run_id> <arquivo.png> <grupos>

O modo ``descobrir`` imprime as rotas e os botoes da tela da DAG. O modo
``capturar`` abre uma execucao no grafo e salva em docs/imagens/ o recorte dos
nos, com ``grupos`` valendo expandido, recolhido ou sem-grupos. Requer
``playwright`` e o Airflow em http://localhost:8080.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import Page, sync_playwright

BASE = "http://localhost:8080"
DIR_IMAGENS = Path(__file__).resolve().parent / "imagens"
USUARIO = SENHA = "airflow"


def entrar(pagina: Page) -> None:
    pagina.goto(f"{BASE}/auth/login/", wait_until="networkidle")
    pagina.locator("input[name='username']").fill(USUARIO)
    pagina.locator("input[name='password']").fill(SENHA)
    pagina.locator("input[type='submit'], button[type='submit']").first.click()
    pagina.wait_for_url(lambda url: "login" not in url, timeout=20_000)
    pagina.wait_for_load_state("networkidle")


def descobrir(pagina: Page) -> None:
    pagina.goto(f"{BASE}/dags/etl_adventureworks_incremental", wait_until="networkidle")
    pagina.wait_for_timeout(2500)
    print("URL:", pagina.url)
    print("Titulo:", pagina.title())
    for papel in ("button", "tab", "link"):
        for item in pagina.get_by_role(papel).all()[:50]:
            rotulo = (item.get_attribute("aria-label") or item.inner_text() or "").strip()
            if rotulo:
                print(f"{papel}: {rotulo[:70]!r}")
    pagina.screenshot(path=str(DIR_IMAGENS / "_descoberta.png"))


def recorte_do_grafo(pagina: Page, margem: int = 10) -> dict:
    """Calcula o retangulo que envolve todos os nos do grafo."""
    caixas = [no.bounding_box() for no in pagina.locator(".react-flow__node").all()]
    caixas = [caixa for caixa in caixas if caixa]
    x0 = min(caixa["x"] for caixa in caixas) - margem
    y0 = min(caixa["y"] for caixa in caixas) - margem
    x1 = max(caixa["x"] + caixa["width"] for caixa in caixas) + margem
    y1 = max(caixa["y"] + caixa["height"] for caixa in caixas) + margem
    return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}


def capturar(pagina: Page, dag: str, execucao: str, arquivo: str, grupos: str) -> None:
    pagina.goto(f"{BASE}/dags/{dag}/runs/{quote(execucao, safe='')}", wait_until="networkidle")
    pagina.wait_for_timeout(2000)
    pagina.add_style_tag(
        content=".react-flow__minimap, .react-flow__controls, .react-flow__panel,"
                ".react-flow__attribution, .react-flow__background {display: none !important;}"
    )
    fechar_painel = pagina.get_by_role("button", name="Collapse Details Panel")
    if fechar_painel.count():
        fechar_painel.first.click()
        pagina.wait_for_timeout(800)
    grafo = pagina.get_by_role("button", name="Show Graph")
    if grafo.count():
        grafo.first.click()
        pagina.wait_for_timeout(1500)
    # O grafo abre com os grupos recolhidos, e o botao de recolher fica desabilitado.
    if grupos == "expandido":
        pagina.get_by_role("button", name="Expand all task groups").first.click()
        pagina.wait_for_timeout(2500)
    pagina.screenshot(path=str(DIR_IMAGENS / arquivo), clip=recorte_do_grafo(pagina))
    print(f"Tela salva em {DIR_IMAGENS / arquivo}")


def main() -> None:
    DIR_IMAGENS.mkdir(exist_ok=True)
    with sync_playwright() as motor:
        navegador = motor.chromium.launch(channel="msedge", headless=True)
        contexto = navegador.new_context(
            viewport={"width": 1800, "height": 1000}, device_scale_factor=3,
            color_scheme="light", locale="en-US",
        )
        pagina = contexto.new_page()
        entrar(pagina)
        if sys.argv[1] == "descobrir":
            descobrir(pagina)
        else:
            capturar(pagina, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        navegador.close()


if __name__ == "__main__":
    main()
