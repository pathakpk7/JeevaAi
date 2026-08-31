import argparse
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config
from src.logging_config import logger
from src.ingestion.pipeline import run_ingestion
from src.vectorstore.manager import VectorStoreManager

def main():
    parser = argparse.ArgumentParser(description="Medical Knowledge Vector Indexing CLI")
    parser.add_argument("--pdf-path", type=str, default=None, help="Path to source medical PDF")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages to index for testing")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index from scratch (resets existing collection)")
    parser.add_argument("--reset", action="store_true", help="Reset/clear the vector store collection without indexing")
    parser.add_argument("--info", action="store_true", help="Display vector store status and sample metadata")

    args = parser.parse_args()
    config = get_config()
    target_pdf = args.pdf_path or str(config.get_absolute_pdf_path())

    manager = VectorStoreManager()

    print("\n============================================================")
    print("      MEDICAL KNOWLEDGE ASSISTANT — VECTOR INDEXING CLI    ")
    print("============================================================")

    if args.info:
        stats = manager.load_store()
        print("\n---------------- VECTOR STORE INFORMATION ----------------")
        print(f"Collection Name     : {stats['collection_name']}")
        print(f"Vector Count        : {stats['vector_count']}")
        print(f"Embedding Model     : {stats['embedding_model']}")
        print(f"Embedding Dimension : {stats['embedding_dimension']}")
        print(f"Persist Directory   : {stats['persist_directory']}")

        if stats['sample_metadata']:
            print("\n---------------- SAMPLE RECORD METADATA ----------------")
            meta = stats['sample_metadata']
            print(f"Article Title : {meta.get('article_title')}")
            print(f"Section       : {meta.get('section')}")
            print(f"Page Number   : {meta.get('page')}")
            print(f"Chunk ID      : {meta.get('chunk_id')}")
            print("Preview       :")
            print("-" * 50)
            print(stats['sample_document_preview'])
            print("-" * 50)

        print("\n[SUCCESS] Vector store inspection complete.\n")
        return

    if args.reset:
        stats = manager.reset_store()
        print("\n---------------- RESET RESULT ----------------")
        print(f"Status        : {stats['status']}")
        print(f"Collection    : {stats['collection_name']}")
        print(f"Vector Count  : {stats['vector_count']}")
        print("\n[SUCCESS] Vector store reset complete.\n")
        return

    # Ingestion & Indexing Workflow
    print(f"Target PDF Path : {target_pdf}")
    print(f"Page Limit      : {args.limit if args.limit else 'All pages'}")
    print(f"Operation Mode  : {'REBUILD' if args.rebuild else 'INDEX (Idempotent)'}")
    print("============================================================\n")

    logger.info("Executing Phase 1 Ingestion Pipeline...")
    chunks, ingestion_stats = run_ingestion(pdf_path=target_pdf, max_pages=args.limit, save_output=False)

    logger.info(f"Generating embeddings and indexing {len(chunks)} chunks into ChromaDB...")
    if args.rebuild:
        index_stats = manager.rebuild_store(chunks)
    else:
        index_stats = manager.index_documents(chunks)

    print("\n============================================================")
    print("             MEDICAL KNOWLEDGE INDEX METRICS                ")
    print("============================================================")
    print(f"Operation Mode          : {index_stats['operation']}")
    print(f"Pages Processed         : {ingestion_stats['useful_pages']} / {ingestion_stats['total_pages']}")
    print(f"Chunks Generated        : {ingestion_stats['total_chunks']}")
    print(f"Vectors Stored (Total)  : {index_stats['vector_count']}")
    print(f"Embedding Model         : {index_stats['embedding_model']}")
    print(f"Embedding Dimension     : {index_stats['embedding_dimension']}")
    print(f"Collection Name         : {index_stats['collection_name']}")
    print(f"Vector Store Path       : {index_stats['persist_directory']}")
    print(f"Status                  : {index_stats['status']}")
    print("============================================================\n")

if __name__ == "__main__":
    main()
