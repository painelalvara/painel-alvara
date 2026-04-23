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
    ext = num2words(valor_float, lang='pt_BR', to='currency').title()
    return ext.replace(" E ", " e ")

def formatar_documento(doc):
    # Remove qualquer coisa que não seja número
    apenas_numeros = re.sub(r'\D', '', doc)
    
    # Se for CPF (11 dígitos)
    if len(apenas_numeros) == 11:
        return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"
    
    # Se for CNPJ (14 dígitos)
    elif len(apenas_numeros) == 14:
        return f"{apenas_numeros[:2]}.{apenas_numeros[2:5]}.{apenas_numeros[5:8]}/{apenas_numeros[8:12]}-{apenas_numeros[12:]}"
    
    # Se não for nenhum dos dois, retorna o que veio original
    return doc

def gerar_pdf_tropa_final(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    styles = getSampleStyleSheet()
    style_corpo = ParagraphStyle('Corpo', fontName='Helvetica', fontSize=11, leading=14)
    style_pequeno = ParagraphStyle('Pequeno', fontName='Helvetica', fontSize=8.5, leading=10)

    c.setFillColorRGB(0, 0, 0)
    
    # 1. PROCESSO NO CABEÇALHO
    c.setFont("Helvetica-Bold", 10)
    c.drawString(435, altura - 153, f"{dados['processo']}")
    
    # 2. BLOCO DE DADOS
    x = 105
    y_base = altura - 316

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y_base, "Credor: ")
    c.setFont("Helvetica", 11)
    c.drawString(x + 48, y_base, dados['nome'])
    
    y_base -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y_base, "CPF/CNPJ: ")
    c.setFont("Helvetica", 11)
    c.drawString(x + 62, y_base, dados['cpf']) # Aqui já sai formatado
    
    y_base -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y_base, "Processo N°: ")
    c.setFont("Helvetica", 11)
    c.drawString(x + 72, y_base, dados['processo'])
    
    y_base -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y_base, "Assunto: ")
    c.setFont("Helvetica", 11)
    c.drawString(x + 50, y_base, dados['assunto'])

    y_base -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y_base, "Cumprimento de sentença contra:")
    
    y_base -= 14
    contra_texto = dados['contra']
    if len(contra_texto) > 85:
        contra_texto = contra_texto[:82] + "..."
    
    c.setFont("Helvetica", 11)
    c.drawString(x, y_base, contra_texto)

    # 3. VALOR A RECEBER
    y_valor_fixo = altura - 540
    p_valor = Paragraph(f"<b>Valor a receber: R$ {dados['valor_str']}</b> ({dados['extenso']})", style_corpo)
    w_val, h_val = p_valor.wrap(largura - 180, 100)
    p_valor.drawOn(c, x, y_valor_fixo - h_val)

    # 4. TEXTOS FIXOS
    curr_y_fixo = y_valor_fixo - h_val - 10
    pf1 = Paragraph("O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.", style_pequeno)
    wf1, hf1 = pf1.wrap(largura - 180, 50)
    pf1.drawOn(c, x, curr_y_fixo - hf1)
    
    curr_y_fixo -= 12
    pf2 = Paragraph("Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.", style_pequeno)
    wf2, hf2 = pf2.wrap(largura - 180, 50)
    pf2.drawOn(c, x, curr_y_fixo - hf2)

    # 5. ASSINATURA E DATA
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
texto_raw = st.text_area("Cole a Live aqui:", height=200)

if st.button("GERAR ALVARÁ"):
    if texto_raw:
        try:
            t = texto_raw.replace('*', '')
            nome = re.search(r"NOME:\s*(.*)", t, re.I)
            cpf_raw = re.search(r"CPF:\s*([\d\.-]*)", t, re.I)
            proc = re.search(r"processo\s*nº\s*([\d\.\-\/]*)", t, re.I)
            assunto = re.search(r"Assunto:\s*(.*)", t, re.I)
            contra = re.search(r"Parte\s*contrária:\s*(.*)", t, re.I)
            valor = re.search(r"valor\s*de\s*R\$\s*([\d\.,]*)", t, re.I)
            adv = re.search(r"Atenciosamente,\s*((?:Dr|Dra)\.?\s*.*)", t, re.I)

            v_str = valor.group(1).strip() if valor else "0,00"
            num_limpo = v_str.replace('.', '').replace(',', '.')
            
            # Formata o CPF/CNPJ antes de salvar nos dados
            doc_final = formatar_documento(cpf_raw.group(1).strip()) if cpf_raw else ""

            dados = {
                'nome': nome.group(1).strip() if nome else "",
                'cpf': doc_final,
                'processo': proc.group(1).strip() if proc else "",
                'assunto': assunto.group(1).strip() if assunto else "Práticas Abusivas",
                'contra': contra.group(1).strip() if contra else "",
                'valor_str': v_str,
                'extenso': formatar_extenso_tropa(float(num_limpo)),
                'advogado': adv.group(1).strip().upper() if adv else "DR. ADVOGADO RESPONSÁVEL"
            }

            pdf = gerar_pdf_tropa_final(dados)
            st.success("Tudo pronto! CPF formatado e Dra. reconhecida.")
            st.download_button("📥 BAIXAR AGORA", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error(f"Erro: {e}")
