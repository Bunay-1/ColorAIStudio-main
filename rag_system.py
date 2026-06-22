"""
IRM RAG System — Retrieval-Augmented Generation (Advanced) - Qdrant Edition (Async + Hybrid + Ollama)
================================================================================================
- Vector DB: Qdrant (Async, On-disk storage, Quantization)
- Hybrid Search: Dense + Sparse (SPLADE via FastEmbed)
- Multi-Model Embeddings: Local (MiniLM) or Ollama (nomic-embed-text)
- Semantic Chunking, GraphRAG & Cross-Encoder
"""

import os
import json
import logging
import time
import cv2
import pandas as pd
import zipfile
import shutil
import uuid
import asyncio
from pathlib import Path
from pypdf import PdfReader
import pandas as pd
from docx import Document
from lxml import etree
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np
from sentence_transformers import CrossEncoder
from knowledge_graph import IndustrialKG
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from fastembed import SparseTextEmbedding
import httpx

# Конфигуриране на логване
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGSystem")

class OllamaEmbeddings:
    """Клас за генериране на embeddings чрез Ollama API (Асинхронен)."""
    def __init__(self, url, model):
        self.url = url
        self.model = model
        self.client = None

    async def _ensure_client(self):
        if self.client is None:
            timeout = float(os.environ.get("OLLAMA_TIMEOUT", "180.0"))
            self.client = httpx.AsyncClient(timeout=timeout)

    async def _get_embedding(self, text):
        await self._ensure_client()
        try:
            response = await self.client.post(self.url, json={"model": self.model, "prompt": text})
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Ollama Embedding Error: {e}")
            return [0.0] * 768

    async def embed_documents(self, texts):
        results = []
        for text in texts:
            emb = await self._get_embedding(text)
            results.append(emb)
        return results

    async def embed_query(self, text):
        return await self._get_embedding(text)

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

class IRM_RAG:
    def _is_cuda_available(self):
        try:
            import torch
            return torch.cuda.is_available()
        except: return False

    def __init__(self, db_path="./qdrant_db", lightweight=None):
        self.db_path = db_path
        self.enabled = False
        self.client = None
        self.collection_name = "industrial_docs_v3"
        self.kg = IndustrialKG()

        self.edge_mode = os.environ.get("ICAP_EDGE_MODE", "0") == "1"
        self.lightweight = lightweight if lightweight is not None else self.edge_mode

        # Настройка на Embeddings
        self.embed_type = os.environ.get("EMBEDDING_TYPE", "local").lower()
        if self.embed_type == "ollama":
            url = os.environ.get("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
            model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
            self.hf_embeddings = OllamaEmbeddings(url, model)
            self.vector_size = 768
            logger.info(f"Using Ollama Embeddings: {model}")
        else:
            os.environ["TRANSFORMERS_OFFLINE"] = "1" if os.path.exists("./models/embeddings") else "0"
            embedding_model = "./models/embeddings" if os.path.exists("./models/embeddings") else "paraphrase-multilingual-MiniLM-L12-v2"
            self.hf_embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cuda' if self._is_cuda_available() else 'cpu'}
            )
            self.vector_size = 384
            logger.info(f"Using Local Embeddings: {embedding_model}")

        # Sparse Embeddings (Lazy Loaded)
        self._sparse_embeddings_model = None

        # Семантичен разделител с настройки от .env
        chunk_size = int(os.environ.get("RAG_CHUNK_SIZE", "1000"))
        chunk_overlap = int(os.environ.get("RAG_CHUNK_OVERLAP", "150"))

        self.semantic_splitter = SemanticChunker(
            HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2"),
            breakpoint_threshold_type="percentile"
        )
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        
        try:
            if self.lightweight:
                self.reranker = None
                logger.info("LIGHTWEIGHT MODE: Cross-Encoder reranker is disabled.")
            else:
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except Exception as e:
            logger.warning(f"Re-ranker load failed: {e}")
            self.reranker = None

    async def initialize(self):
        """Асинхронна инициализация на Qdrant с автоматичен fallback към Local."""
        try:
            qdrant_url = os.environ.get("QDRANT_URL")
            connected = False

            if qdrant_url:
                try:
                    logger.info(f"Connecting to remote Qdrant at: {qdrant_url}...")
                    self.client = AsyncQdrantClient(url=qdrant_url, timeout=5)
                    # Проверка на връзката
                    await self.client.get_collections()
                    connected = True
                    logger.info("Connected to remote Qdrant.")
                except Exception as re:
                    logger.error(f"Remote Qdrant connection failed: {re}. Falling back to local.")
                    self.client = None

            if not connected:
                logger.info(f"Using local Qdrant at: {self.db_path}")
                try:
                    self.client = AsyncQdrantClient(path=self.db_path)
                except Exception as local_error:
                    logger.error(f"Local Qdrant initialization failed: {local_error}")
                    raise RuntimeError(f"Failed to initialize Qdrant (both remote and local): {local_error}") from local_error

            collections = (await self.client.get_collections()).collections
            exists = any(c.name == self.collection_name for c in collections)

            if exists:
                info = await self.client.get_collection(self.collection_name)
                current_size = info.config.params.vectors["dense"].size
                if current_size != self.vector_size:
                    logger.warning(f"Vector size mismatch. Resetting collection...")
                    await self.reset_collection()
            else:
                await self.reset_collection()

            self.enabled = True
            logger.info("Async Hybrid RAG Ready.")
        except Exception as e:
            logger.error(f"Init Error: {e}")
            self.enabled = False
            raise RuntimeError(f"RAG System initialization failed: {e}") from e

    async def reset_collection(self):
        """Пълно изчистване и пресъздаване на колекцията."""
        if self.client is None: return

        collections = (await self.client.get_collections()).collections
        if any(c.name == self.collection_name for c in collections):
            await self.client.delete_collection(self.collection_name)

        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                    on_disk=True,
                    quantization_config=models.ScalarQuantization(
                        scalar=models.ScalarQuantizationConfig(
                            type=models.ScalarType.INT8, quantile=0.99, always_ram=True
                        )
                    )
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(index=models.SparseIndexParams(on_disk=True))
            }
        )

        await self.client.create_payload_index(self.collection_name, "industry", models.PayloadSchemaType.KEYWORD)
        await self.client.create_payload_index(self.collection_name, "substrate", models.PayloadSchemaType.KEYWORD)
        await self.client.create_payload_index(self.collection_name, "source", models.PayloadSchemaType.KEYWORD)

    def format_size(self, size_bytes):
        if size_bytes == 0: return "0 B"
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        return "%s %s" % (round(size_bytes / math.pow(1024, i), 2), ("B", "KB", "MB", "GB", "TB")[i])

    @property
    def sparse_embeddings(self):
        if self.lightweight:
            return None
        if self._sparse_embeddings_model is None:
            try:
                logger.info("Loading Sparse Text Embedding model (SPLADE)...")
                # Използваме по-лек модел за среди с малко RAM
                self._sparse_embeddings_model = SparseTextEmbedding(model_name="prithvida/SPLADE_PP_en_v1")
                logger.info("SPLADE model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load SPLADE model: {e}")
                return None
        return self._sparse_embeddings_model

    async def add_to_collection(self, text, source_name, metadata_extra=None):
        """Ченква текста и го добавя към векторната база с автоматични логове и прогрес."""
        if not self.enabled or self.client is None:
            logger.warning("RAG is disabled or client is None. Skipping indexing.")
            return
        logger.info(f"Indexing start: {source_name} ({len(text)} chars)")

        try:
            # Версиониране: Проверяваме дали файлът вече съществува и увеличаваме версията
            version = 1
            try:
                scroll_res, _ = await self.client.scroll(
                    self.collection_name,
                    scroll_filter=models.Filter(must=[models.FieldCondition(key="source", match=models.MatchValue(value=source_name))]),
                    limit=1,
                    with_payload=["version"]
                )
                if scroll_res:
                    latest_version = max([p.payload.get("version", 1) for p in scroll_res])
                    version = latest_version + 1
                    logger.info(f"Versioning: New version {version} for {source_name}")
            except Exception as e:
                logger.warning(f"Versioning check failed: {e}")

            # Оптимизирано цепене: Използваме Recursive splitter по подразбиране за скорост,
            # освен ако документът не е малък и не се изисква семантична прецизност.
            if len(text) > 20000 or self.lightweight:
                chunks = self.recursive_splitter.split_text(text)
            else:
                try:
                    chunks = self.semantic_splitter.split_text(text)
                except Exception as e:
                    logger.warning(f"Semantic splitter failed, falling back to recursive: {e}")
                    chunks = self.recursive_splitter.split_text(text)

            points = []
            file_path = metadata_extra.get('path') if metadata_extra else None
            file_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0

            if chunks:
                logger.info(f"Document {source_name} split into {len(chunks)} chunks.")
                if self.embed_type == "ollama":
                    # Parallel processing for Ollama embeddings
                    dense_embeddings = await self._parallel_embed_documents(chunks)
                else:
                    # Използваме executor за локални embeddings за избягване на лаг
                    loop = asyncio.get_running_loop()
                    dense_embeddings = await loop.run_in_executor(None, lambda: self.hf_embeddings.embed_documents(chunks))

                logger.info(f"Dense embeddings generated for {source_name}.")

                loop = asyncio.get_running_loop()
                if self.sparse_embeddings:
                    sparse_embeddings = await loop.run_in_executor(None, lambda: list(self.sparse_embeddings.embed(chunks)))
                    logger.info(f"Sparse embeddings generated for {source_name}.")
                else:
                    sparse_embeddings = [None] * len(chunks)
                    logger.warning("Skipping sparse embeddings due to model load failure.")

                # GraphRAG: Extract entities from the whole text once per document to update KG
                # (In production, we might do it per chunk for more precision)
                if os.environ.get("OLLAMA_URL"):
                    try:
                        await self.kg.extract_entities_and_relations(
                            text,
                            os.environ.get("OLLAMA_URL"),
                            os.environ.get("OLLAMA_MODEL", "llama3.1")
                        )
                    except Exception as e:
                        logger.warning(f"Graph extraction skipped for {source_name}: {e}")

                for i, (chunk, dense_emb, sparse_emb) in enumerate(zip(chunks, dense_embeddings, sparse_embeddings)):
                    # Link chunk to existing entities in KG (Graph Indexing)
                    found_entities = self.kg.search_entities_in_text(chunk)
                    meta = {
                        "source": source_name, "size": file_size,
                        "version": version,
                        "substrate": metadata_extra.get('substrate', 'unknown') if metadata_extra else 'unknown',
                        "industry": metadata_extra.get('industry', 'general') if metadata_extra else 'general',
                        "document": chunk,
                        "entities": found_entities, # Cross-reference KG
                        "timestamp": time.time()
                    }
                    if metadata_extra: meta.update(metadata_extra)
                    # Поправка: Използваме само името и индекса за консистентно ID (Idempotency)
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{source_name}_{i}"))

                    vector_data = {"dense": dense_emb}
                    if sparse_emb:
                        vector_data["sparse"] = models.SparseVector(indices=sparse_emb.indices, values=sparse_emb.values)

                    points.append(models.PointStruct(
                        id=point_id,
                        vector=vector_data,
                        payload=meta
                    ))

                if points:
                    for i in range(0, len(points), 100):
                        await self.client.upsert(self.collection_name, points[i:i + 100])
                    logger.info(f"Successfully upserted {len(points)} points to Qdrant for {source_name}")
        except Exception as e:
            logger.error(f"Error during indexing {source_name}: {e}")
            raise

    async def index_any(self, file_path, progress_callback=None):
        if not self.enabled: return
        path = Path(file_path)
        if not path.exists(): return
        if path.name.startswith("~$"): return

        if path.is_dir():
            for root, dirs, files in os.walk(path):
                for file in files: await self.index_any(os.path.join(root, file))
            return

        ext = path.suffix.lower()
        try:
            text = ""
            logger.info(f"Processing file: {path.name}")
            if progress_callback:
                await progress_callback({"type": "indexing_progress", "file": path.name, "status": "extracting"})

            if ext == ".pdf":
                reader = PdfReader(path)
                num_pages = len(reader.pages)
                logger.info(f"PDF {path.name} has {num_pages} pages.")
                for i, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as pe:
                        logger.warning(f"Failed to extract text from page {i} of {path.name}: {pe}")

                    if progress_callback and i % 5 == 0:
                        await progress_callback({
                            "type": "indexing_progress",
                            "file": path.name,
                            "progress": int(((i+1)/num_pages)*100),
                            "current": i+1,
                            "total": num_pages
                        })

                if text and len(text.strip()) > 10:
                    logger.info(f"Extracted {len(text)} chars from {path.name}")
                    await self.add_to_collection(text, path.name, {"path": str(path), "type": "pdf"})
                else:
                    logger.warning(f"No usable text extracted from PDF: {path.name}")
            elif ext == ".docx":
                text = "\n".join([p.text for p in Document(path).paragraphs])
                if text.strip():
                    await self.add_to_collection(text, path.name, {"path": str(path), "type": "docx"})
            elif ext in [".xlsx", ".xls", ".csv"]:
                try:
                    df = pd.read_excel(path) if ext != ".csv" else pd.read_csv(path)
                    text = df.to_string()
                    if text.strip():
                        await self.add_to_collection(text, path.name, {"path": str(path), "type": "table"})
                except Exception as ee:
                    logger.error(f"Excel/CSV read error {path.name}: {ee}")
            elif ext == ".json":
                with open(path, 'r', encoding='utf-8') as f: text = json.dumps(json.load(f), ensure_ascii=False)
                await self.add_to_collection(text, path.name, {"path": str(path), "type": "json"})
            elif ext == ".md":
                with open(path, 'r', encoding='utf-8') as f: text = f.read()
                await self.add_to_collection(text, path.name, {"path": str(path), "type": "markdown"})
            elif ext == ".html":
                with open(path, 'r', encoding='utf-8') as f: content = f.read()
                parser = etree.HTMLParser()
                tree = etree.fromstring(content, parser)
                if tree is not None:
                    for s in tree.xpath("//script | //style"): s.getparent().remove(s)
                    text = etree.tostring(tree, encoding='unicode', method='text')
                    text = "\n".join([l.strip() for l in text.splitlines() if l.strip()])
                    await self.add_to_collection(text, path.name, {"path": str(path), "type": "html"})
            elif ext == ".xml":
                with open(path, 'r', encoding='utf-8') as f: content = f.read()
                tree = etree.fromstring(content.encode('utf-8'))
                text = etree.tostring(tree, encoding='unicode', method='text')
                text = "\n".join([l.strip() for l in text.splitlines() if l.strip()])
                await self.add_to_collection(text, path.name, {"path": str(path), "type": "xml"})
            elif ext == ".tmx":
                tree = etree.parse(str(path))
                all_text = []
                for tu in tree.iter("tu"):
                    for tuv in tu.iter("tuv"):
                        lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang") or tuv.get("lang")
                        seg = tuv.find("seg")
                        if seg is not None and seg.text: all_text.append(f"[{lang}] {seg.text.strip()}")
                if all_text: await self.add_to_collection("\n".join(all_text), path.name, {"path": str(path), "type": "tmx"})
            elif ext in [".udb", ".mdb", ".accdb"]:
                # Поддръжка за индустриални бази данни (User/Microsoft Database)
                # В тази версия ги четем като двоични структури или текстови екстракти
                with open(path, 'rb') as f:
                    content = f.read(10000) # Прочитаме заглавната част
                    text = f"Industrial Database File: {path.name}\nSize: {len(content)} bytes\nMetadata extract: {content.hex()[:500]}"
                await self.add_to_collection(text, path.name, {"path": str(path), "type": "database"})
            elif ext == ".zip":
                extract_path = path.parent / f"tmp_zip_{int(time.time())}"
                try:
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    await self.index_any(str(extract_path))
                finally:
                    if extract_path.exists(): shutil.rmtree(extract_path)
        except Exception as e:
            logger.error(f"Index Error {path.name}: {e}")

    async def query(self, text, n_results=None, filters=None):
        if not self.enabled or self.client is None:
            logger.warning("RAG is disabled or client is None. Returning empty results.")
            return "", []

        try:
            if n_results is None:
                n_results = int(os.environ.get("RAG_TOP_K", "5" if self.lightweight else "10"))

            # 0. GraphRAG: Discover entities in query and find related context
            graph_context = ""
            query_entities = self.kg.search_entities_in_text(text)

            if query_entities:
                logger.info(f"GraphRAG: Засечени ентитети в заявката: {query_entities}")
                all_related = []
                for ent in query_entities:
                    related = self.kg.get_related_entities(ent, depth=2)
                    all_related.extend(related)

                if all_related:
                    graph_context = "\n--- ГРАФ НА ЗНАНИЕТО (Свързан контекст) ---\n"
                    graph_context += f"Ентитети свързани с вашия въпрос: {', '.join(list(set(all_related))[:10])}\n"

                    # Добавяме логическо разсъждение ако открием директен проблем
                    for ent in query_entities:
                        reasoning = self.kg.find_reasoning_path(ent)
                        if isinstance(reasoning, list):
                            for step in reasoning:
                                graph_context += f"Логическа връзка: {step['source']} {step['relation']} {ent}. {step['condition']}\n"

            if self.embed_type == "ollama":
                dense_vector = await self.hf_embeddings.embed_query(text)
            else:
                dense_vector = self.hf_embeddings.embed_query(text)

            loop = asyncio.get_running_loop()
            sparse_vector = None
            if self.sparse_embeddings:
                sparse_vector = (await loop.run_in_executor(None, lambda: list(self.sparse_embeddings.embed([text]))))[0]

            qdrant_filter = None
            if filters:
                must = [models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in filters.items()]
                qdrant_filter = models.Filter(must=must)

            # Hybrid Search (RRF)
            prefetch = [models.Prefetch(query=dense_vector, using="dense", filter=qdrant_filter, limit=n_results)]

            if sparse_vector:
                prefetch.append(models.Prefetch(
                    query=models.SparseVector(indices=sparse_vector.indices, values=sparse_vector.values),
                    using="sparse",
                    filter=qdrant_filter,
                    limit=n_results
                ))

            query_res = await self.client.query_points(
                self.collection_name,
                prefetch=prefetch,
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=n_results,
                with_payload=True
            )

            candidates = [res.payload.get("document", "") for res in query_res.points]
            candidate_metas = [res.payload for res in query_res.points]

            if not candidates: return "", []

            # Rerank
            if self.reranker:
                rerank_scores = self.reranker.predict([[text, cand] for cand in candidates])
                top_indices = np.argsort(rerank_scores)[::-1][:3]
                final_docs = [candidates[i] for i in top_indices]
                final_sources = [candidate_metas[i]['source'] for i in top_indices]
            else:
                final_docs = candidates[:3]
                final_sources = [m['source'] for m in candidate_metas[:3]]

            context = graph_context + "\n" + "\n".join([f"--- Doc ---\n{d}" for d in final_docs])
            return context[:4000], list(set(final_sources))
        except Exception as e:
            logger.error(f"Error during query: {e}")
            return "", []

    async def _parallel_embed_documents(self, chunks, batch_size=10):
        """Parallel embedding processing for better performance."""
        import asyncio
        
        async def embed_batch(batch):
            if self.embed_type == "ollama":
                return await self.hf_embeddings.embed_documents(batch)
            else:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, lambda: self.hf_embeddings.embed_documents(batch))
        
        # Split chunks into batches
        batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
        
        # Process batches in parallel
        tasks = [embed_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        embeddings = []
        for result in results:
            embeddings.extend(result)
        
        return embeddings

    async def get_stats(self):
        """Връща бърза статистика за колекцията. Оптимизирано за висока скорост."""
        if not self.enabled or self.client is None:
            logger.warning("get_stats called but RAG is not enabled or client is None")
            return {"total_size": "0 B", "total_chunks": 0, "total_files": 0}

        try:
            # 1. Общ брой точки чрез count() - най-точния метод
            count_res = await self.client.count(self.collection_name, exact=True)
            points_count = count_res.count
            logger.debug(f"RAG Stats: Points count = {points_count}")

            # 2. Извличане на метаданни за уникални файлове чрез scroll
            # За локален Qdrant това е най-надеждния начин
            unique_files = {}
            offset = None

            # Обхождаме до 5000 записа за статистиката (Enterprise мащаб)
            for _ in range(25):
                scroll_res = await self.client.scroll(
                    self.collection_name,
                    limit=200,
                    offset=offset,
                    with_payload=["source", "size"]
                )
                results = scroll_res[0]
                offset = scroll_res[1]

                for res in results:
                    source = res.payload.get('source')
                    if source:
                        unique_files[source] = max(unique_files.get(source, 0), res.payload.get('size', 0))
                if not offset: break

            stats = {
                "total_size": self.format_size(sum(unique_files.values())),
                "total_chunks": points_count,
                "total_files": len(unique_files)
            }
            logger.info(f"RAG Stats generated: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Stats Error in RAG System: {e}")
            return {"total_size": "0 B", "total_chunks": 0, "total_files": 0}
