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
    return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

def formatar_cpf_cnpj(valor):
    numeros = re.sub(r'\D', '', valor)
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    return valor

def gerar_pdf_tropa_fiel(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    c.setFillColorRGB(0, 0, 0)
    
    # --- PROCESSO TOPO DIREITO ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(440, altura - 153, f"{dados['processo']}")
    
    # --- BLOCO PRINCIPAL (altura - 316) ---
    x_margem = 105
    y = altura - 316 
    
    # Função auxiliar para escrever Negrito + Normal na mesma linha
    def escrever_linha(label, valor, y_pos):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_margem, y_pos, label)
        largura_label = c.stringWidth(label, "Helvetica-Bold", 11)
        c.setFont("Helvetica", 11)
        c.drawString(x_margem + largura_label, y_pos, str(valor).upper())

    escrever_linha("Credor: ", dados['nome'], y)
    y -= 15
    escrever_linha("CPF/CNPJ: ", dados['cpf'], y)
    y -= 15
    escrever_linha("Processo N°: ", dados['processo'], y)
    y -= 15
    escrever_linha("Assunto: ", "PRÁTICAS ABUSIVAS", y)
    y -= 15
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y, "Cumprimento de sentença contra:")
    y -= 15
    c.setFont("Helvetica", 11)
    c.drawString(x_margem, y, str(dados['contra']).upper())

    # --- VALOR A RECEBER (altura - 540) ---
    y_valor = altura - 540
    c.setFont("Helvetica-Bold", 11)
    texto_valor = f"Valor a receber: R$ {dados['valor_str']} "
    c.drawString(x_margem, y_valor, texto_valor)
    
    largura_v = c.stringWidth(texto_valor, "Helvetica-Bold", 11)
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + largura_v, y_valor, f"({dados['extenso']})")

    # --- FRASES FIXAS (AQUI ESTÁ O QUE VOCÊ FALOU) ---
    y_fixo = y_valor - 25
    c.setFont("Helvetica", 9)
    c.drawString(x_margem, y_fixo, "O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.")
    y_fixo -= 15
    c.drawString(x_margem, y_fixo, "Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.")
    
    # --- ASSINATURA ---
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, altura - 675, "DR. ADVOGADO RESPONSÁVEL")
    c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso()}.")
    
    c.save()
    packet.seek(0)
    return packet

# Interface Streamlit
st.title("⚖️ TROPA DO ADV - ORIGINAL")

texto_raw = st.text_area("Cole as informações aqui:", height=250)

if st.button("GERAR ALVARÁ"):
    if texto_raw:
        try:
            def buscar(p, default=""):
                m = re.search(p, texto_raw, re.I)
                return m.group(1).strip() if m else default

            v_raw = buscar(r"valor de\s*R\$\s*([\d\.,]*)") or buscar(r"VALOR:\s*([\d\.,]*)")
            v_limpo = v_raw.replace('.', '').replace(',', '.') if v_raw else "0.00"
            
            dados = {
                'nome': buscar(r"NOME:\s*(.*)"),
                'cpf': formatar_cpf_cnpj(buscar(r"CPF:\s*([\d\.-]*)")),
                'processo': buscar(r"nº\s*([\d\.\-\/]*)") or buscar(r"PROCESSO:\s*([\d\.\-\/]*)"),
                'contra': buscar(r"contrária:\s*(.*)") or buscar(r"CONTRA:\s*(.*)"),
                'valor_str': v_raw if v_raw else "0,00",
                'extenso': num2words(float(v_limpo), lang='pt_BR', to='currency').title()
            }

            pdf = gerar_pdf_tropa_fiel(dados)
            st.success("Gerado! Agora sim no padrão.")
            st.download_button("📥 BAIXAR ALVARÁ", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error(f"Erro: {e}")
