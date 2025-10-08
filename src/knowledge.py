"""
Sistema de gestión de conocimiento (RAG) para FAQs.
"""
import json
import os
from typing import List, Dict
from config.settings import FAQS_FILE, TOP_K_RESULTS

class KnowledgeBase:
    """
    Gestiona la base de conocimiento de FAQs del banco.
    En producción, usaría embeddings y búsqueda vectorial.
    """
    
    def __init__(self):
        self.faqs = self._load_faqs()
    
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
    
    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> str:
        """
        Busca FAQs relevantes para el query del usuario.
        
        En producción, esto usaría:
        1. Embeddings (sentence-transformers o OpenAI embeddings)
        2. Vector database (ChromaDB, Pinecone, Weaviate)
        3. Búsqueda por similitud coseno
        
        Flujo en producción:
        ```python
        from sentence_transformers import SentenceTransformer
        import chromadb
        
        # Al inicializar
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        client = chromadb.Client()
        collection = client.create_collection("faqs")
        
        # Indexar FAQs
        for faq in faqs:
            embedding = model.encode(faq['question'] + ' ' + faq['answer'])
            collection.add(
                embeddings=[embedding.tolist()],
                documents=[faq['answer']],
                metadatas=[{"question": faq['question'], "category": faq['category']}],
                ids=[faq['id']]
            )
        
        # Buscar
        query_embedding = model.encode(query)
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        ```
        
        Para esta demo, usamos keyword matching simple.
        """
        query_lower = query.lower()
        
        # Calcular relevancia por keywords
        scored_faqs = []
        for faq in self.faqs:
            score = 0
            
            # Buscar en keywords
            for keyword in faq.get('keywords', []):
                if keyword.lower() in query_lower:
                    score += 2  # Keywords tienen más peso
            
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
        
        # Formatear resultados
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
        En producción, también actualizaría el índice vectorial.
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
            
            # Guardar en archivo
            with open(FAQS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"faqs": self.faqs}, f, ensure_ascii=False, indent=2)
            
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
        
        return {
            "total_faqs": len(self.faqs),
            "categories": categories,
            "categories_count": len(categories)
        }


# Herramienta para búsqueda en la base de conocimiento
def search_knowledge_base(query: str) -> Dict:
    """
    Tool: search_knowledge_base
    
    Propósito:
    Buscar información relevante en la base de conocimiento de FAQs.
    
    Entradas esperadas:
    - query (str): Pregunta o términos de búsqueda del usuario
    
    Salida esperada:
    {
        "success": bool,
        "results": str (texto formateado con las FAQs relevantes),
        "count": int (número de resultados encontrados)
    }
    
    Posibles errores:
    - NO_RESULTS: No se encontraron FAQs relevantes
    - SERVICE_ERROR: Error al buscar en la base de datos
    
    Manejo del agente:
    - Si NO_RESULTS: Disculparse y ofrecer contactar con un asesor
    - Si SERVICE_ERROR: Intentar reformular o sugerir contacto directo
    """
    try:
        kb = KnowledgeBase()
        results = kb.search(query)
        
        if not results:
            return {
                "success": False,
                "error": "NO_RESULTS",
                "message": "No encontré información sobre eso en mi base de conocimiento",
                "count": 0
            }
        
        return {
            "success": True,
            "results": results,
            "count": len(results.split('\n\n'))
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": "SERVICE_ERROR",
            "message": "Error al buscar en la base de conocimiento"
        }