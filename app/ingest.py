import os
import pandas as pd
import oracledb
from sentence_transformers import SentenceTransformer

def run_ingestion():
    """Conecta-se ao banco de dados, gera os embeddings e ingere os dados."""
    print("Iniciando a ingestão de dados...")

    # 1. Carrega o Modelo
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 2. Lê os dados do CSV
    df = pd.read_csv('data/products.csv')

    # 3. Gera os Embeddings
    descriptions = df['description'].tolist()
    embeddings = model.encode(descriptions)

    # 4. Detalhes da Conexão com o Banco de Dados
    user = os.getenv('ORACLE_USER', 'sys')
    password = os.getenv('ORACLE_PASSWORD', 'oracle')
    dsn = os.getenv('ORACLE_DSN', 'oracle-db:1521/FREEPDB1')

    # Estabelece a conexão como SYSDBA
    with oracledb.connect(user=user, password=password, dsn=dsn, mode=oracledb.SYSDBA) as conn:
        with conn.cursor() as cursor:
            # 5. Cria a Tabela com a coluna VECTOR
            try:
                cursor.execute("DROP TABLE products")
            except oracledb.DatabaseError as e:
                if e.args[0].code != 942: # ORA-00942: tabela ou view não existe
                    raise

            cursor.execute("""
                CREATE TABLE products (
                    product_id NUMBER,
                    product_name VARCHAR2(255),
                    description VARCHAR2(1000),
                    embedding VECTOR(384, FLOAT32)
                )
            """)

            # 6. Prepara e Insere os Dados
            for i, row in df.iterrows():
                product_id = int(row['product_id'])
                product_name = row['product_name']
                description = row['description']
                embedding_vector = str(embeddings[i].tolist())

                cursor.execute("""
                    INSERT INTO products (product_id, product_name, description, embedding)
                    VALUES (:1, :2, :3, TO_VECTOR(:4))
                """, [product_id, product_name, description, embedding_vector])

            conn.commit()

    print("Ingestão de dados completa!")

if __name__ == "__main__":
    run_ingestion()
