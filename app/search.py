import os
import sys
import oracledb
from sentence_transformers import SentenceTransformer

def run_search(search_query: str):
    """Conecta-se ao banco de dados, gera o embedding da consulta e realiza uma busca vetorial."""
    print(f"Buscando por: '{search_query}'\n")

    # 1. Carrega o Modelo
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 2. Gera o Embedding para a consulta
    query_embedding = str(model.encode(search_query).tolist())

    # 3. Detalhes da Conexão com o Banco de Dados
    user = os.getenv('ORACLE_USER', 'sys')
    password = os.getenv('ORACLE_PASSWORD', 'oracle')
    dsn = os.getenv('ORACLE_DSN', 'oracle-db:1521/FREEPDB1')

    # 4. Conecta ao banco de dados e realiza a busca
    with oracledb.connect(user=user, password=password, dsn=dsn, mode=oracledb.SYSDBA) as conn:
        with conn.cursor() as cursor:
            # 5. Realiza a Busca Vetorial
            cursor.execute("""
                SELECT product_name, description, VECTOR_DISTANCE(embedding, TO_VECTOR(:1), COSINE) as distance
                FROM products
                ORDER BY distance
                FETCH FIRST 5 ROWS ONLY
            """, [query_embedding])

            results = cursor.fetchall()

    # 6. Exibe os Resultados
    print(f"Resultados da busca para: '{search_query}'\n")
    if not results:
        print("Nenhum produto correspondente encontrado.")
        return

    for row in results:
        product_name, description, distance = row
        print(f"- Produto: {product_name}")
        print(f"  Descrição: {description}")
        print(f"  Similaridade: {1 - distance:.4f}") # A distância de cosseno é 1 - similaridade
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python search.py \"<sua consulta de busca>\"")
        sys.exit(1)
    run_search(sys.argv[1])
