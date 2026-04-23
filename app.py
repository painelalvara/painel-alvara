import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import io
import re

st.set_page_config(page_title="TROPA DO ADV", layout="centered")

st.title("⚖️ Sistema de Alvarás - TROPA DO ADV")

texto_bruto = st.text_area("Cole as informações aqui:", height=300)

def gerar_pdf(texto):
    # Procura processo e valor de um jeito mais certeiro
    proc_match = re.search(r"(?:PROCESSO|PROC|Processo):?\s*([\d\.\-\/]+)", texto, re.IGNORECASE)
    val_match = re.search(r"(?:VALOR|R\$):?\s*([\d\.,]+)", texto, re.IGNORECASE)
    
    num_proc = proc_match.group(1) if proc_match else "NAO_INFORMADO"
    valor_final = val_match.group(1) if val_match else "0,00"
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # Carrega o seu template
    try:
        can.drawImage("template.png", 0, 0, width=595, height=842)
    except:
        pass

    # --- AQUI É ONDE A GENTE ARRUMA A BAGUNÇA ---
    can.setFillColorRGB(0, 0, 0) # Texto preto
    
    # 1. Coloca o Processo e Valor em locais fixos (ajuste os números se precisar)
    can.setFont("Helvetica-Bold", 14)
    can.drawString(120, 710, f"PROCESSO: {num_proc}")
    can.drawString(120, 690, f"VALOR: R$ {valor_final}")
    
    # 2. Coloca o resto do texto separado, linha por linha
    can.setFont("Helvetica", 11)
    y = 650
    linhas = texto.split('\n')
    for linha in linhas:
        if linha.strip(): # Só escreve se a linha não estiver vazia
            can.drawString(100, y, linha.strip())
            y -= 18 # Pula para a linha de baixo (espaçamento)
            if y < 50: # Cria nova página se acabar o espaço
                can.showPage()
                y = 800
            
    can.save()
    packet.seek(0)
    return packet, num_proc

if st.button("GERAR ALVARÁ"):
    if texto_bruto:
        pdf_ready, nome_proc = gerar_pdf(texto_bruto)
        st.success(f"Alvará gerado!")
        st.download_button(
            label="📥 BAIXAR AGORA",
            data=pdf_ready,
            file_name=f"Alvara_{nome_proc}.pdf",
            mime="application/pdf"
        )
