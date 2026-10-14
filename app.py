import streamlit as st
from core import (CAMPOS, TIPOS_EMISSAO, FORMAS_PAGAMENTO, PARCELAS, PRODUTOS,
                  OK, AGUARDANDO, validar, gerar_remarks)

st.set_page_config(page_title="Remarks OBT", page_icon="📝", layout="centered")
st.title("REMARKs OBTs")
st.caption("Preencha os campos. O texto do Remarks é gerado quando tudo estiver correto. "
           "Cada aba do navegador tem sua própria sessão independente.")

# Chaves de widget; session_state é isolado por sessão/aba de cada usuário.
K = {k: f"w_{k}" for k, _ in CAMPOS}
LIMPA_ORIGINAL = ["ticket", "tipo", "fop", "cartao", "markup", "fee", "incentivo"]  # C3:C9 do VBA


def _reset(chaves):
    for k in chaves:
        st.session_state[K[k]] = None if k in ("tipo", "fop", "produto", "parcelas", "data") else ""


st.button("Limpar campos (C3:C9)", on_click=lambda: _reset(LIMPA_ORIGINAL),
          help="Mesmo comportamento da macro original: limpa Ticket até Incentivo.")
st.button("Limpar tudo", on_click=lambda: _reset([k for k, _ in CAMPOS]))

HELP = {
    "ticket": "Formato #1234567 (até 7 dígitos).",
    "tipo": "OFF = emissão offline, ON = online.",
    "fop": "VP = cartão da agência; IV = invoice; GR = órgão governamental (só cia aérea); CC = cartão cliente.",
    "cartao": "CP-XXXX (4 últimos dígitos) ou NÃO.",
    "markup": "Valor total do markup, ou NÃO. Se não houver, 0.",
    "fee": "Valor do FEE/RC da consolidadora, ou NÃO. Se não houver, 0.",
    "incentivo": "Valor do incentivo acordado, ou NÃO. Se não houver, 0.",
    "rav": "RAV para compras CC direto no emissor, ou NÃO. Se não houver, 0.",
    "produto": "Código do produto a ser alimentado no Wintour.",
    "parcelas": "0x se não houver parcelamento.",
    "data": "Entre 01/01/2000 e hoje.",
    "cia": "Código de 2 letras da companhia mandatória.",
}
SEL = {"tipo": TIPOS_EMISSAO, "fop": FORMAS_PAGAMENTO, "produto": PRODUTOS, "parcelas": PARCELAS}

dados = {}
for key, label in CAMPOS:
    c1, c2 = st.columns([3, 2])
    with c1:
        if key in SEL:
            dados[key] = st.selectbox(label, SEL[key], index=None, key=K[key], help=HELP[key])
        elif key == "data":
            dados[key] = st.date_input(label, value=None, format="DD/MM/YYYY", key=K[key], help=HELP[key])
        else:
            dados[key] = st.text_input(label, key=K[key], help=HELP[key])
    status = validar({**dados})[key]
    with c2:
        st.write("")
        st.write("")
        if status == OK:
            st.success(status)
        elif status == AGUARDANDO:
            st.warning(status)
        elif status.startswith("Insira"):
            st.info(status)
        else:
            st.error(status)

st.divider()
st.subheader("Informação para inserir no Remarks do OBT (Backoffice)")
texto = gerar_remarks(dados)
if texto:
    st.code(texto, language=None)  # botão de copiar embutido
else:
    st.info("Preencha/corrija os campos acima para gerar o texto.")
