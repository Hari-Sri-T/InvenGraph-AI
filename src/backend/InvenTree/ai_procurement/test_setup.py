#!/usr/bin/env python
"""Quick test script to verify Agentic AI Procurement setup."""

import sys


def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")

    try:
        import langgraph
        print("  ✅ langgraph")
    except ImportError as e:
        print(f"  ❌ langgraph: {e}")
        return False

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        print("  ✅ langgraph-checkpoint-postgres")
    except ImportError as e:
        print(f"  ❌ langgraph-checkpoint-postgres: {e}")
        return False

    try:
        import prophet
        print("  ✅ prophet")
    except ImportError as e:
        print(f"  ❌ prophet: {e}")
        return False

    try:
        import xgboost
        print("  ✅ xgboost")
    except ImportError as e:
        print(f"  ❌ xgboost: {e}")
        return False

    try:
        import pandas
        print("  ✅ pandas")
    except ImportError as e:
        print(f"  ❌ pandas: {e}")
        return False

    try:
        import numpy
        print("  ✅ numpy")
    except ImportError as e:
        print(f"  ❌ numpy: {e}")
        return False

    try:
        import requests
        print("  ✅ requests")
    except ImportError as e:
        print(f"  ❌ requests: {e}")
        return False

    return True


def test_django_setup():
    """Test Django setup."""
    print("\n🔍 Testing Django setup...")

    try:
        import django

        django.setup()
        print("  ✅ Django setup")
    except Exception as e:
        print(f"  ❌ Django setup failed: {e}")
        return False

    try:
        from ai_procurement.models import (
            ApprovalRequest,
            DemandForecast,
            PipelineExecution,
            ProcurementDecisionLog,
            ProcurementOutcome,
            ProphetModelCache,
            ReorderPointHistory,
            SupplierEvaluation,
            SupplierReliabilityScore,
            FewShotMemory,
        )

        print("  ✅ All models importable")
    except Exception as e:
        print(f"  ❌ Models import failed: {e}")
        return False

    try:
        from ai_procurement.agents.demand_agent import DemandAgent
        from ai_procurement.agents.supplier_agent import SupplierAgent
        from ai_procurement.agents.decision_agent import DecisionAgent
        from ai_procurement.agents.execution_agent import ExecutionAgent

        print("  ✅ All agents importable")
    except Exception as e:
        print(f"  ❌ Agents import failed: {e}")
        return False

    try:
        from ai_procurement.state_manager import StateManager
        from ai_procurement.graph import compile_procurement_graph

        print("  ✅ LangGraph components importable")
    except Exception as e:
        print(f"  ❌ LangGraph components import failed: {e}")
        return False

    try:
        from ai_procurement.approval_gate import ApprovalGate
        from ai_procurement.notifications import NotificationService
        from ai_procurement.learning.learning_layer import LearningLayer

        print("  ✅ Supporting components importable")
    except Exception as e:
        print(f"  ❌ Supporting components import failed: {e}")
        return False

    return True


def test_ollama():
    """Test Ollama connection."""
    print("\n🔍 Testing Ollama connection...")

    try:
        import requests

        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("  ✅ Ollama is running")

            # Check for llama3 model
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            if any('llama3' in model for model in models):
                print("  ✅ llama3 model is available")
            else:
                print("  ⚠️  llama3 model not found")
                print("     Run: ollama pull llama3")
                return False
        else:
            print("  ❌ Ollama returned unexpected status")
            return False
    except requests.exceptions.ConnectionError:
        print("  ❌ Cannot connect to Ollama")
        print("     Make sure Ollama is running: ollama serve")
        print("     Or install from: https://ollama.ai/download")
        return False
    except Exception as e:
        print(f"  ❌ Ollama test failed: {e}")
        return False

    return True


def test_database():
    """Test database connectivity."""
    print("\n🔍 Testing database...")

    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            print("  ✅ Database connection works")
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

    try:
        from ai_procurement.models import PipelineExecution

        count = PipelineExecution.objects.count()
        print(f"  ✅ Can query models (found {count} pipeline executions)")
    except Exception as e:
        print(f"  ❌ Model query failed: {e}")
        print("     Run migrations: python manage.py migrate ai_procurement")
        return False

    return True


def main():
    """Run all tests."""
    print("🤖 Agentic AI Procurement System - Setup Verification\n")

    results = []

    # Test imports
    results.append(('Imports', test_imports()))

    # Test Django setup
    results.append(('Django Setup', test_django_setup()))

    # Test Ollama
    results.append(('Ollama', test_ollama()))

    # Test database
    results.append(('Database', test_database()))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Start Django: python manage.py runserver")
        print("2. Open InvenTree: http://localhost:8000")
        print("3. Navigate to a Part and test the AI Procurement panel")
        print("\n📖 See TESTING.md for detailed testing scenarios")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\n📖 See TESTING.md for troubleshooting help")
        return 1


if __name__ == '__main__':
    sys.exit(main())
