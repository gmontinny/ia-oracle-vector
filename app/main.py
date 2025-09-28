import argparse
from ingest import run_ingestion
from search import run_search

def main():
    """Ponto de entrada principal para a aplicação."""
    parser = argparse.ArgumentParser(description="Aplicação de Busca Vetorial para o Oracle DB.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Comandos disponíveis")

    # Sub-comando para ingestão de dados
    parser_ingest = subparsers.add_parser("ingest", help="Executa o processo de ingestão de dados.")

    # Sub-comando para busca
    parser_search = subparsers.add_parser("search", help="Executa uma busca semântica.")
    parser_search.add_argument("query", type=str, help="A consulta de busca em linguagem natural.")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingestion()
    elif args.command == "search":
        run_search(args.query)

if __name__ == "__main__":
    main()
