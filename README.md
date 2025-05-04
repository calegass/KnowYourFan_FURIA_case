# Know Your Fan - FURIA

Este projeto foi desenvolvido como um protótipo funcional para demonstrar a estratégia "Know Your Fan", aplicando-a ao
universo da FURIA Esports, por Matheus Calegari.

---

## Funcionalidades Principais

* **Coleta de Dados Multi-etapas:** interface amigável construída com Streamlit para coletar dados básicos (nome,
  cidade), preferências de jogo (CS/LoL, role, nickname) e interesses (estilo de jogo, acompanhamento de campeonatos).
* **Verificação de Identidade (Opcional via OCR):** Permite o upload de um PDF da CNH Digital para verificar o nome
  fornecido pelo usuário.
    * Utiliza **EasyOCR** e **PyMuPDF** para extrair texto da imagem do PDF.
    * **Privacidade:** O arquivo PDF é processado em memória e **não é salvo permanentemente**. Apenas o status da
      verificação é registrado.
* **Matching de Jogador com IA:**
    * Gera um vetor (embedding) representando o perfil do fã com base em suas respostas usando **Sentence Transformers** (`paraphrase-multilingual-mpnet-base-v2`).
    * Compara o vetor do fã com vetores pré-calculados de jogadores da FURIA (CS e LoL) usando **similaridade de cosseno** (`scikit-learn`).
    * Exibe o jogador mais similar e o nível de similaridade.
* **Persistência de Dados:** Salva os dados do perfil do usuário (incluindo status de verificação e resultado do match)
  no **Firebase Realtime Database**.
* **Dockerizado:** Configuração completa com `Dockerfile` e `docker-compose.yml` para fácil execução e deploy,
  necessitando apenas configurar credenciais do Firebase em `.env` e `firebase-service-account.json`.

---

## Tecnologias Utilizadas

* **Linguagem:** Python 3.11
* **Web Framework:** Streamlit
* **Inteligência Artificial (Embeddings):** `sentence-transformers`
* **Inteligência Artificial (OCR):** `EasyOCR`
* **Processamento de PDF:** PyMuPDF
* **Computação Científica/Vetores:** `scikit-learn`
* **Banco de Dados:** Firebase Realtime Database (`firebase-admin`)
* **Variáveis de Ambiente:** `python-dotenv`
* **Containerização:** Docker, Docker Compose
* **Gerenciador de Pacotes:** UV

---

## Como Usar a Aplicação

* **Acesso:** Abra a URL onde a aplicação está rodando (ex: `http://localhost:8501` se executando localmente via
  Docker).
* **Preenchimento:** Siga as etapas do formulário:
    1. **Dados Básicos:** Insira seu nome, sobrenome, cidade, jogo preferido (CS/LoL), role principal e nickname.
    2. **Interesses:** Descreva seu estilo de jogo e responda a perguntas sobre seus hábitos como fã.
    3. **Verificação (Opcional):** Se desejar, faça o upload do PDF da sua CNH Digital para validar seu nome. Lembre-se
       da nossa política de privacidade (o arquivo não é salvo). Você pode pular esta etapa.
* **Resultado:** Após a última etapa, a aplicação processará seus dados, realizará a verificação (se aplicável), gerará
  seu perfil vetorial e mostrará o jogador da FURIA com quem você mais se identifica, com o nível de similaridade.
  Seu perfil (sem o PDF) será salvo no banco de dados.

---

## Configuração e Execução

Existem duas maneiras principais de executar a aplicação: localmente ou via Docker (recomendado).

**Pré-requisitos:**

* Git
* Python 3.11 ou superior (se for rodar localmente) (idealmente 3.11.9/12 que foi o que usei e não testei em versões anteriores/superiores)
* UV (gerenciador de pacotes Python)
* Docker e Docker Compose (se for usar Docker)
* Conta no [Firebase](https://console.firebase.google.com/):
    * Projeto Firebase criado.
    * **Realtime Database** ativado (Copiar a URL do banco).
    * **Chave de Conta de Serviço (Service Account Key):** Gerada nas configurações do projeto Firebase (arquivo JSON).

**1. Clonar o Repositório:**

```bash
git clone https://github.com/calegass/KnowYourFan_FURIA_case.git
cd KnowYourFan_FURIA_case
```

**2. Configurar Variáveis de Ambiente:**

Crie um arquivo .env na raiz do projeto e adicione as seguintes variáveis:

```
FIREBASE_SERVICE_ACCOUNT_PATH
FIREBASE_DATABASE_URL
```

Adicione também as credenciais do Firebase no arquivo `firebase-service-account.json` na raiz do projeto.

**3. Rodar o Docker Compose:**

```bash
docker-compose up --build -d
```
Para acompanhar os logs da aplicação, você pode usar: `docker-compose logs -f know-your-fan-furia`