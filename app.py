import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import io
import re

# Configuração da página
st.set_page_config(page_title="TROPA DO ADV", layout="centered")

st.title("⚖️ Sistema de Alvarás - TROPA DO ADV")

# Área de texto para colar a live
texto_bruto = st.text_area("Cole as informações da live aqui:", height=300)

def gerar_pdf(texto):
    # Lógica original de extração de dados
    processo = re.search(r"(?:PROCESSO|Processo):\s*([\d\.\-\/]+)", texto)
    valor = re.search(r"(?:VALOR|Valor|valor):\s*[R$\s]*([\d\.,]+)", texto)
    
    num_processo = processo.group(1) if processo else "NÃO INFORMADO"
    valor_total = valor.group(1) if valor else "0,00"
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # Tenta carregar o template original
    try:
        can.drawImage("template.png", 0, 0, width=595, height=842)
    except:
        pass

    # Formatação do texto no PDF (Posições originais)
    can.setFont("Helvetica-Bold", 12)
    can.drawString(110, 680, f"PROCESSO: {num_processo}")
    can.drawString(110, 660, f"VALOR: R$ {valor_total}")
    
    # Restante do texto (Corpo da sentença)
    can.setFont("Helvetica", 10)
    linhas = texto.split('\n')
    y_pos = 600
    for linha in linhas:
        if y_pos > 100:
            can.drawString(100, y_pos, linha)
            y_pos -= 15
            
    can.save()
    packet.seek(0)
    return packet, num_processo

if st.button("GERAR MEU ALVARÁ ORIGINAL"):
    if texto_bruto:
        pdf_ready, nome_proc = gerar_pdf(texto_bruto)
        st.success(f"Alvará do processo {nome_proc} gerado!")
        st.download_button(
            label="📥 BAIXAR PDF AGORA",
            data=pdf_ready,
            file_name=f"Alvara_{nome_proc}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("Por favor, cole os dados primeiro.")
