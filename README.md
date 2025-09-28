# Projeto de Busca Vetorial com Oracle 23ai e Sentence Transformers

Este projeto demonstra como implementar uma busca por similaridade semântica utilizando o Oracle Database 23ai e modelos de linguagem da biblioteca `sentence-transformers`. A aplicação consiste em ingerir uma lista de produtos, gerar embeddings (vetores) para suas descrições e, em seguida, realizar buscas baseadas em linguagem natural para encontrar os produtos mais relevantes.

## Estrutura do Projeto

O projeto está organizado da seguinte forma para maior clareza e manutenibilidade:

```
/oracle
|-- app/                  # Contém a lógica da aplicação
|   |-- Dockerfile          # Define o ambiente da aplicação Python
|   |-- main.py             # Ponto de entrada principal da aplicação
|   |-- ingest.py           # Módulo para ingerir e vetorizar os dados
|   |-- search.py           # Módulo para realizar a busca semântica
|   `-- requirements.txt    # Lista de dependências Python
|-- data/                 # Contém os dados brutos
|   `-- products.csv        # Arquivo CSV com os produtos
|-- docker-compose.yml    # Orquestra os serviços da aplicação e do banco de dados
`-- README.md             # Esta documentação
```

## Como Funciona

1.  **Orquestração com Docker:** O `docker-compose.yml` sobe dois serviços:
    *   `oracle-db`: Uma instância do Oracle Database 23ai Free.
    *   `app`: Um contêiner Python com as dependências instaladas a partir do `requirements.txt`.

2.  **Ponto de Entrada (`main.py`):**
    *   Serve como o orquestrador principal, fornecendo uma interface de linha de comando (CLI) para executar as diferentes ações do projeto: `ingest` e `search`.

3.  **Ingestão de Dados (`ingest.py`):
    *   Quando chamado pelo comando `ingest`, este módulo lê o arquivo `data/products.csv`.
    *   Utiliza o modelo `all-MiniLM-L6-v2` (sentence-transformers) ou `text-embedding-3-small` (OpenAI) para converter as descrições dos produtos em vetores.
    *   Conecta-se ao banco de dados Oracle, cria uma tabela `products` com uma coluna `VECTOR` e insere os dados e vetores.

4.  **Busca Semântica (`search.py`):**
    *   Quando chamado pelo comando `search`, este módulo recebe uma consulta em linguagem natural.
    *   Gera um vetor para essa consulta usando o mesmo modelo configurado (sentence-transformers ou OpenAI).
    *   Executa uma busca por similaridade de cosseno no Oracle DB utilizando a função `VECTOR_DISTANCE`.
    *   Retorna os produtos mais relevantes.

## Pré-requisitos

*   Docker
*   Docker Compose

## Como Executar

Execute os seguintes comandos a partir do diretório raiz do projeto (`C:/projetos-ia/oracle/`):

1.  **Construir e Iniciar os Contêineres:**
    Este comando irá construir a imagem da aplicação e iniciar os contêineres em segundo plano. Pode levar alguns minutos para o Oracle DB iniciar completamente na primeira vez.

    ```sh
    docker-compose up -d --build
    ```

2.  **Executar a Ingestão de Dados:**
    Use o comando `ingest` para popular o banco de dados.

    ```sh
    docker-compose exec app python main.py ingest
    ```

    Aguarde a mensagem: `Ingestão de dados completa!`

3.  **Realizar uma Busca:**
    Use o comando `search` seguido da sua consulta entre aspas.

    ```sh
    docker-compose exec app python main.py search "um computador para trabalho"
    ```

    **Exemplo de Saída:**
    ```
    Resultados da busca para: 'um computador para trabalho'

    - Produto: Laptop
      Descrição: High-performance laptop with 16GB RAM and 512GB SSD.
      Similaridade: 0.85...
    ```

## Usando Embeddings da OpenAI

Para usar embeddings da OpenAI em vez do sentence-transformers:

1. **Altere a variável de ambiente no docker-compose.yml:**
   ```yaml
   - USE_OPENAI=true
   ```

2. **Reconstrua e execute:**
   ```sh
   docker-compose up -d --build
   docker-compose exec app python main.py ingest
   ```

## Experimentando

*   **Novas Buscas:** Tente diferentes consultas para ver a relevância dos resultados.
  ```sh
  docker-compose exec app python main.py search "bom som"
  docker-compose exec app python main.py search "algo para digitar"
  ```
*   **Novos Dados:** Adicione mais produtos ao arquivo `data/products.csv` e execute o comando de ingestão novamente.
*   **Outros Modelos:** Você pode experimentar outros modelos de `sentence-transformers`. Para isso, altere o nome do modelo nos arquivos `ingest.py` e `search.py`. Se o novo modelo tiver uma dimensão de embedding diferente, você precisará ajustar a declaração da coluna `VECTOR` no script `ingest.py` (ex: `VECTOR(768, FLOAT32)`).
