import streamlit as st
import re
import io
import textwrap
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from num2words import num2words

# Título da Aba
st.set_page_config(page_title="TROPA DO ADV - SISTEMA OFICIAL", layout="centered")

def obter_data_extenso():
    meses = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho", 
             7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
    hoje = datetime.now()
    return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

def formatar_cpf_cnpj(valor):
    numeros = re.sub(r'\D', '', valor)
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    return valor

def gerar_pdf_final(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    # Tenta desenhar seu fundo
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    c.setFillColorRGB(0, 0, 0) # Texto sempre preto
    
    # --- POSIÇÕES EXATAS DO SEU ORIGINAL ---
    
    # Processo no topo direito
    c.setFont("Helvetica-Bold", 10)
    c.drawString(440, altura - 153, f"{dados['processo']}")
    
    # Bloco de Dados principal
    x_margem = 105
    y_base = altura - 316 
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y_base, "Credor: ")
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + 50, y_base, str(dados['nome']).upper())
    
    y_base -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y_base, "CPF/CNPJ: ")
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + 65, y_base, dados['cpf'])
    
    y_base -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y_base, "Processo N°: ")
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + 75, y_base, dados['processo'])
    
    y_base -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y_base, "Assunto: ")
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + 50, y_base, "INDENIZAÇÃO")
    
    y_base -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y_base, "Cumprimento de sentença contra:")
    
    y_base -= 15
    c.setFont("Helvetica", 11)
    c.drawString(x_margem, y_base, str(dados['contra']).upper())

    # Valor e Extenso
    y_valor = altura - 540
    c.setFont("Helvetica-Bold", 11)
    label_valor = f"Valor a receber: R$ {dados['valor_str']} "
    c.drawString(x_margem, y_valor, label_valor)
    
    largura_label = c.stringWidth(label_valor, "Helvetica-Bold", 11)
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + largura_label, y_valor, f"({dados['extenso']})")

    # Assinatura centralizada
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, altura - 675, str(dados['advogado']).upper())
    c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso()}.")
    
    c.save()
    packet.seek(0)
    return packet

# Tela do Sistema
st.title("⚖️ SISTEMA DE ALVARÁS - TROPA DO ADV")

texto_raw = st.text_area("COLE A MENSAGEM PADRÃO AQUI:", height=250)

if st.button("GERAR ALVARÁ AGORA"):
    if texto_raw:
        try:
            # Captura os dados ignorando se é maiúsculo ou minúsculo
            def buscar(p):
                m = re.search(p, texto_raw, re.I)
                return m.group(1).strip() if m else ""

            v_raw = buscar(r"(?:VALOR|R\$):?\s*([\d\.,]+)")
            v_limpo = v_raw.replace('.', '').replace(',', '.') if v_raw else "0.00"
            
            dados = {
                'nome': buscar(r"NOME:\s*(.*)"),
                'cpf': formatar_cpf_cnpj(buscar(r"CPF:\s*([\d\.-]*)")),
                'processo': buscar(r"(?:Nº|PROC|PROCESSO):?\s*([\d\.\-\/]+)"),
                'contra': buscar(r"(?:CONTRA|CONTRÁRIA):\s*(.*)"),
                'valor_str': v_raw if v_raw else "0,00",
                'extenso': num2words(float(v_limpo), lang='pt_BR', to='currency').title(),
                'advogado': buscar(r"(DR[A]?\.\s*.*)") or "DR. ADVOGADO RESPONSÁVEL"
            }

            pdf = gerar_pdf_final(dados)
            st.success("ALVARÁ GERADO COM SUCESSO!")
            st.download_button("📥 CLIQUE AQUI PARA BAIXAR", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error("Erro ao ler o padrão. Verifique se o valor está correto.")
