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

def main():
    parser = argparse.ArgumentParser(description="Medical PDF Ingestion Engine CLI")
    parser.add_argument("--pdf-path", type=str, default=None, help="Path to PDF source document")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages to process for testing")
    parser.add_argument("--save", action="store_true", help="Save processed output artifact to data/processed/chunks.json")
    parser.add_argument("--sample", type=int, default=3, help="Number of sample chunks to display for inspection")

    args = parser.parse_args()
    config = get_config()
    target_pdf = args.pdf_path or str(config.get_absolute_pdf_path())

    print("\n============================================================")
    print("        MEDICAL KNOWLEDGE ASSISTANT — PDF INGESTION         ")
    print("============================================================")
    print(f"Target PDF Path : {target_pdf}")
    print(f"Page Processing Limit : {args.limit if args.limit else 'All pages'}")
    print(f"Save Artifacts : {args.save}")
    print("============================================================\n")

    try:
        chunks, stats = run_ingestion(pdf_path=target_pdf, max_pages=args.limit, save_output=args.save)
    except Exception as e:
        logger.error(f"Ingestion failed with error: {e}")
        sys.exit(1)

    print("------------------------------------------------------------")
    print("                  INGESTION METRICS SUMMARY                 ")
    print("------------------------------------------------------------")
    print(f"Total Pages Processed   : {stats['total_pages']}")
    print(f"Pages With Useful Text  : {stats['useful_pages']}")
    print(f"Empty / Blank Pages     : {stats['empty_pages']}")
    print(f"Total Chunks Created    : {stats['total_chunks']}")
    print(f"Average Chunk Size      : {stats['avg_chunk_size']} chars")
    print(f"Article Coverage        : {stats['article_coverage_pct']}%")
    print(f"Section Coverage        : {stats['section_coverage_pct']}%")
    print("------------------------------------------------------------\n")

    if args.sample > 0 and chunks:
        sample_count = min(args.sample, len(chunks))
        print(f"================ SAMPLE CHUNKS PREVIEW ({sample_count} of {len(chunks)}) ================")
        for i in range(sample_count):
            c = chunks[i]
            meta = c.metadata
            print(f"\n[Chunk {i+1} / {len(chunks)}]")
            print(f"Chunk ID      : {meta.get('chunk_id')}")
            print(f"Article Title : {meta.get('article_title')}")
            print(f"Section       : {meta.get('section')}")
            print(f"Page Number   : {meta.get('page')}")
            print(f"Length        : {meta.get('length')} characters")
            print("Content Preview:")
            print("-" * 50)
            preview_text = c.page_content[:350] + ("..." if len(c.page_content) > 350 else "")
            print(preview_text)
            print("-" * 50)

    print("\n[SUCCESS] PDF Ingestion completed successfully.\n")

if __name__ == "__main__":
    main()
