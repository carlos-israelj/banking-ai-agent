"""
Sistema de gestión de conocimiento con RAG REAL.
Usa embeddings y búsqueda vectorial semántica.
"""
import json
import os
from typing import List, Dict
from config.settings import FAQS_FILE, TOP_K_RESULTS

# Importar bibliotecas para RAG
try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  Bibliotecas de RAG no disponibles. Usando búsqueda por keywords.")

class KnowledgeBase:
    """
    Gestiona la base de conocimiento con RAG real.
    
    PRODUCCIÓN: Usa embeddings + vector database para búsqueda semántica.
    FALLBACK: Si no hay bibliotecas, usa búsqueda por keywords.
    """
    
    def __init__(self, use_embeddings: bool = True):
        self.faqs = self._load_faqs()
        self.use_embeddings = use_embeddings and RAG_AVAILABLE
        
        if self.use_embeddings:
            print("🔄 Inicializando sistema RAG con embeddings...")
            self._initialize_rag_system()
            print("✅ Sistema RAG inicializado correctamente")
        else:
            print("⚠️  Usando sistema de búsqueda por keywords (sin embeddings)")
    
    def _load_faqs(self) -> List[Dict]:
        """Carga las FAQs desde el archivo JSON"""
        try:
            if os.path.exists(FAQS_FILE):
                with open(FAQS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('faqs', [])
            else:
                print(f"⚠️  Advertencia: No se encontró {FAQS_FILE}")
                return []
        except Exception as e:
            print(f"❌ Error al cargar FAQs: {e}")
            return []
    
    def _initialize_rag_system(self):
        """
        Inicializa el sistema RAG completo:
        1. Carga modelo de embeddings
        2. Crea/carga vector database
        3. Indexa FAQs si es necesario
        """
        # 1. Cargar modelo de embeddings multilingüe
        print("  📥 Cargando modelo de embeddings...")
        self.embedding_model = SentenceTransformer(
            'paraphrase-multilingual-mpnet-base-v2'
        )
        # Dimensiones: 768
        # Soporta: 50+ idiomas incluyendo español
        
        # 2. Inicializar ChromaDB (vector database)
        print("  💾 Inicializando ChromaDB...")
        self.chroma_client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True
        ))
        
        # 3. Crear colección (o cargarla si existe)
        try:
            self.collection = self.chroma_client.get_collection("banking_faqs")
            print("  ✅ Colección existente cargada")
        except:
            print("  🆕 Creando nueva colección...")
            self.collection = self.chroma_client.create_collection(
                name="banking_faqs",
                metadata={"description": "FAQs bancarias con embeddings"}
            )
            self._index_faqs()
    
    def _index_faqs(self):
        """
        Indexa todas las FAQs en la vector database.
        
        Proceso:
        1. Para cada FAQ, combina pregunta + respuesta
        2. Genera embedding usando sentence-transformers
        3. Almacena en ChromaDB con metadatos
        """
        print(f"  🔄 Indexando {len(self.faqs)} FAQs...")
        
        documents = []
        embeddings = []
        ids = []
        metadatas = []
        
        for faq in self.faqs:
            # Combinar pregunta y respuesta para mejor contexto
            text = f"{faq['question']} {faq['answer']}"
            
            # Generar embedding
            embedding = self.embedding_model.encode(text)
            
            documents.append(faq['answer'])
            embeddings.append(embedding.tolist())
            ids.append(faq['id'])
            metadatas.append({
                'question': faq['question'],
                'category': faq.get('category', 'general')
            })
        
        # Agregar todo a ChromaDB en batch
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"  ✅ {len(self.faqs)} FAQs indexadas correctamente")
    
    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> str:
        """
        Busca FAQs relevantes usando búsqueda semántica.
        
        PRODUCCIÓN (con embeddings):
        1. Convierte el query del usuario a embedding
        2. Busca en ChromaDB por similitud coseno
        3. Retorna los top-K más relevantes
        
        FALLBACK (sin embeddings):
        - Usa búsqueda por keywords
        
        Args:
            query: Pregunta del usuario
            top_k: Número de resultados a retornar
            
        Returns:
            String formateado con las FAQs más relevantes
        """
        if self.use_embeddings:
            return self._search_with_embeddings(query, top_k)
        else:
            return self._search_with_keywords(query, top_k)
    
    def _search_with_embeddings(self, query: str, top_k: int) -> str:
        """
        Búsqueda semántica usando embeddings y ChromaDB.
        
        Ventajas:
        - Entiende sinónimos y paráfrasis
        - No depende de keywords exactas
        - Búsqueda por significado, no por palabras
        """
        # 1. Generar embedding del query
        query_embedding = self.embedding_model.encode(query)
        
        # 2. Buscar en ChromaDB por similitud coseno
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # 3. Formatear resultados
        if not results['documents'] or not results['documents'][0]:
            return ""
        
        formatted_results = []
        for i, doc in enumerate(results['documents'][0]):
            question = results['metadatas'][0][i]['question']
            formatted_results.append(f"**{question}**\n{doc}")
        
        return "\n\n".join(formatted_results)
    
    def _search_with_keywords(self, query: str, top_k: int) -> str:
        """
        Búsqueda simple por keywords (fallback).
        Usado si no hay embeddings disponibles.
        """
        query_lower = query.lower()
        
        # Calcular relevancia por keywords
        scored_faqs = []
        for faq in self.faqs:
            score = 0
            
            # Buscar en keywords
            for keyword in faq.get('keywords', []):
                if keyword.lower() in query_lower:
                    score += 2
            
            # Buscar en pregunta
            if any(word in faq['question'].lower() for word in query_lower.split()):
                score += 1
            
            # Buscar en respuesta
            if any(word in faq['answer'].lower() for word in query_lower.split()):
                score += 0.5
            
            if score > 0:
                scored_faqs.append((score, faq))
        
        # Ordenar por relevancia
        scored_faqs.sort(reverse=True, key=lambda x: x[0])
        
        # Retornar top_k resultados
        if not scored_faqs:
            return ""
        
        results = []
        for _, faq in scored_faqs[:top_k]:
            results.append(f"**{faq['question']}**\n{faq['answer']}")
        
        return "\n\n".join(results)
    
    def get_faq_by_category(self, category: str) -> List[Dict]:
        """Obtiene todas las FAQs de una categoría"""
        return [faq for faq in self.faqs if faq.get('category') == category]
    
    def get_all_categories(self) -> List[str]:
        """Obtiene todas las categorías disponibles"""
        categories = set()
        for faq in self.faqs:
            if 'category' in faq:
                categories.add(faq['category'])
        return sorted(list(categories))
    
    def add_faq(self, question: str, answer: str, category: str, 
                keywords: List[str]) -> bool:
        """
        Agrega una nueva FAQ a la base de conocimiento.
        
        Si hay embeddings activos, también la indexa en ChromaDB.
        """
        try:
            new_faq = {
                "id": f"faq_{len(self.faqs) + 1:03d}",
                "category": category,
                "question": question,
                "answer": answer,
                "keywords": keywords
            }
            
            self.faqs.append(new_faq)
            
            # Guardar en archivo JSON
            with open(FAQS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"faqs": self.faqs}, f, ensure_ascii=False, indent=2)
            
            # Si hay embeddings, indexar la nueva FAQ
            if self.use_embeddings:
                text = f"{question} {answer}"
                embedding = self.embedding_model.encode(text)
                
                self.collection.add(
                    documents=[answer],
                    embeddings=[embedding.tolist()],
                    ids=[new_faq['id']],
                    metadatas=[{
                        'question': question,
                        'category': category
                    }]
                )
            
            return True
        except Exception as e:
            print(f"Error al agregar FAQ: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de la base de conocimiento"""
        categories = {}
        for faq in self.faqs:
            cat = faq.get('category', 'uncategorized')
            categories[cat] = categories.get(cat, 0) + 1
        
        stats = {
            "total_faqs": len(self.faqs),
            "categories": categories,
            "categories_count": len(categories),
            "rag_enabled": self.use_embeddings
        }
        
        if self.use_embeddings:
            stats["embedding_model"] = "paraphrase-multilingual-mpnet-base-v2"
            stats["embedding_dimensions"] = 768
            stats["vector_db"] = "ChromaDB"
        
        return stats


# Herramienta para búsqueda en la base de conocimiento
def search_knowledge_base(query: str) -> Dict:
    """
    Tool: search_knowledge_base
    
    Propósito:
    Buscar información relevante en la base de conocimiento usando RAG.
    
    Implementación:
    - Con embeddings: Búsqueda semántica por similitud coseno
    - Sin embeddings: Búsqueda por keywords (fallback)
    
    Entradas esperadas:
    - query (str): Pregunta o términos de búsqueda del usuario
    
    Salida esperada:
    {
        "success": bool,
        "results": str (texto formateado con las FAQs relevantes),
        "count": int (número de resultados encontrados),
        "method": str ("embeddings" o "keywords")
    }
    
    Posibles errores:
    - NO_RESULTS: No se encontraron FAQs relevantes
    - SERVICE_ERROR: Error al buscar en la base de datos
    """
    try:
        kb = KnowledgeBase()
        results = kb.search(query)
        
        if not results:
            return {
                "success": False,
                "error": "NO_RESULTS",
                "message": "No encontré información sobre eso en mi base de conocimiento",
                "count": 0,
                "method": "embeddings" if kb.use_embeddings else "keywords"
            }
        
        return {
            "success": True,
            "results": results,
            "count": len(results.split('\n\n')),
            "method": "embeddings" if kb.use_embeddings else "keywords"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": "SERVICE_ERROR",
            "message": "Error al buscar en la base de conocimiento",
            "details": str(e)
        }