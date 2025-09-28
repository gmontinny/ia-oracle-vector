# Construindo uma Busca Semântica Inteligente com Oracle 23ai e Python

Em um mundo inundado por dados, encontrar informações relevantes é como procurar uma agulha no palheiro. A busca tradicional, baseada em palavras-chave, muitas vezes falha em capturar a intenção e o contexto do usuário. Se você busca por "comida para o frio", espera encontrar "sopa" ou "chocolate quente", mesmo que as palavras "comida" e "frio" não estejam presentes nessas descrições. É aqui que a busca semântica entra em cena.

Este artigo é um guia prático e detalhado para construir uma aplicação completa de busca semântica. Utilizaremos o poder do **Oracle Database 23ai**, com seu novo e revolucionário tipo de dado `VECTOR`, em conjunto com o ecossistema de Inteligência Artificial do Python, orquestrado em um ambiente Docker robusto e organizado.

## Conceitos Fundamentais

Antes de mergulhar no código, vamos entender os três pilares da nossa aplicação.

### 1. Busca Semântica vs. Busca por Palavra-Chave

A busca por palavra-chave é literal. Ela busca documentos que contenham exatamente os termos que você digitou. Já a **busca semântica** foca no significado e na intenção por trás da consulta. Ela utiliza um modelo de IA para entender que "um computador para trabalho" está semanticamente próximo de "laptop de alta performance com muita RAM", mesmo que as palavras sejam diferentes.

### 2. Vector Embeddings: A Linguagem da IA

Para que uma máquina entenda o "significado", ela precisa converter texto em números. **Vector Embeddings** (ou simplesmente "vetores") são representações numéricas de dados (como texto, imagens ou som) em um espaço multidimensional. A "mágica" é que conceitos semanticamente similares são posicionados próximos uns dos outros nesse espaço. A distância entre dois vetores indica o quão relacionados eles são.

Para criar esses vetores a partir de texto, nossa aplicação suporta duas abordagens:
- **Sentence Transformers**: Biblioteca open-source com modelos como `all-MiniLM-L6-v2` (384 dimensões)
- **OpenAI Embeddings**: API da OpenAI com o modelo `text-embedding-3-small` (1536 dimensões)

### 3. Oracle 23ai: O Banco de Dados para a Era da IA

Historicamente, bancos de dados relacionais não foram projetados para lidar com vetores. A solução comum era usar um banco de dados vetorial especializado, separado do banco de dados principal, o que introduzia complexidade, custos e problemas de sincronização de dados.

O **Oracle Database 23ai** resolve esse problema de forma elegante com a introdução do tipo de dado nativo `VECTOR` e operadores de busca vetorial como `VECTOR_DISTANCE`. Isso permite:

*   **Armazenamento Unificado:** Guarde seus dados relacionais (ID, nome, preço) e seus dados vetoriais na mesma tabela e no mesmo banco de dados.
*   **Performance:** Execute buscas por similaridade de forma extremamente rápida e eficiente, diretamente no banco.
*   **Busca Híbrida:** Combine a busca vetorial com filtros relacionais tradicionais em uma única consulta SQL (ex: encontre produtos semanticamente similares a "roupas de verão" que também custam menos de R$100 e estão em estoque).

## Arquitetura do Nosso Projeto

Nosso projeto é orquestrado pelo Docker e possui uma estrutura clara que separa responsabilidades:

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
`-- README.md             # Guia rápido de execução
```

*   **`docker-compose.yml`**: Define e conecta nossos dois serviços: o banco de dados `oracle-db` e a nossa `app` Python.
*   **`app/Dockerfile`**: Constrói a imagem da nossa aplicação, instalando o Python e as dependências listadas no `requirements.txt`.
*   **`app/main.py`**: É o nosso ponto de entrada, que direciona a execução para o módulo de ingestão ou de busca, dependendo do comando fornecido.

## Implementação Passo a Passo

Vamos analisar os trechos de código mais importantes.

### Passo 1: A Ingestão de Dados (`ingest.py`)

O primeiro passo é popular nosso banco de dados. O script `ingest.py` é responsável por isso.

**A. Criando a Tabela:**
Primeiro, criamos a tabela `products`. A dimensão da coluna `embedding` é ajustada dinamicamente: 384 para Sentence Transformers ou 1536 para OpenAI.

```python
cursor.execute(f"""
    CREATE TABLE products (
        product_id NUMBER,
        product_name VARCHAR2(255),
        description VARCHAR2(1000),
        embedding VECTOR({vector_dim}, FLOAT32)
    )
""")
```

**B. Gerando e Inserindo os Vetores:**
O sistema detecta automaticamente qual modelo usar baseado na variável de ambiente `USE_OPENAI`. Para resolver problemas de binding com vetores grandes, utilizamos `array.array`:

```python
# Gera os Embeddings
if use_openai:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    embeddings = []
    for desc in descriptions:
        response = client.embeddings.create(input=desc, model="text-embedding-3-small")
        embeddings.append(response.data[0].embedding)
else:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(descriptions)

# Prepara e Insere os Dados
for i, row in df.iterrows():
    if use_openai:
        embedding_vector = array.array('f', embeddings[i])
    else:
        embedding_vector = array.array('f', embeddings[i].tolist())

    cursor.execute("""
        INSERT INTO products (product_id, product_name, description, embedding)
        VALUES (:1, :2, :3, :4)
    """, [product_id, product_name, description, embedding_vector])
```

### Passo 2: A Busca Semântica (`search.py`)

Com os dados no banco, podemos realizar a busca.

**A. Vetorizando a Consulta:**
A consulta é vetorizada usando o mesmo modelo configurado durante a ingestão:

```python
# Gera o Embedding para a consulta
if use_openai:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.embeddings.create(input=search_query, model="text-embedding-3-small")
    query_embedding = array.array('f', response.data[0].embedding)
else:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = array.array('f', model.encode(search_query).tolist())
```

**B. Executando a Busca Vetorial:**
Com `array.array`, o Oracle reconhece automaticamente o formato vetorial, simplificando a consulta:

```python
cursor.execute("""
    SELECT product_name, description, VECTOR_DISTANCE(embedding, :1, COSINE) as distance
    FROM products
    ORDER BY distance
    FETCH FIRST 5 ROWS ONLY
""", [query_embedding])
```

O resultado é uma lista de produtos cuja descrição melhor corresponde ao *significado* da sua busca.

## Desafios Técnicos Superados

Durante o desenvolvimento, enfrentamos alguns desafios técnicos importantes:

### 1. Binding de Arrays no Oracle
O erro `ORA-01484: arrays can only be bound to PL/SQL statements` foi resolvido usando `array.array('f', ...)` em vez de listas Python, permitindo que o Oracle reconheça automaticamente o formato vetorial.

### 2. Limite VARCHAR2 para Embeddings Grandes
Embeddings da OpenAI (1536 dimensões) convertidos para string excedem o limite VARCHAR2. A solução foi usar `array.array` diretamente, evitando conversões desnecessárias.

### 3. Flexibilidade de Modelos
Implementamos detecção automática do modelo baseada em variáveis de ambiente, ajustando dinamicamente as dimensões da tabela Oracle.

## Conclusão e Próximos Passos

Construímos com sucesso uma aplicação de busca semântica do zero, demonstrando como a combinação do Oracle 23ai com o ecossistema de IA do Python oferece uma solução poderosa e integrada. Eliminamos a necessidade de um banco de dados vetorial separado, simplificando a arquitetura e abrindo portas para consultas híbridas complexas.

Este projeto é apenas o começo. A partir daqui, você pode evoluir a aplicação:

*   **Construir uma API:** Crie uma API REST (com Flask ou FastAPI) em torno do `search.py` para servir os resultados a uma aplicação web ou móvel.
*   **Experimentar Modelos:** Alterne entre Sentence Transformers e OpenAI, ou experimente outros modelos da família `multilingual-e5` para suportar múltiplos idiomas.
*   **Implementar Busca Híbrida:** Adicione filtros de metadados à sua busca. Modifique a consulta SQL para filtrar por categoria, preço ou data de lançamento antes de aplicar a busca por similaridade vetorial.

A era da IA nos bancos de dados relacionais chegou, e o Oracle 23ai está na vanguarda dessa revolução.
