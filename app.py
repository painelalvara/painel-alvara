import streamlit as st
import re
import io
import textwrap
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from num2words import num2words
from PIL import Image

# Configuração da Página
st.set_page_config(page_title="TROPA DO ADV - Original", layout="centered")

def obter_data_extenso():
    meses = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho", 
             7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
    hoje = datetime.now()
    return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

def formatar_cpf_cnpj(valor):
    numeros = re.sub(r'\D', '', valor)
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    elif len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return valor

def gerar_pdf_tropa(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    # Carrega o template.png da raiz do GitHub
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    c.setFillColorRGB(0, 0, 0)
    
    # --- CABEÇALHO (SUA COORDENADA ORIGINAL) ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(440, altura - 153, f"{dados['processo']}")
    
    # --- BLOCO DE DADOS (SUA COORDENADA ORIGINAL) ---
    x_margem = 105
    y_base = altura - 316 
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y_base, "Credor: ")
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + 50, y_base, dados['nome'].title())
    
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
    c.drawString(x_margem + 50, y_base, dados['assunto'].title())
    
    y_base -= 15
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y_base, "Cumprimento de sentença contra:")
    
    y_base -= 15
    c.setFont("Helvetica", 11)
    c.drawString(x_margem, y_base, dados['contra'].title()[:75])

    # --- VALOR A RECEBER ---
    y_valor = altura - 540
    c.setFont("Helvetica-Bold", 11)
    label_valor = f"Valor a receber: R$ {dados['valor_str']} "
    c.drawString(x_margem, y_valor, label_valor)
    
    largura_label = c.stringWidth(label_valor, "Helvetica-Bold", 11)
    c.setFont("Helvetica", 11)
    extenso_parenteses = f"({dados['extenso']})"
    
    largura_disponivel = 480 - largura_label
    
    if c.stringWidth(extenso_parenteses, "Helvetica", 11) > largura_disponivel:
        linhas = textwrap.wrap(extenso_parenteses, width=65) 
        for i, linha in enumerate(linhas):
            if i == 0:
                c.drawString(x_margem + largura_label, y_valor, linha)
            else:
                y_valor -= 14
                c.drawString(x_margem, y_valor, linha)
        y_valor -= 14
    else:
        c.drawString(x_margem + largura_label, y_valor, extenso_parenteses)
        y_valor -= 14

    # --- TEXTOS FINAIS ---
    y_texto = y_valor - 10
    c.setFont("Helvetica", 9)
    c.drawString(x_margem, y_texto, "O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.")
    y_texto -= 15
    c.drawString(x_margem, y_texto, "Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.")
    
    # --- ASSINATURA E DATA ---
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, altura - 675, dados['advogado'].title())
    c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso()}.")
    
    c.save()
    packet.seek(0)
    return packet

# Interface do Streamlit
st.title("⚖️ TROPA DO ADV - Original")

texto_raw = st.text_area("Cole os dados da live aqui:", height=300)

if st.button("GERAR ALVARÁ"):
    if texto_raw:
        try:
            def extrair(pattern, default="Não Encontrado"):
                match = re.search(pattern, texto_raw, re.I)
                return match.group(1).strip() if match else default

            nome = extrair(r"NOME:\s*(.*)")
            cpf_raw = extrair(r"CPF:\s*([\d.-]*)")
            proc = extrair(r"nº\s*([\d.-]*)")
            contra = extrair(r"contrária:\s*(.*)")
            assunto = extrair(r"Assunto:\s*(.*)", "Indenização")
            valor_raw = extrair(r"valor de\s*R\$\s*([\d.,]*)", "0,00")
            
            adv_match = re.search(r"(Dr[a]?\.\s*.*)", texto_raw, re.I)
            advogado = adv_match.group(1).strip() if adv_match else "Dr. Advogado Responsável"

            num_limpo = valor_raw.replace('.', '').replace(',', '.')
            extenso = num2words(float(num_limpo), lang='pt_BR', to='currency').title()

            dados = {
                'nome': nome, 'cpf': formatar_cpf_cnpj(cpf_raw), 'processo': proc, 
                'contra': contra, 'assunto': assunto, 'valor_str': valor_raw, 
                'extenso': extenso, 'advogado': advogado
            }

            pdf_output = gerar_pdf_tropa(dados)
            st.success("PDF gerado com as coordenadas originais!")
            st.download_button(
                label="📥 BAIXAR ALVARÁ PDF",
                data=pdf_output,
                file_name=f"ALVARA_{proc}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")
