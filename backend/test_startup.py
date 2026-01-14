"""
Test if the server can start
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("Testing imports...")

try:
    from workflow.orchestrator import Orchestrator
    print("✓ Orchestrator imported")
except Exception as e:
    print(f"✗ Orchestrator import failed: {e}")

try:
    from llm.llm_client import create_llm_client, LLMProvider
    print("✓ LLM client imported")
except Exception as e:
    print(f"✗ LLM client import failed: {e}")

try:
    from storage.history import HistoryStorage
    print("✓ HistoryStorage imported")
except Exception as e:
    print(f"✗ HistoryStorage import failed: {e}")

try:
    from utils.file_parser import parse_file_content
    print("✓ file_parser imported")
except Exception as e:
    print(f"✗ file_parser import failed: {e}")

print("\nTesting LLM client creation...")
os.environ['LLM_PROVIDER'] = 'google'
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDgmAVIF6bgdbLUAMvf1GGafBfGYmqKI5U'

try:
    client = create_llm_client(LLMProvider.GOOGLE)
    print(f"✓ Google client created: {type(client)}")
except Exception as e:
    print(f"✗ Google client creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\nAll tests complete!")
