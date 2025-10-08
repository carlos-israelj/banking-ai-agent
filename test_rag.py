#!/usr/bin/env python3
"""Script para probar el sistema RAG con embeddings."""

import sys
import os

# Asegurarse de que puede importar desde src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.knowledge import KnowledgeBase

def test_rag_system():
    print("="*70)
    print("🧪 PRUEBA DEL SISTEMA RAG CON EMBEDDINGS")
    print("="*70)
    
    try:
        # Inicializar knowledge base con embeddings
        print("\n🔄 Inicializando KnowledgeBase...")
        kb = KnowledgeBase(use_embeddings=True)
        
        # Mostrar estadísticas
        print("\n📊 Obteniendo estadísticas...")
        stats = kb.get_statistics()
        
        print(f"\n✅ Estadísticas:")
        print(f"  • Total FAQs: {stats['total_faqs']}")
        print(f"  • Categorías: {stats['categories_count']}")
        print(f"  • RAG habilitado: {stats['rag_enabled']}")
        
        if stats['rag_enabled']:
            print(f"  • Modelo: {stats.get('embedding_model', 'N/A')}")
            print(f"  • Dimensiones: {stats.get('embedding_dimensions', 'N/A')}")
            print(f"  • Vector DB: {stats.get('vector_db', 'N/A')}")
        
        # Queries de prueba
        test_queries = [
            "¿A qué hora abren?",
            "Necesito una cuenta para ahorrar dinero",
            "¿Cuánto me cobran si transfiero plata?",
        ]
        
        print("\n" + "="*70)
        print("🔍 PRUEBAS DE BÚSQUEDA")
        print("="*70)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'─'*70}")
            print(f"Prueba {i}/{len(test_queries)}")
            print(f"❓ Query: \"{query}\"")
            print()
            
            results = kb.search(query, top_k=1)
            
            if results:
                print("✅ Resultado encontrado:")
                print(results[:200] + "..." if len(results) > 200 else results)
            else:
                print("❌ No se encontraron resultados")
        
        print("\n" + "="*70)
        print("✅ PRUEBAS COMPLETADAS")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_system()
