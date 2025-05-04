import json
import os

import numpy as np
import streamlit as st
from numpy import ndarray
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


@st.cache_resource
def load_model(model_name: str = 'paraphrase-multilingual-mpnet-base-v2'):
    """Carrega o modelo Sentence Transformer."""
    print(f"Carregando modelo Sentence Transformer: {model_name}...")
    model = SentenceTransformer(model_name)
    print("Modelo carregado com sucesso.")
    return model


def prepare_user_text(user_data: dict) -> str:
    """Combina os dados relevantes do usuário em uma única string descritiva."""
    parts = []
    if user_data.get('fav_game') and user_data['fav_game'] != "Selecione":
        parts.append(f"Jogo preferido: {user_data['fav_game']}.")
    if user_data.get('role') and user_data['role'] != "Selecione uma role":
        parts.append(f"Role principal: {user_data['role']}.")
    if user_data.get('playstyle_desc'):
        parts.append(f"Descrição do estilo: {user_data['playstyle_desc']}.")

    return " ".join(parts)


def get_vector(text: str, model: SentenceTransformer) -> ndarray | None:
    """Gera o vetor (embedding) para um dado texto usando o modelo carregado."""
    if not text or not model:
        return None
    vector = model.encode(text, convert_to_numpy=True)
    return vector


@st.cache_data
def load_player_vectors(filepath: str = 'players_vectors.json') -> list[dict] | None:
    """Carrega os dados e vetores dos jogadores do arquivo JSON."""
    if not os.path.exists(filepath):
        st.error(f"Arquivo de vetores dos jogadores não encontrado: {filepath}")
        print(f"Erro: Arquivo de vetores dos jogadores não encontrado: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            players_data = json.load(f)
        print(f"Vetores de {len(players_data)} jogadores carregados de {filepath}.")
        return players_data
    except json.JSONDecodeError as e:
        st.error(f"Erro ao ler o JSON dos jogadores: {e}")
        print(f"Erro: Falha ao decodificar JSON em {filepath}: {e}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado ao carregar dados dos jogadores: {e}")
        print(f"Erro inesperado ao carregar {filepath}: {e}")
        return None


def find_best_match(user_vector: np.ndarray, players_data: list[dict]) -> dict | None:
    """
    Encontra o jogador com o vetor mais similar ao vetor do usuário.

    Args:
        user_vector: O vetor (embedding NumPy array) do usuário;
        players_data: lista de dicionários, cada um contendo 'name', 'text', 'embedding' (como lista).

    Returns:
        Um dicionário com 'name', 'score' (similaridade) e 'text' do jogador correspondente,
        ou None se não for possível encontrar uma correspondência.
    """
    if user_vector is None or not players_data:
        print("Vetor do usuário ou dados dos jogadores inválidos para find_best_match.")
        return None

    try:
        player_embeddings = np.array(
            [np.array(player['embedding']) for player in players_data if 'embedding' in player])

        if player_embeddings.ndim != 2 or player_embeddings.shape[0] == 0:
            print(
                f"Erro: A matriz de embeddings dos jogadores não tem o formato esperado. Shape: {player_embeddings.shape}")
            return None

        user_vector_2d = user_vector.reshape(1, -1)

        similarities = cosine_similarity(user_vector_2d, player_embeddings)

        best_match_index = np.argmax(similarities[0])

        best_score = similarities[0][best_match_index]

        best_player_data = players_data[best_match_index]

        print(f"Melhor correspondência encontrada: {best_player_data['name']} com score {best_score:.4f}")

        return {
            "name": best_player_data['name'],
            "score": float(best_score),
            "text": best_player_data.get('text', 'Descrição não disponível.')
        }

    except Exception as e:
        st.error(f"Erro ao calcular a similaridade: {e}")
        print(f"Erro durante o cálculo de similaridade: {e}")
        return None
