import streamlit as st
from core import (CAMPOS, VOOS, NAO_APLICA, TIPOS_EMISSAO, FORMAS_PAGAMENTO, PARCELAS, PRODUTOS,
                  OK, AGUARDANDO, validar, gerar_remarks)

st.set_page_config(page_title="Remarks OBT", page_icon="📝", layout="wide")
st.markdown("### REMARKs OBTs")

# Chaves de widget; session_state é isolado por sessão/aba de cada usuário.
K = {k: f"w_{k}" for k, _ in CAMPOS}
RESETA_NONE = ("voo", "tipo", "fop", "produto", "parcelas", "data")


def _limpar():
    for k, _ in CAMPOS:
        st.session_state[K[k]] = None if k in RESETA_NONE else ""


# Resultado no topo (preenchido depois de ler os campos) + botão de limpar
topo_txt, topo_btn = st.columns([5, 1], vertical_alignment="bottom")
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


def _fmt_status(s):
    if s == OK:
        return ":green[✓ OK]"
    if s in (AGUARDANDO, NAO_APLICA):
        return f":gray[{s}]"
    if s.startswith(("Insira", "Selecione")):
        return f":blue[{s}]"
    return f":red[{s}]"


COLS = 3
dados, slots = {}, {}
grade = st.columns(COLS)
for i, (key, label) in enumerate(CAMPOS):
    with grade[i % COLS]:
        if key in SEL:
            dados[key] = st.selectbox(label, SEL[key], index=None, key=K[key], help=HELP[key],
                                      placeholder="Selecione")
        elif key == "data":
            dados[key] = st.date_input(label, value=None, format="DD/MM/YYYY", key=K[key], help=HELP[key])
        else:
            dados[key] = st.text_input(label, key=K[key], help=HELP[key],
                                       disabled=(key == "cia" and dados.get("voo") != "Internacional"))
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
