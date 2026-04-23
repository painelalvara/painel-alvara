import streamlit as st
import re
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from num2words import num2words

st.set_page_config(page_title="SISTEMA TROPA DO ADV", layout="centered")

def formatar_extenso_tropa(valor_float):
    # Mantém o padrão de capitalização que você aprovou
    ext = num2words(valor_float, lang='pt_BR', to='currency').title()
    return ext.replace(" E ", " e ")

def gerar_pdf_tropa_estatico(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    styles = getSampleStyleSheet()
    style_topo = ParagraphStyle('Topo', fontName='Helvetica', fontSize=11, leading=12)
    style_corpo = ParagraphStyle('Corpo', fontName='Helvetica', fontSize=11, leading=14)
    style_pequeno = ParagraphStyle('Pequeno', fontName='Helvetica', fontSize=8.5, leading=10)

    c.setFillColorRGB(0, 0, 0)
    
    # 1. PROCESSO NO CABEÇALHO
    c.setFont("Helvetica-Bold", 10)
    c.drawString(435, altura - 153, f"{dados['processo']}")
    
    # 2. BLOCO DE DADOS (TRAVADO / JUNTINHO)
    x = 105
    curr_y = altura - 316

    # Dados do Credor até Assunto
    campos = [
        ("Credor: ", dados['nome']),
        ("CPF/CNPJ: ", dados['cpf']),
        ("Processo N°: ", dados['processo']),
        ("Assunto: ", dados['assunto'])
    ]

    for label, valor in campos:
        p = Paragraph(f"<b>{label}</b> {valor}", style_topo)
        p.wrap(largura - 180, 20)
        p.drawOn(c, x, curr_y - 11)
        curr_y -= 14

    # Cumprimento de Sentença (COM CORTE 'ETC' SE FOR GRANDE)
    curr_y -= 5
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, curr_y - 11, "Cumprimento de sentença contra:")
    curr_y -= 14

    contra_texto = dados['contra']
    if len(contra_texto) > 85:
        contra_texto = contra_texto[:82] + " etc." # Usa o 'etc.' conforme solicitado
    
    c.setFont("Helvetica", 11)
    c.drawString(x, curr_y - 11, contra_texto)

    # 3. VALOR A RECEBER (ESTE PULA LINHA SE PRECISAR)
    y_valor_fixo = altura - 540
    p_valor = Paragraph(f"<b>Valor a receber: R$ {dados['valor_str']}</b> ({dados['extenso']})", style_corpo)
    w_val, h_val = p_valor.wrap(largura - 180, 100)
    p_valor.drawOn(c, x, y_valor_fixo - h_val)

    # 4. TEXTOS FIXOS (ABAIXO DO VALOR)
    curr_y_fixo = y_valor_fixo - h_val - 10
    pf1 = Paragraph("O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.", style_pequeno)
    wf1, hf1 = pf1.wrap(largura - 180, 50)
    pf1.drawOn(c, x, curr_y_fixo - hf1)
    
    curr_y_fixo -= 12
    pf2 = Paragraph("Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.", style_pequeno)
    wf2, hf2 = pf2.wrap(largura - 180, 50)
    pf2.drawOn(c, x, curr_y_fixo - hf2)

    # 5. ASSINATURA
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
texto_raw = st.text_area("Cole os dados aqui:", height=200)

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
            
            dados = {
                'nome': nome.group(1).strip() if nome else "",
                'cpf': cpf.group(1).strip() if cpf else "",
                'processo': proc.group(1).strip() if proc else "",
                'assunto': assunto.group(1).strip() if assunto else "Indenização",
                'contra': contra.group(1).strip() if contra else "",
                'valor_str': v_str,
                'extenso': formatar_extenso_tropa(float(num_limpo)),
                'advogado': adv.group(1).strip().upper() if adv else "DR. ADVOGADO RESPONSÁVEL"
            }

            pdf = gerar_pdf_tropa_estatico(dados)
            st.success("Tudo certo! Topo travado e valor ajustável.")
            st.download_button("📥 BAIXAR ALVARÁ", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error(f"Erro: {e}")
