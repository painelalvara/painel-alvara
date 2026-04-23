import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import io
import re

st.set_page_config(page_title="TROPA DO ADV", layout="centered")

# Estilo para ficar com a cara da Tropa
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    stButton>button { width: 100%; background-color: #000000; color: white; height: 3em; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚖️ Painel de Alvarás - TROPA DO ADV")

texto_live = st.text_area("Cole os dados brutos da live aqui:", height=250)

def extrair_dados(texto):
    # Procura os padrões no seu texto da live
    processo = re.search(r"PROCESSO:\s*([\d\.-]+)", texto)
    valor = re.search(r"VALOR:\s*R\$\s*([\d\.,]+)", texto)
    sentenca = re.search(r"SENTENÇA:\s*(.*)", texto)
    
    return {
        "processo": processo.group(1) if processo else "N/A",
        "valor": valor.group(1) if valor else "0,00",
        "sentenca": sentenca.group(1) if sentenca else "Procedente"
    }

if st.button("GERAR ALVARÁ PROFISSIONAL"):
    if texto_live:
        dados = extrair_dados(texto_live)
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # Tenta colocar o seu template de fundo
        try:
            can.drawImage("template.png", 0, 0, width=595, height=842)
        except:
            pass

        # ESCREVENDO OS DADOS NO LUGAR CERTO (Ajuste as coordenadas se precisar)
        can.setFont("Helvetica-Bold", 12)
        can.setFillColorRGB(0, 0, 0)
        
        # Posições baseadas no seu modelo antigo
        can.drawString(150, 680, f"PROCESSO: {dados['processo']}")
        can.drawString(150, 660, f"VALOR: R$ {dados['valor']}")
        
        can.setFont("Helvetica", 11)
        # Quebra o texto da sentença para não sair da folha
        text_object = can.beginText(100, 600)
        text_object.textLines(f"SENTENÇA: {dados['sentenca']}")
        can.drawText(text_object)

        can.save()
        packet.seek(0)
        
        st.success("PDF Gerado! Confira os dados abaixo:")
        st.write(f"**Processo:** {dados['processo']} | **Valor:** R$ {dados['valor']}")
        
        st.download_button(
            label="📥 BAIXAR ALVARÁ AGORA",
            data=packet,
            file_name=f"Alvara_{dados['processo']}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("Cole o texto da live para processar.")
