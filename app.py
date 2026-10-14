import streamlit as st
from core import (CAMPOS, VOOS, NAO_APLICA, TIPOS_EMISSAO, FORMAS_PAGAMENTO, PARCELAS, PRODUTOS,
                  OK, AGUARDANDO, validar, gerar_remarks)

st.set_page_config(page_title="Remarks OBT", page_icon="📝", layout="wide")
st.markdown(
    """<style>
    .block-container {padding-top: 1.2rem; padding-bottom: 1rem;}
    div[data-testid="stVerticalBlock"] {gap: 0.35rem;}
    div[data-testid="stCaptionContainer"] {margin-top: -0.3rem;}
    </style>""",
    unsafe_allow_html=True,
)
st.markdown("### REMARKs OBTs")

# Chaves de widget; session_state é isolado por sessão/aba de cada usuário.
K = {k: f"w_{k}" for k, _ in CAMPOS}
LABEL = dict(CAMPOS)
RESETA_NONE = ("voo", "tipo", "fop", "produto", "parcelas", "data")


def _limpar():
    for k, _ in CAMPOS:
        st.session_state[K[k]] = None if k in RESETA_NONE else ""


def _on_fop():
    """IV/GR: cartão = NÃO e parcelas = 0x (travados). VP/CC: cartão começa com 'CP-' e parcelas livre."""
    fop = st.session_state.get(K["fop"])
    cartao = st.session_state.get(K["cartao"]) or ""
    if fop in ("IV", "GR"):
        st.session_state[K["cartao"]] = "NÃO"
        st.session_state[K["parcelas"]] = "0x"
    elif fop in ("VP", "CC"):
        if cartao.strip().upper() in ("", "NÃO"):
            st.session_state[K["cartao"]] = "CP-"
        if cartao.strip().upper() == "NÃO":  # veio de IV/GR: parcelas volta a ser escolha do usuário
            st.session_state[K["parcelas"]] = None


# Resultado no topo (preenchido depois de ler os campos) + botão de limpar
topo_txt, topo_btn = st.columns([6, 1], vertical_alignment="bottom")
resultado = topo_txt.empty()
topo_btn.button("Limpar campos", on_click=_limpar, use_container_width=True)

HELP = {
    "voo": "Nacional (D) ou Internacional (I). Internacional habilita a companhia mandatória.",
    "ticket": "Formato #1234567 (até 7 dígitos).",
    "tipo": "OFF = emissão offline, ON = online.",
    "fop": "VP = cartão da agência; IV = invoice; GR = órgão governamental (só cia aérea); CC = cartão cliente.",
    "cartao": "CP-XXXX (4 últimos dígitos) ou NÃO.",
    "markup": "Valor total do markup. Se não houver colocar 0.",
    "fee": "Valor do FEE/RC da consolidadora. Se não houver colocar 0.",
    "incentivo": "Valor do incentivo acordado. Se não houver colocar 0.",
    "rav": "RAV para compras CC direto no emissor. Se não houver colocar 0.",
    "produto": "Código do produto a ser alimentado no Wintour.",
    "parcelas": "0x se não houver parcelamento e 1x para a vista",
    "data": "Data da emissão hoje.",
    "cia": "Código de 2 letras da companhia mandatória, caso seja internacional",
}
SEL = {"voo": VOOS, "tipo": TIPOS_EMISSAO, "fop": FORMAS_PAGAMENTO, "produto": PRODUTOS, "parcelas": PARCELAS}



PLACEHOLDER = {"ticket": "#1234567", "cartao": "CP-0000", "markup": "0", "fee": "0",
                "incentivo": "0", "rav": "0", "cia": "XX"}
# Ordem de preenchimento/Tab: cada linha é um st.columns próprio, então Tab segue para a direita.
LINHAS = [
    ["voo", "cia", "ticket", "tipo", "fop"],
    ["cartao", "parcelas", "produto", "data", None],
    ["markup", "fee", "incentivo", "rav", None],
]


def _fmt_status(s):
    if s == OK:
        return ":green[✓ OK]"
    if s in (AGUARDANDO, NAO_APLICA):
        return f":gray[{s}]"
    if s.startswith(("Insira", "Selecione")):
        return f":blue[{s}]"
    return f":red[{s}]"


dados, slots = {}, {}
for linha in LINHAS:
    cols = st.columns(len(linha))
    for col, key in zip(cols, linha):
        if key is None:
            continue
        label = LABEL[key]
        travado = (
            (key == "cia" and dados.get("voo") != "Internacional")
            or (key in ("cartao", "parcelas") and dados.get("fop") in ("IV", "GR"))
        )
        with col:
            if key in SEL:
                dados[key] = st.selectbox(label, SEL[key], index=None, key=K[key], placeholder="Selecione",
                                          disabled=travado,
                                          on_change=_on_fop if key == "fop" else None)
            elif key == "data":
                dados[key] = st.date_input(label, value=None, format="DD/MM/YYYY", key=K[key])
            else:
                dados[key] = st.text_input(label, key=K[key], placeholder=PLACEHOLDER.get(key, ""),
                                           disabled=travado, max_chars=7 if key == "cartao" else None)
            slots[key] = st.empty()

for key, status in validar(dados).items():
    slots[key].caption(_fmt_status(status))

texto = gerar_remarks(dados)
with resultado.container():
    st.caption("Informação para inserir no Remarks do OBT (Backoffice)")
    if texto:
        st.code(texto, language=None)  # botão de copiar embutido
    else:
        st.info("Preencha/corrija os campos para gerar o texto.")

with st.expander("Ajuda dos campos"):
    for k, _ in CAMPOS:
        st.markdown(f"**{LABEL[k]}** — {HELP[k]}")
