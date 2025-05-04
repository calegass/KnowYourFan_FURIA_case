import os

import streamlit as st
import torch
from dotenv import load_dotenv

from utils.ocr import verify_name_from_cnh_pdf
from utils.storage import initialize_firebase, save_user_profile_rtdb
from utils.vectorizer import load_model, prepare_user_text, get_vector, load_player_vectors, find_best_match

torch.classes.__path__ = []

st.set_page_config(layout="centered")

load_dotenv()

SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")

firebase_initialized = False
if SERVICE_ACCOUNT_PATH and DATABASE_URL:
    firebase_initialized = initialize_firebase(SERVICE_ACCOUNT_PATH, DATABASE_URL)
else:
    st.error("Erro, variáveis de ambiente não configuradas.")

if 'form_stage' not in st.session_state:
    st.session_state.form_stage = 1
    st.session_state.first_name = ""
    st.session_state.last_name = ""
    st.session_state.city = ""
    st.session_state.fav_game = "Selecione"
    st.session_state.nickname = ""
    st.session_state.role = ""
    st.session_state.playstyle_desc = ""
    st.session_state.watched_champs = None
    st.session_state.instagram_handle = ""
    st.session_state.cnh_uploaded = False
    st.session_state.stage1_complete = False
    st.session_state.stage2_complete = False
    st.session_state.stage3_complete = False
    st.session_state.cnh_pdf_bytes = None
    st.session_state.match_result = None
    st.session_state.verification_status = "Pendente"
    st.session_state.profile_saved = False


# --- Funções de Callback ---
def next_stage(current_stage):
    """Avança para a próxima etapa do formulário."""
    st.session_state[f'stage{current_stage}_complete'] = True

    if current_stage == 3:
        if st.session_state.get('cnh_pdf_bytes') is not None:
            st.session_state.cnh_uploaded = True
            st.session_state.verification_status = "Verificação Solicitada"
            print("Callback Etapa 3: PDF bytes encontrados, status definido para 'Verificação Solicitada'.")
        else:
            st.session_state.cnh_uploaded = False
            st.session_state.verification_status = "Pulado"
            print("Callback Etapa 3: PDF bytes NÃO encontrados, status definido para 'Pulado'.")
        st.session_state.cnh_upload = None

    st.session_state.form_stage += 1


def get_radio_index(key, options):
    """Retorna o índice da opção selecionada ou None."""
    value = st.session_state.get(key)
    if value in options:
        return options.index(value)
    return None


# --- Título Principal ---
st.title("🧠 Know Your Fan - FURIA")
st.write("Nos ajude a te conhecer melhor! Preencha as informações abaixo.")
st.divider()

# --- Etapa 1: Dados Básicos ---
with st.container(border=True):
    st.subheader("1. Seus Dados Básicos")
    is_stage1_active = (st.session_state.form_stage == 1)
    is_stage1_complete = st.session_state.get('stage1_complete', False)
    disabled_stage1 = is_stage1_complete or not is_stage1_active

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Nome", key="first_name", disabled=disabled_stage1, value=st.session_state.first_name)
    with col2:
        st.text_input("Sobrenome", key="last_name", disabled=disabled_stage1, value=st.session_state.last_name)

    st.text_input("Cidade", key="city", disabled=disabled_stage1, value=st.session_state.city)

    game_options = ["Selecione", "Counter-Strike", "League of Legends"]
    game_index = game_options.index(st.session_state.get('fav_game', "Selecione"))
    st.selectbox("Jogo Preferido", game_options, key="fav_game", disabled=disabled_stage1, index=game_index)

    role_options = ["Selecione uma role"]
    game_selected = st.session_state.fav_game
    if game_selected == "Counter-Strike":
        role_options.extend(["Entry Fragger", "Suporte", "AWPer", "IGL", "Lurker"])
    elif game_selected == "League of Legends":
        role_options.extend(["Top", "Jungle", "Mid", "ADC", "Support"])
    role_index = get_radio_index('role', role_options)
    st.selectbox("Role Principal", role_options, key="role",
                 disabled=disabled_stage1 or game_selected == "Selecione", index=role_index or 0)

    st.text_input("Nickname Principal", key="nickname", disabled=disabled_stage1, value=st.session_state.nickname)

    if is_stage1_active:
        proceed_stage1 = (
                st.session_state.first_name and
                st.session_state.last_name and
                st.session_state.city and
                st.session_state.fav_game != "Selecione" and
                st.session_state.role and st.session_state.role != "Selecione uma role" and
                st.session_state.nickname
        )
        st.button("Próximo: Interesses", on_click=next_stage, args=(1,), type="primary", disabled=not proceed_stage1)
        if not proceed_stage1:
            st.caption("Preencha todos os campos acima para continuar.")

# --- Etapa 2: Interesses ---
if st.session_state.form_stage >= 2:
    st.divider()
    with st.container(border=True):
        st.subheader("2. Interesses")
        is_stage2_active = (st.session_state.form_stage == 2)
        is_stage2_complete = st.session_state.get('stage2_complete', False)
        disabled_stage2 = is_stage2_complete or not is_stage2_active

        st.text_area("Descreva seu estilo de jogo: (por favor, não cole texto aqui) (*)", key="playstyle_desc",
                     disabled=disabled_stage2, value=st.session_state.playstyle_desc)

        col1, col2 = st.columns(2)
        with col1:
            watched_options = ["Sim", "Não"]
            watched_index = get_radio_index('watched_champs', watched_options)
            st.radio(
                "Assistiu algum campeonato de e-sports esse ano?", watched_options, key="watched_champs",
                disabled=disabled_stage2, index=watched_index,
                horizontal=True
            )

        with col2:
            st.text_input("Seu @ no Instagram", key="instagram_handle",
                          disabled=disabled_stage2,
                          value=st.session_state.instagram_handle)

        if is_stage2_active:
            proceed_stage2 = (
                st.session_state.playstyle_desc
            )
            st.button("Próximo: Verificação", on_click=next_stage, args=(2,), type="primary",
                      disabled=not proceed_stage2)
            if not proceed_stage2:
                st.caption("Preencha todos os campos acima para continuar.")

# --- Etapa 3: Verificação ---
if st.session_state.form_stage >= 3:
    st.divider()
    with st.container(border=True):
        st.subheader("3. Verificação de Identidade (Opcional)")
        is_stage3_active = (st.session_state.form_stage == 3)

        st.warning("""
        **Importante sobre Privacidade:** Para validar seu nome, faça upload do **PDF**
        da sua CNH Digital. **O arquivo PDF NÃO será salvo permanentemente.**
        Ele será processado em memória apenas para esta verificação e depois descartado.
        Este passo é opcional.
        """)

        pdf_uploaded_successfully = False

        if is_stage3_active:
            uploaded_file_widget = st.file_uploader(
                "Faça upload do PDF da CNH Digital",
                type=["pdf"],
                key="cnh_upload",
                help="Arraste e solte ou clique para procurar o PDF.",
                disabled=False
            )

            if uploaded_file_widget is not None:
                try:
                    st.session_state.cnh_pdf_bytes = uploaded_file_widget.getvalue()
                    pdf_uploaded_successfully = True
                    print(
                        f"Etapa 3 (Rerun pós-upload): PDF '{uploaded_file_widget.name}' lido, {len(st.session_state.cnh_pdf_bytes)} bytes salvos em session_state.")
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo PDF: {e}")
                    st.session_state.cnh_pdf_bytes = None
                    pdf_uploaded_successfully = False
            elif 'cnh_upload' in st.session_state and st.session_state.cnh_upload is None:
                st.session_state.cnh_pdf_bytes = None
                pdf_uploaded_successfully = False

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                button_label = "Verificar e Ver Resultado" if pdf_uploaded_successfully else "Pular e Ver Resultado"
                st.button(
                    button_label,
                    on_click=next_stage,
                    args=(3,),
                    type="primary",
                )
            with col_btn2:
                if pdf_uploaded_successfully:
                    st.success(f"PDF '{uploaded_file_widget.name}' pronto para verificação.")
                elif uploaded_file_widget is not None and not pdf_uploaded_successfully:
                    st.warning("Houve um problema ao ler o PDF. Tente recarregá-lo ou pule.")
                else:
                    if st.session_state.get('cnh_pdf_bytes') is None:
                        st.info("Sem upload, a verificação será pulada.")

        else:
            final_status = st.session_state.verification_status
            if final_status == "Verificado com Sucesso":
                st.success("Status da Verificação: Verificado com Sucesso")
            elif final_status == "Pulado":
                st.info("Status da Verificação: Verificação pulada.")
            elif final_status == "Falha na Verificação (Nome não encontrado)":
                st.warning("Status da Verificação: Nome não encontrado no documento")
            elif final_status.startswith("Erro"):
                st.error(f"Status da Verificação: {final_status}")
            else:
                st.info(f"Status da Verificação: {final_status}")

st_model = load_model()

# --- Etapa 4: Resultado ---
if st.session_state.form_stage >= 4:
    st.divider()
    with st.container(border=True):
        st.subheader(f"🎉 Análise Concluída, {st.session_state.first_name}!")

        if st.session_state.verification_status == "Verificação Solicitada":
            with st.spinner("🔍 Processando verificação da CNH... (Isso pode levar alguns segundos)"):
                print("Etapa 4: Iniciando verificação da CNH...")
                pdf_bytes_to_process = st.session_state.get('cnh_pdf_bytes')
                first_name_to_verify = st.session_state.get('first_name')
                last_name_to_verify = st.session_state.get('last_name')

                if pdf_bytes_to_process and first_name_to_verify and last_name_to_verify:
                    verification_result_status, _ = verify_name_from_cnh_pdf(
                        pdf_bytes_to_process,
                        first_name_to_verify,
                        last_name_to_verify
                    )
                    st.session_state.verification_status = verification_result_status
                    print(f"Etapa 4: Verificação concluída com status: {verification_result_status}")
                    st.session_state.cnh_pdf_bytes = None
                    print("Etapa 4: Bytes do PDF descartados da memória.")
                else:
                    st.session_state.verification_status = "Erro: Dados Faltando para Verificação"
                    st.session_state.cnh_pdf_bytes = None
                    print("Etapa 4: Erro - Dados faltando para iniciar a verificação.")
            st.rerun()


        else:
            final_verification_status = st.session_state.verification_status
            if final_verification_status == "Verificado com Sucesso":
                st.success("Identidade Verificada com Sucesso")
            elif final_verification_status == "Pulado":
                st.warning("Verificação de identidade pulada.")
            elif final_verification_status == "Falha na Verificação (Nome não encontrado)":
                st.warning("Falha na Verificação: Nome não corresponde ao documento.")
            elif final_verification_status.startswith("Erro"):
                st.error(f"Erro durante a verificação: {final_verification_status.split(':', 1)[-1].strip()}")

            st.divider()

            st.write("--- Análise Semântica (Vetorização) ---")
            if 'user_vector' not in st.session_state:
                st.session_state.user_vector = None
            if st.session_state.user_vector is None and st_model:
                user_text_to_vectorize = prepare_user_text(st.session_state)
                if user_text_to_vectorize:
                    vector = get_vector(user_text_to_vectorize, st_model)
                    if vector is not None:
                        st.session_state.user_vector = vector
                        st.success("Vetor do perfil gerado com sucesso!")
                    else:
                        st.error("Falha ao gerar o vetor do perfil.")
                else:
                    st.warning("Não foi possível gerar o vetor: sem texto descritivo suficiente.")
            elif st.session_state.user_vector is not None:
                st.success("Vetor do perfil já foi gerado.")
            elif not st_model:
                st.error("Modelo de IA não carregado, vetorização impossível.")

            st.divider()
            st.subheader("🔥 Seu Match na FURIA!")
            if st.session_state.user_vector is not None and st_model:
                players_data = load_player_vectors('data/players_vectors.json')
                if players_data:
                    if st.session_state.get('match_result') is None:
                        print("Calculando a melhor correspondência...")
                        match_result = find_best_match(st.session_state.user_vector, players_data)
                        st.session_state.match_result = match_result
                    else:
                        match_result = st.session_state.match_result
                        print("Usando resultado da correspondência cacheado na sessão.")

                    if match_result:
                        player_name = match_result['name']
                        similarity_score = match_result['score']
                        player_description = match_result['text']
                        st.success(f"Você mais se identifica com: **{player_name}**!")
                        score_emoji = "🔥🔥🔥" if similarity_score > 0.6 else ("🔥🔥" if similarity_score > 0.4 else "🔥")
                        st.metric(label="Nível de Similaridade", value=f"{similarity_score:.2%}", delta=score_emoji)
                        with st.expander(f"Ver descrição de {player_name}"):
                            st.write(player_description)
                    else:
                        st.error("Não foi possível encontrar um jogador correspondente.")
                else:
                    st.error("Não foi possível carregar dados dos jogadores para comparação.")
            elif st.session_state.user_vector is None and st_model:
                st.warning("O vetor do seu perfil não pôde ser gerado. A comparação não pode ser realizada.")
            elif not st_model:
                st.error("O modelo de IA não pôde ser carregado. A comparação não pode ser realizada.")

            st.divider()
            if firebase_initialized and not st.session_state.get('profile_saved', False):
                print("Tentando salvar perfil no Firebase RTDB...")
                if save_user_profile_rtdb(st.session_state):
                    st.success("Seu perfil foi salvo com sucesso no nosso banco de dados!")
                    st.session_state.profile_saved = True
                else:
                    print("Falha ao salvar perfil no Firebase RTDB.")
            elif st.session_state.get('profile_saved', False):
                st.info("Seu perfil já foi salvo nesta sessão.")
            elif not firebase_initialized:
                st.warning("Não foi possível salvar o perfil (Firebase não inicializado). Verifique as configurações.")
