import json
import os

from sentence_transformers import SentenceTransformer

# --- Configurações ---
INPUT_JSON_PATH = '../data/players.json'
OUTPUT_JSON_PATH = '../data/players_vectors.json'
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'


def generate_embeddings():
    """
    Carrega os dados dos jogadores, gera embeddings para suas descrições
    e salva um novo JSON com nome, texto original e embedding.
    """
    print(f"Carregando o modelo Sentence Transformer...")
    model = SentenceTransformer(MODEL_NAME)
    print("Modelo carregado com sucesso.")

    if not os.path.exists(INPUT_JSON_PATH):
        print(f"ERRO: Arquivo de entrada '{INPUT_JSON_PATH}' não encontrado.")
        return

    print(f"Lendo dados dos jogadores de '{INPUT_JSON_PATH}'...")
    try:
        with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            players_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERRO: Falha ao decodificar o JSON de entrada: {e}")
        return
    except Exception as e:
        print(f"ERRO inesperado ao ler o arquivo de entrada: {e}")
        return

    player_embeddings_list = []
    total_players = len(players_data)
    print(f"Gerando embeddings para {total_players} jogadores...")

    for i, (player_name, description_text) in enumerate(players_data.items()):
        print(f"  Processando [{i + 1}/{total_players}]: {player_name}")

        if not isinstance(description_text, str) or not description_text:
            print(f"    AVISO: Descrição inválida ou vazia para {player_name}. Pulando.")
            continue

        try:
            embedding = model.encode(description_text, convert_to_numpy=True)

            embedding_list = embedding.tolist()

            player_embeddings_list.append({
                "name": player_name,
                "text": description_text,
                "embedding": embedding_list
            })
        except Exception as e:
            print(f"Erro ao processar {player_name}: {e}")

    print(f"\nSalvando os dados processados em '{OUTPUT_JSON_PATH}'...")
    try:
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(player_embeddings_list, f, indent=2, ensure_ascii=False)
        print("Arquivo de embeddings salvo com sucesso!")
    except Exception as e:
        print(f"Erro inesperado ao salvar o arquivo de saída: {e}")


if __name__ == "__main__":
    generate_embeddings()
