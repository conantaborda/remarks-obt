"""Regras de validação e geração do Remarks OBT (portadas da planilha v2.4)."""
from __future__ import annotations
import re
from datetime import date
from typing import Optional

# Listas da aba "Base"
TIPOS_EMISSAO = ["OFF", "ON"]
FORMAS_PAGAMENTO = ["VP", "IV", "GR", "CC"]
VOOS = ["Nacional", "Internacional"]
PARCELAS = [f"{i}x" for i in range(0, 13)]
PRODUTOS = ["TKT", "REM", "AS", "BG", "HTL", "ALIM", "FLU", "SEG",
            "TAXIAEREO", "TRF", "TREM", "TKTG", "HTLG", "CAR", "ROD"]

OK = "OK"
AGUARDANDO = "Aguardando informação"
NAO_APLICA = "Não se aplica"
NAO = "NÃO"
MAX_VALOR = 999999.99

CAMPOS = [
    ("voo", "Nacional ou Internacional"),
    ("ticket", "Ticket Zoho Desk"),
    ("tipo", "Tipo de emissão"),
    ("fop", "Forma de pagamento"),
    ("cartao", "Cartão utilizado"),
    ("markup", "Markup individual"),
    ("fee", "FEE Consolidadora (RC)"),
    ("incentivo", "Incentivo/comissão"),
    ("rav", "RAV (se aplicável)"),
    ("produto", "Código do produto"),
    ("parcelas", "Parcelamento no cartão"),
    ("data", "Data de Emissão"),
    ("cia", "Cia mandatória"),
]


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def _eq(a: str, b: str) -> bool:  # comparação do Excel é case-insensitive
    return a.casefold() == b.casefold()


def parse_valor(txt: str) -> Optional[float]:
    """Aceita '12,50' ou '12.50'. Retorna None se não for número."""
    t = txt.strip().replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t):  # 1.234,56
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    try:
        return float(t) if re.fullmatch(r"\d+(\.\d+)?|\.\d+", t) else None
    except ValueError:
        return None


def valida_ticket(v) -> str:
    v = _s(v)
    if not v:
        return "Insira o número do ticket do cliente Zoho Desk."
    if re.fullmatch(r"#\d+", v) and int(v[1:]) < 10_000_000:
        return OK
    return "Corrigir o número do ticket do cliente Zoho Desk"


def valida_tipo(v) -> str:
    v = _s(v)
    if not v:
        return "Insira o tipo de emissão ON ou OFF"
    return OK if v.upper() in ("ON", "OFF") else "Corrigir tipo emissão (C4)"


def valida_fop(v) -> str:
    v = _s(v)
    if not v:
        return "Insira a forma de pagamento utilizada no fornecedor."
    return OK if v.upper() in FORMAS_PAGAMENTO else "Corrigir forma de pagamento utilizada (B3)"


def valida_cartao(v) -> str:
    v = _s(v)
    if not v:
        return "Insira o cartão utilizado ou 'NÃO'"
    if _eq(v, NAO) or (v[:3].upper() == "CP-" and len(v) == 7 and v[-4:].isdigit()):
        return OK
    return "Corrigir o campo Cartão Utilizado"


def _valida_valor(v, msg: str, vazio: str) -> str:
    v = _s(v)
    if not v:
        return vazio
    if _eq(v, NAO):
        return OK
    n = parse_valor(v)
    return OK if n is not None and 0 <= n <= MAX_VALOR else msg


def valida_markup(v): return _valida_valor(v, "Corrigir Markup Total", "Insira o markup (0 se não houver)")
def valida_fee(v): return _valida_valor(v, "Corrigir Fee/RC", "Insira o FEE/RC (0 se não houver)")
def valida_incentivo(v): return _valida_valor(v, "Corrigir Incentivo", "Insira o incentivo (0 se não houver)")
def valida_rav(v): return _valida_valor(v, "Corrigir RAV", "Insira o RAV (0 se não houver)")


def valida_produto(v) -> str:
    return "Insira o codigo do produto" if not _s(v) else OK


def valida_parcelas(v) -> str:
    v = _s(v)
    if not v:
        return "Selecione o parcelamento (0x se não houver)"
    return OK if v.lower() in PARCELAS else "Corrigir Parcela"


def valida_data(v) -> str:
    if v is None or v == "":
        return "Insira a data de emissão"
    return OK if date(2000, 1, 1) <= v <= date.today() else "Data inválida"


def valida_voo(v) -> str:
    v = _s(v)
    if not v:
        return "Selecione se o voo é Nacional ou Internacional"
    return OK if v in VOOS else "Corrigir tipo de voo"


def valida_cia(v, voo=None) -> str:
    if _s(voo) == "Nacional":
        return NAO_APLICA
    v = _s(v)
    if not v:
        return "Insira o codigo da CIA"
    return "Código Incorreto" if len(v) != 2 else OK


VALIDADORES = {
    "voo": valida_voo,
    "ticket": valida_ticket, "tipo": valida_tipo, "fop": valida_fop,
    "cartao": valida_cartao, "markup": valida_markup, "fee": valida_fee,
    "incentivo": valida_incentivo, "rav": valida_rav, "produto": valida_produto,
    "parcelas": valida_parcelas, "data": valida_data, "cia": valida_cia,
}


def _fmt_valor(v) -> str:
    """Valor para o texto final: vazio -> 0; 'NÃO' mantém; número em formato pt-BR."""
    v = _s(v)
    if not v:
        return "0"
    if _eq(v, NAO):
        return v
    n = parse_valor(v)
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def validar(d: dict) -> dict:
    st = {k: VALIDADORES[k](d.get(k)) for k, _ in CAMPOS if k != "cia"}
    st["cia"] = valida_cia(d.get("cia"), d.get("voo"))
    return st


def gerar_remarks(d: dict) -> str:
    """Retorna o texto do Remarks, ou '' se houver pendências (igual à célula C16)."""
    st = validar(d)
    for k, _ in CAMPOS:
        if st[k] in (OK, NAO_APLICA):  # "Aguardando informação" também bloqueia a geração
            continue
        return ""
    fop = _s(d.get("fop"))
    cartao = "não" if fop.upper() in ("IV", "GR") else _s(d.get("cartao"))
    partes = [
        _s(d.get("ticket")), _s(d.get("tipo")), fop, cartao,
        _fmt_valor(d.get("markup")), _fmt_valor(d.get("fee")),
        _fmt_valor(d.get("incentivo")), _fmt_valor(d.get("rav")),
        _s(d.get("produto")), _s(d.get("parcelas")),
        d["data"].strftime("%d/%m/%Y"),
    ]
    texto = ";".join(p for p in partes if p != "")  # TEXTJOIN ignora vazios
    # Marcador D (nacional) / I (internacional) sempre presente; cia só se internacional.
    if _s(d.get("voo")) == "Internacional":
        return f"{texto};I;{_s(d.get('cia'))}"
    return f"{texto};D;"
