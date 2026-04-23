import streamlit as st
import re
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from num2words import num2words

# Configuração da Página
st.set_page_config(page_title="TROPA DO ADV", layout="centered")

def obter_data_extenso():
    meses = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho", 
             7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
    hoje = datetime.now()
    return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}."

def formatar_cpf_cnpj(valor):
    numeros = re.sub(r'\D', '', valor)
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    return valor

def formatar_extenso_simples(valor_float):
    # Gera o extenso padrão
    ext = num2words(valor_float, lang='pt_BR', to='currency')
    # Deixa apenas a primeira letra da frase em maiúsculo
    return ext.capitalize()

def gerar_pdf_tropa_corrigido(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    c.setFillColorRGB(0, 0, 0)
    
    # 1. PROCESSO TOPO DIREITO
    c.setFont("Helvetica-Bold", 10)
    c.drawString(435, altura - 153, f"{dados['processo']}")
    
    # 2. BLOCO DE DADOS
    x_margem = 105
    y = altura - 316 
    
    def escrever_campo(label, valor, y_pos, offset):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_margem, y_pos, label)
        c.setFont("Helvetica", 11)
        c.drawString(x_margem + offset, y_pos, str(valor))

    escrever_campo("Credor: ", dados['nome'], y, 48)
    y -= 15
    escrever_campo("CPF/CNPJ: ", dados['cpf'], y, 62)
    y -= 15
    escrever_campo("Processo N°: ", dados['processo'], y, 72)
    y -= 15
    escrever_campo("Assunto: ", dados['assunto'], y, 50)
    y -= 15
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y, "Cumprimento de sentença contra:")
    y -= 15
    c.setFont("Helvetica", 10)
    # Limita o texto da contraparte para não estourar a margem
    contra_texto = str(dados['contra'])
    if len(contra_texto) > 85:
        contra_texto = contra_texto[:82] + "..."
    c.drawString(x_margem, y, contra_texto)

    # 3. VALOR A RECEBER
    y_valor = altura - 540
    c.setFont("Helvetica-Bold", 11)
    texto_v = f"Valor a receber: R$ {dados['valor_str']} "
    c.drawString(x_margem, y_valor, texto_v)
    
    w_v = c.stringWidth(texto_v, "Helvetica-Bold", 11)
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + w_v, y_valor, f"({dados['extenso']})")

    # 4. TEXTOS FIXOS
    y_fixo = y_valor - 25
    c.setFont("Helvetica", 8.5)
    c.drawString(x_margem, y_fixo, "O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.")
    y_fixo -= 12
    c.drawString(x_margem, y_fixo, "Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.")
    
    # 5. ASSINATURA
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, altura - 675, dados['advogado'])
    c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso()}")
    
    c.save()
    packet.seek(0)
    return packet

# Interface
st.title("⚖️ SISTEMA TROPA DO ADV")
texto_raw = st.text_area("Cole a Live aqui:", height=250)

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
            
            extenso_final = formatar_extenso_simples(float(num_limpo))

            dados = {
                'nome': nome.group(1).strip() if nome else "",
                'cpf': formatar_cpf_cnpj(cpf.group(1)) if cpf else "",
                'processo': proc.group(1).strip() if proc else "",
                'assunto': assunto.group(1).strip() if assunto else "Práticas Abusivas",
                'contra': contra.group(1).strip() if contra else "",
                'valor_str': v_str,
                'extenso': extenso_final,
                'advogado': adv.group(1).strip().upper() if adv else "DR. ADVOGADO RESPONSÁVEL"
            }

            pdf = gerar_pdf_tropa_corrigido(dados)
            st.success("Alvará gerado com sucesso!")
            st.download_button("📥 BAIXAR ALVARÁ", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error(f"Erro: {e}")
