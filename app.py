import streamlit as st
import re
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from num2words import num2words

# Configuração da Página
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

def gerar_pdf_tropa_final(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    c.setFillColorRGB(0, 0, 0)
    
    # 1. PROCESSO NO TOPO DIREITO
    c.setFont("Helvetica-Bold", 10)
    c.drawString(440, altura - 153, f"{dados['processo']}")
    
    # 2. BLOCO DE DADOS (altura - 316)
    x_margem = 105
    y = altura - 316 
    
    def escrever_linha(label, valor, y_pos, bold_valor=False):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_margem, y_pos, label)
        w = c.stringWidth(label, "Helvetica-Bold", 11)
        c.setFont("Helvetica-Bold" if bold_valor else "Helvetica", 11)
        c.drawString(x_margem + w, y_pos, str(valor))

    escrever_linha("Credor: ", dados['nome'], y)
    y -= 15
    escrever_linha("CPF/CNPJ: ", dados['cpf'], y)
    y -= 15
    escrever_linha("Processo N°: ", dados['processo'], y)
    y -= 15
    escrever_linha("Assunto: ", dados['assunto'], y)
    y -= 15
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y, "Cumprimento de sentença contra:")
    y -= 15
    c.setFont("Helvetica", 10) # Fonte levemente menor para caber nomes longos
    c.drawString(x_margem, y, str(dados['contra'])[:90])

    # 3. VALOR A RECEBER (altura - 540)
    y_valor = altura - 540
    c.setFont("Helvetica-Bold", 11)
    label_v = f"Valor a receber: R$ {dados['valor_str']} "
    c.drawString(x_margem, y_valor, label_v)
    
    w_v = c.stringWidth(label_v, "Helvetica-Bold", 11)
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + w_v, y_valor, f"({dados['extenso']})")

    # 4. TEXTOS FIXOS
    y_fixo = y_valor - 25
    c.setFont("Helvetica", 9)
    c.drawString(x_margem, y_fixo, "O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.")
    y_fixo -= 15
    c.drawString(x_margem, y_fixo, "Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.")
    
    # 5. ASSINATURA DINÂMICA
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, altura - 675, dados['advogado'])
    c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso()}.")
    
    c.save()
    packet.seek(0)
    return packet

# --- INTERFACE ---
st.title("⚖️ Sistema de Alvarás - TROPA DO ADV")

texto_raw = st.text_area("Cole a mensagem da Live aqui:", height=300)

if st.button("GERAR ALVARÁ PROFISSIONAL"):
    if texto_raw:
        try:
            # Limpa asteriscos para facilitar a busca
            t = texto_raw.replace('*', '')

            # Buscas precisas baseadas nos seus exemplos
            nome = re.search(r"NOME:\s*(.*)", t, re.I)
            cpf = re.search(r"CPF:\s*([\d\.-]*)", t, re.I)
            # Busca processo que vem depois de "processo nº"
            proc = re.search(r"processo\s*nº\s*([\d\.\-\/]*)", t, re.I)
            # Busca assunto
            assunto = re.search(r"Assunto:\s*(.*)", t, re.I)
            # Busca parte contrária
            contra = re.search(r"Parte\s*contrária:\s*(.*)", t, re.I)
            # Busca valor (depois de "valor de R$")
            valor = re.search(r"valor\s*de\s*R\$\s*([\d\.,]*)", t, re.I)
            # Busca o Advogado no final
            adv = re.search(r"Atenciosamente,\s*(Dr\.\s*.*)", t, re.I)

            v_str = valor.group(1).strip() if valor else "0,00"
            num_limpo = v_str.replace('.', '').replace(',', '.')
            extenso = num2words(float(num_limpo), lang='pt_BR', to='currency').title()

            dados = {
                'nome': nome.group(1).strip() if nome else "Não encontrado",
                'cpf': formatar_cpf_cnpj(cpf.group(1)) if cpf else "000.000.000-00",
                'processo': proc.group(1).strip() if proc else "Não informado",
                'assunto': assunto.group(1).strip() if assunto else "Práticas Abusivas",
                'contra': contra.group(1).strip() if contra else "Não informado",
                'valor_str': v_str,
                'extenso': extenso,
                'advogado': adv.group(1).strip() if adv else "Dr. Anderson Souza Brito"
            }

            pdf = gerar_pdf_tropa_final(dados)
            st.success(f"Alvará de {dados['nome']} gerado!")
            st.download_button("📥 BAIXAR PDF", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error(f"Erro ao ler live: {e}")
