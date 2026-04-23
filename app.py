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

def gerar_pdf_tropa_original(dados):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4
    
    # Busca o fundo (template.png)
    try:
        c.drawImage('template.png', 0, 0, width=largura, height=altura)
    except:
        pass

    c.setFillColorRGB(0, 0, 0)
    
    # 1. PROCESSO NO TOPO DIREITO (Lugar 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(440, altura - 153, f"{dados['processo']}")
    
    # 2. BLOCO DE INFORMAÇÕES (Lugar 2 e outros dados)
    x_margem = 105
    y = altura - 316 
    
    def escrever_campo(label, valor, y_pos, negrito_valor=False):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_margem, y_pos, label)
        largura_label = c.stringWidth(label, "Helvetica-Bold", 11)
        
        if negrito_valor:
            c.setFont("Helvetica-Bold", 11)
        else:
            c.setFont("Helvetica", 11)
        c.drawString(x_margem + largura_label, y_pos, str(valor))

    # Credor
    escrever_campo("Credor: ", dados['nome'], y)
    y -= 15
    # CPF/CNPJ
    escrever_campo("CPF/CNPJ: ", dados['cpf'], y)
    y -= 15
    # Processo Nº (Lugar 2)
    escrever_campo("Processo N°: ", dados['processo'], y)
    y -= 15
    # Assunto
    escrever_campo("Assunto: ", "Práticas Abusivas", y)
    y -= 15
    # Cumprimento de sentença contra
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margem, y, "Cumprimento de sentença contra:")
    y -= 15
    c.setFont("Helvetica", 11)
    c.drawString(x_margem, y, str(dados['contra']))

    # 3. VALOR A RECEBER E EXTENSO
    y_valor = altura - 540
    c.setFont("Helvetica-Bold", 11)
    texto_v = f"Valor a receber: R$ {dados['valor_str']} "
    c.drawString(x_margem, y_valor, texto_v)
    
    largura_v = c.stringWidth(texto_v, "Helvetica-Bold", 11)
    c.setFont("Helvetica", 11)
    c.drawString(x_margem + largura_v, y_valor, f"({dados['extenso']})")

    # 4. TEXTOS FIXOS DO TJ (Saindo automático agora)
    y_fixo = y_valor - 25
    c.setFont("Helvetica", 9)
    c.drawString(x_margem, y_fixo, "O valor será depositado em conta corrente vinculada à titularidade indicada no ato da liberação.")
    y_fixo -= 15
    c.drawString(x_margem, y_fixo, "Os autos foram encaminhados pelo TJ para Vara das Execuções, gerando o processo de Execução.")
    
    # 5. ASSINATURA E DATA
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, altura - 675, "Dr. Advogado Responsável")
    c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso()}.")
    
    c.save()
    packet.seek(0)
    return packet

# --- INTERFACE ---
st.title("⚖️ Sistema de Alvarás - TROPA DO ADV")

texto_raw = st.text_area("Cole as informações aqui:", height=250, placeholder="NOME: ...\nCPF: ...\nvalor de R$ ...")

if st.button("GERAR PDF AGORA"):
    if texto_raw:
        try:
            def buscar(p):
                m = re.search(p, texto_raw, re.I)
                return m.group(1).strip() if m else ""

            v_raw = buscar(r"valor de\s*R\$\s*([\d\.,]*)") or buscar(r"VALOR:\s*([\d\.,]*)")
            v_limpo = v_raw.replace('.', '').replace(',', '.') if v_raw else "0.00"
            
            proc = buscar(r"nº\s*([\d\.\-\/]*)") or buscar(r"PROCESSO:\s*([\d\.\-\/]*)")

            dados = {
                'nome': buscar(r"NOME:\s*(.*)"),
                'cpf': formatar_cpf_cnpj(buscar(r"CPF:\s*([\d\.-]*)")),
                'processo': proc if proc else "Processo não informado",
                'contra': buscar(r"contrária:\s*(.*)") or buscar(r"CONTRA:\s*(.*)"),
                'valor_str': v_raw if v_raw else "0,00",
                'extenso': num2words(float(v_limpo), lang='pt_BR', to='currency').title()
            }

            pdf = gerar_pdf_tropa_original(dados)
            st.success("Tudo certo! PDF gerado no padrão original.")
            st.download_button("📥 BAIXAR ALVARÁ", pdf, f"ALVARA_{dados['processo']}.pdf")
        except Exception as e:
            st.error(f"Erro ao ler os dados: {e}")
