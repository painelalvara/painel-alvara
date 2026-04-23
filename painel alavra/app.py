import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import io

st.set_page_config(page_title="TROPA DO ADV - Painel", layout="centered")

st.title("⚖️ Sistema de Alvarás - TROPA DO ADV")
st.subheader("Gerador de Documentos Profissionais")

texto_live = st.text_area("Cole aqui os dados da live:", height=300)

if st.button("GERAR ALVARÁ EM PDF"):
    if texto_live:
        try:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            
            # Tenta carregar o seu template personalizado
            try:
                # O caminho abaixo considera que a imagem está na mesma pasta que este arquivo
                img = Image.open("painel alavra/template.png")
                can.drawImage("painel alavra/template.png", 0, 0, width=595, height=842)
            except:
                st.warning("Template não encontrado. Gerando PDF em branco.")

            # Configuração do texto (Cor preta e posição central)
            can.setFont("Helvetica", 12)
            lines = texto_live.split('\n')
            y = 650 # Posição inicial no meio do seu template
            for line in lines:
                can.drawString(100, y, line)
                y -= 20
            
            can.save()
            packet.seek(0)
            
            st.success("✅ Alvará gerado com sucesso!")
            st.download_button(
                label="📥 BAIXAR ALVARÁ AGORA",
                data=packet,
                file_name="alvara_tropa_adv.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")
    else:
        st.error("Por favor, cole os dados antes de gerar.")
