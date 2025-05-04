import time

import easyocr
import fitz
import streamlit as st
import torch


@st.cache_resource
def load_ocr_reader():
    """
    Carrega o leitor OCR com os idiomas especificados.
    :return: Instância do leitor OCR.
    """
    print(f"Carregando modelo EasyOCR...")
    try:
        reader = easyocr.Reader(['pt'], gpu=torch.cuda.is_available())
        print("Modelo EasyOCR carregado.")
        return reader
    except Exception as e:
        print(f"Erro ao carregar modelo EasyOCR: {e}")
        st.error(f"Não foi possível carregar o modelo de OCR: {e}")
        return None


def verify_name_from_cnh_pdf(pdf_bytes: bytes, first_name: str, last_name: str) -> tuple[str, str | None]:
    """
    Tenta extrair texto de um PDF (renderizando como imagem) e verifica
    se o primeiro e último nome fornecidos estão presentes.
    """
    start_time = time.time()
    reader = load_ocr_reader()

    if reader is None:
        return "Erro: Modelo OCR não carregado", None

    if not pdf_bytes or not first_name or not last_name:
        return "Erro: Dados de entrada inválidos", None

    extracted_text_all_pages = ""
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        num_pages = len(pdf_document)
        print(f"Processando PDF com {num_pages} página(s).")

        page_num_to_process = min(1, num_pages)

        for page_number in range(page_num_to_process):
            page = pdf_document.load_page(page_number)

            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")

            print(f"  Executando OCR na página {page_number + 1}...")
            ocr_results = reader.readtext(img_bytes, detail=0, paragraph=True)

            page_text = " ".join(ocr_results).lower()
            extracted_text_all_pages += page_text + " "
            print(f"  Texto extraído da página {page_number + 1} (primeiros 100 chars): {page_text[:100]}...")

        pdf_document.close()

    except Exception as e:
        print(f"Erro ao processar o PDF ou renderizar imagem: {e}")
        return "Erro ao Processar PDF", None

    print("Verificando nomes no texto extraído...")
    if not extracted_text_all_pages.strip():
        print("  Falha: Nenhum texto foi extraído pelo OCR.")
        return "Falha na Verificação (OCR não extraiu texto)", ""

    first_name_lower = first_name.lower()
    last_name_lower = last_name.lower()

    if first_name_lower in extracted_text_all_pages and last_name_lower in extracted_text_all_pages:
        status = "Verificado com Sucesso"
        print(f"  Sucesso: Nomes '{first_name}' e '{last_name}' encontrados.")
    else:
        status = "Falha na Verificação (Nome não encontrado)"
        print(f"  Falha: Nomes '{first_name}' ou '{last_name}' não encontrados no texto.")
        print(f"  Texto completo extraído (lower): {extracted_text_all_pages}")

    end_time = time.time()
    print(f"Verificação concluída em {end_time - start_time:.2f} segundos.")

    return status, extracted_text_all_pages.strip()
