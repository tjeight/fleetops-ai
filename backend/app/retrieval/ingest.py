import os
import sys
from app.retrieval.chroma_store import retriever

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sop_dir = os.path.join(base_dir, "data", "sops")
    print(f"[Ingestion] Scanning SOP directory: {sop_dir}")
    
    if not os.path.exists(sop_dir):
        print(f"[Ingestion] ERROR: Directory {sop_dir} does not exist.")
        sys.exit(1)
        
    chunks_count = retriever.ingest_sop_directory(sop_dir)
    print(f"[Ingestion] SUCCESS: Ingested {chunks_count} procedure chunks into ChromaDB.")

if __name__ == "__main__":
    main()
