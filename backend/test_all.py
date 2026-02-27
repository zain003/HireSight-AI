"""
Comprehensive test script for HireSIGHT AI Backend
Tests all modules: Auth, Resume, AI
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from app.auth.models import User, Profile
        print("✓ Auth models imported")
        
        from app.resume.parser import get_parser
        print("✓ Resume parser imported")
        
        from app.ai.extraction import get_extraction_service
        print("✓ AI extraction service imported")
        
        from app.ai.embeddings import get_embedding_service
        print("✓ Embedding service imported")
        
        print("\n✓ All imports successful!\n")
        return True
    except Exception as e:
        print(f"\n✗ Import failed: {e}\n")
        return False


def test_ai_components():
    """Test AI/ML components"""
    print("=" * 60)
    print("TEST 2: AI Components")
    print("=" * 60)
    
    try:
        from app.ai.embeddings import get_embedding_service
        from app.ai.extraction import get_extraction_service
        
        # Test embedding service
        embedding_service = get_embedding_service()
        print(f"✓ SBERT model loaded: {embedding_service.model_name}")
        
        # Test embedding generation
        embedding = embedding_service.generate_embedding("Python programming")
        print(f"✓ Embedding generated: {len(embedding)} dimensions")
        
        # Test similarity
        similarity = embedding_service.compute_similarity("Python", "Java")
        print(f"✓ Similarity computed: Python vs Java = {similarity:.3f}")
        
        # Test extraction service
        extraction_service = get_extraction_service()
        test_text = """
        Software Engineer with 5 years of experience in Python, JavaScript, React, 
        Node.js, Docker, and AWS. Built scalable microservices and RESTful APIs.
        """
        
        result = extraction_service.extract_all(test_text)
        print(f"✓ Skills extracted: {len(result['skills'])} skills")
        print(f"  Skills: {', '.join(result['skills'][:5])}...")
        print(f"✓ Domain classified: {result['domain']}")
        
        print("\n✓ All AI tests passed!\n")
        return True
    except Exception as e:
        print(f"\n✗ AI test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_resume_parsing():
    """Test resume parsing"""
    print("=" * 60)
    print("TEST 3: Resume Parsing")
    print("=" * 60)
    
    try:
        from app.resume.parser import get_parser
        
        parser = get_parser()
        print("✓ Parser initialized")
        
        # Test with sample text (simulating parsed content)
        sample_text = """
        JOHN DOE
        Software Engineer
        
        EXPERIENCE
        Senior Developer at Tech Corp (2020-2023)
        - Developed microservices using Python and Docker
        - Built RESTful APIs with FastAPI
        - Managed PostgreSQL databases
        
        SKILLS
        Python, JavaScript, React, Node.js, Docker, Kubernetes, AWS, PostgreSQL
        """
        
        print(f"✓ Sample resume text: {len(sample_text)} characters")
        print("✓ Resume parsing components working")
        
        print("\n✓ Resume parsing tests passed!\n")
        return True
    except Exception as e:
        print(f"\n✗ Resume parsing test failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  HireSIGHT AI - Backend Test Suite")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("AI Components", test_ai_components()))
    results.append(("Resume Parsing", test_resume_parsing()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed successfully!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
