import streamlit as st
import re
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from num2words import num2words

st.set_page_config(page_title="TROPA DO ADV - SISTEMA", layout="centered")

def formatar_extenso_tropa(valor_float):
    ext = num2words(valor_float, lang='pt_BR', to='currency').title()
    return ext.replace(" E ", " e ")

def gerar_pdf_tropa_dinamico(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    # Estilos para permitir quebra de linha
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', fontName='Helvetica', fontSize=11, leading=14)
    style_bold = ParagraphStyle('Bold', fontName='Helvetica-Bold', fontSize=11, leading=14)
    style_pequeno = ParagraphStyle('Pequeno', fontName='Helvetica', fontSize=8.5, leading=11)

    c.setFillColorRGB(0, 0, 0)
    
    # 1. PROCESSO TOPO DIREITO
    c.setFont("Helvetica-Bold", 10)
    c.drawString(435, altura - 153, f"{dados['processo']}")
    
    # 2. BLOCO DE DADOS
    x = 105
    curr_y = altura - 316

    # Campos simples
    campos = [
        ("Credor: ", dados['nome']),
        ("CPF/CNPJ: ", dados['cpf']),
        ("Processo N°: ", dados['processo']),
        ("Assunto: ", dados['assunto'])
    ]

    for label, valor in campos:
        p = Paragraph(f"<b>{label}</b> {valor}", style_normal)
        w, h = p.wrap(largura - 200, 20)
        p.drawOn(c, x, curr_y - h)
        curr_y -= 20

    # Cumprimento de Sentença (AQUI ELE PULA LINHA SE FOR GRANDE)
    p_contra_label = Paragraph("<b>Cumprimento de sentença contra:</b>", style_normal)
    w, h = p_contra_label.wrap(largura - 200, 20)
    p_contra_label.drawOn(c, x, curr_y - h)
    curr_y -= 15

    p_contra_val = Paragraph(dados['contra'], style_normal)
    w, h = p_contra_val.wrap(largura - 180, 100) # Largura máxima antes de pular
    p_contra_val.drawOn(c, x, curr_y - h)
    
    # Empurra o resto para baixo baseado no tamanho do nome da empresa
    curr_y -= (h + 30)

    # 3. VALOR A RECEBER (TAMBÉM PULA LINHA SE O EXTENSO FOR LONGO)
    p_valor = Paragraph(f"<b>Valor a receber: R$ {dados['valor_str']}</b> ({dados['extenso']})", style_normal)
    w, h = p_valor.wrap(largura - 180, 100)
    # A posição do valor no template é fixa em torno de altura - 540, 
    # mas vamos usar o curr_y para manter a proporção se a empresa for gigante
    y_final_valor = min(curr_y, altura - 540) 
    p_valor.drawOn(c, x, y_final_valor)

    # 4. TEXTOS FIXOS (Sempre abaixo do valor)
    y_fixo = y_final_valor - h - 10
    p_fixo1 = Paragraph("O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.", style_pequeno)
    w, h1 = p_fixo1.wrap(largura - 180, 50)
    p_fixo1.drawOn(c, x, y_fixo)
    
    y_fixo -= 12
    p_fixo2 = Paragraph("Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.", style_pequeno)
    p_fixo2.wrap(largura - 180, 50)
    p_fixo2.drawOn(c, x, y_fixo)
    
    # 5. ASSINATURA (Sempre no mesmo lugar no fim)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, 160, dados['advogado'])
    c.setFont("Helvetica", 11)
    hoje = datetime.now()
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_ext = f"{hoje.day} de {meses[hoje.month-1]} de {hoje.year}."
    c.drawCentredString(largura/2, 140, data_ext)
    
    c.save()
    packet.seek(0)
    return packet

# Interface Streamlit
st.title("⚖️ SISTEMA TROPA DO ADV")
texto_raw = st.text_area("Cole a Live:", height=200)

if st.button("GERAR ALVARÁ"):
    if texto_raw:
        try:
            t = texto_raw.replace('*', '')
            nome = re.search(r"NOME:\s*(.*)", t, re.I)
            cpf = re.search(r"CPF:\s*([\d\.-]*)", t, re.I)
            proc = re.search(r"processo\s*nº\s*([\d\.\-\/]*)", t, re.I)
            assunto = re.search(r"Assunto:\s*(.*)", t, re.I)
            contra = re.search(r"Parte\s*contrária:\s*(.*)", t, re.I)
            valor = re.search(r"valor\s*de\s*R\$\s*([\d\.,]*)", t, re.I)
            adv = re.search(r"Atenciosamente,\s*(Dr\.\s*.*)", t, re.I)

            v_str = valor.group(1).strip() if valor else "0,00"
            num_limpo = v_str.replace('.', '').replace(',', '.')
            ext_final = formatar_extenso_tropa(float(num_limpo))

            dados = {
                'nome': nome.group(1).strip() if nome else "",
                'cpf': cpf.group(1).strip() if cpf else "",
                'processo': proc.group(1).strip() if proc else "",
                'assunto': assunto.group(1).strip() if assunto else "",
                'contra': contra.group(1).strip() if contra else "",
                'valor_str': v_str,
                'extenso': ext_final,
                'advogado': adv.group(1).strip().upper() if adv else "DR. ADVOGADO RESPONSÁVEL"
            }

            pdf = gerar_pdf_tropa_dinamico(dados)
            st.success("Perfeito! Com quebra de linha igual ao original.")
            st.download_button("📥 BAIXAR ALVARÁ", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error(f"Erro: {e}")
