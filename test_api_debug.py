#!/usr/bin/env python3
"""
Debug script to test the core agent directly
"""
import logging
import sys
import os

# Add the TARS directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'TARS'))

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_core_agent():
    """Test the core agent directly"""
    try:
        from graphs.core_agent import run_core_agent
        
        print("=== TESTING CORE AGENT ===")
        print("Testing with simple message...")
        
        # Test with a simple message
        user_id = "test_user_123"
        user_message = "Hello, how are you?"
        
        print(f"Input - user_id: {user_id}, message: {user_message}")
        
        # Get the generator
        response_generator = run_core_agent(user_id=user_id, user_message=user_message)
        
        # Collect responses
        response_parts = []
        for part in response_generator:
            print(f"Received part: '{part}'")
            response_parts.append(part)
        
        final_response = ''.join(response_parts)
        print(f"Final response: '{final_response}'")
        
        if final_response.strip():
            print("✅ SUCCESS: Core agent returned a response")
        else:
            print("❌ FAILURE: Core agent returned empty response")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_model_initialization():
    """Test model initialization"""
    try:
        from graphs.utils.nodes import _get_model
        from config.config import graph_config
        
        print("=== TESTING MODEL INITIALIZATION ===")
        print(f"Graph config agent_model_name: {graph_config.agent_model_name}")
        
        model = _get_model(graph_config.agent_model_name)
        print("✅ SUCCESS: Model initialized successfully")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting debug tests...")
    
    # Test model initialization first
    test_model_initialization()
    print("\n" + "="*50 + "\n")
    
    # Test core agent
    test_core_agent() 