#!/usr/bin/env python3
"""
Script para probar el sistema RAG con embeddings.
"""

from src.knowledge import KnowledgeBase

def test_rag_system():
    """Prueba el sistema RAG con diferentes queries"""
    
    print("="*70)
    print("🧪 PRUEBA DEL SISTEMA RAG CON EMBEDDINGS")
    print("="*70)
    
    # Inicializar knowledge base
    kb = KnowledgeBase(use_embeddings=True)
    
    # Mostrar estadísticas
    stats = kb.get_statistics()
    print(f"\n📊 Estadísticas:")
    print(f"  • Total FAQs: {stats['total_faqs']}")
    print(f"  • Categorías: {stats['categories_count']}")
    print(f"  • RAG habilitado: {stats['rag_enabled']}")
    if stats['rag_enabled']:
        print(f"  • Modelo: {stats['embedding_model']}")
        print(f"  • Dimensiones: {stats['embedding_dimensions']}")
        print(f"  • Vector DB: {stats['vector_db']}")
    
    # Queries de prueba
    test_queries = [
        "¿A qué hora abren?",
        "Necesito una cuenta para ahorrar dinero",
        "¿Cuánto me cobran si transfiero plata?",
        "Perdí mi tarjeta de crédito",
        "Quiero invertir mi dinero",
        "¿Tienen seguros para el carro?",
    ]
    
    print("\n" + "="*70)
    print("🔍 PRUEBAS DE BÚSQUEDA SEMÁNTICA")
    print("="*70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─'*70}")
        print(f"Prueba {i}/{len(test_queries)}")
        print(f"{'─'*70}")
        print(f"❓ Query: \"{query}\"")
        print()
        
        results = kb.search(query, top_k=2)
        
        if results:
            print("✅ Resultados encontrados:")
            print()
            print(results)
        else:
            print("❌ No se encontraron resultados")
    
    print("\n" + "="*70)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*70)
    
    # Comparación con keywords (si disponible)
    if kb.use_embeddings:
        print("\n" + "="*70)
        print("📊 COMPARACIÓN: Embeddings vs Keywords")
        print("="*70)
        
        comparison_query = "me robaron la tarjeta"
        
        print(f"\n🔍 Query: \"{comparison_query}\"")
        
        print("\n1️⃣  Con EMBEDDINGS (semántico):")
        results_embeddings = kb._search_with_embeddings(comparison_query, 1)
        print(results_embeddings if results_embeddings else "No encontrado")
        
        print("\n2️⃣  Con KEYWORDS (literal):")
        results_keywords = kb._search_with_keywords(comparison_query, 1)
        print(results_keywords if results_keywords else "No encontrado")
        
        print("\n💡 Los embeddings entienden 'me robaron' ≈ 'perdí/robaron/extraviada'")
        print("   mientras que keywords solo busca coincidencias exactas.")

if __name__ == "__main__":
    test_rag_system()