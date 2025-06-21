#!/usr/bin/env python3
"""
Test script to demonstrate the API feedback functionality.

This script shows how to:
1. Send a chat request to get a response and run_id
2. Submit feedback for that response using the run_id
"""

import requests
import json
import time

# API base URL - adjust this to match your deployment
API_BASE_URL = "http://localhost:8000"

def test_chat_and_feedback():
    """Test the complete chat and feedback flow."""
    
    print("=== Testing API Chat and Feedback Flow ===\n")
    
    # Step 1: Send a chat request
    print("1. Sending chat request...")
    chat_data = {
        "message": "Hello! Can you help me with a simple question?",
        "user_name": "test_user_123"
    }
    
    try:
        chat_response = requests.post(
            f"{API_BASE_URL}/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        )
        chat_response.raise_for_status()
        
        chat_result = chat_response.json()
        print(f"✅ Chat response received:")
        print(f"   Response: {chat_result['response'][:100]}...")
        print(f"   Run ID: {chat_result['run_id']}")
        
        # Step 2: Submit positive feedback
        print("\n2. Submitting positive feedback...")
        feedback_data = {
            "user_name": "test_user_123",
            "satisfaction_score": 0.9,
            "comment": "Great response, very helpful!"
        }
        
        feedback_response = requests.post(
            f"{API_BASE_URL}/feedback",
            json=feedback_data,
            headers={"Content-Type": "application/json"}
        )
        feedback_response.raise_for_status()
        
        feedback_result = feedback_response.json()
        print(f"✅ Feedback submitted successfully:")
        print(f"   Status: {feedback_result['status']}")
        print(f"   Message: {feedback_result['message']}")
        print(f"   Feedback ID: {feedback_result['feedback_id']}")
        
        # Step 3: Submit negative feedback (for demonstration)
        print("\n3. Submitting negative feedback...")
        negative_feedback_data = {
            "user_name": "test_user_123",
            "satisfaction_score": 0.2,
            "comment": "Response was not very helpful"
        }
        
        negative_feedback_response = requests.post(
            f"{API_BASE_URL}/feedback",
            json=negative_feedback_data,
            headers={"Content-Type": "application/json"}
        )
        negative_feedback_response.raise_for_status()
        
        negative_feedback_result = negative_feedback_response.json()
        print(f"✅ Negative feedback submitted successfully:")
        print(f"   Status: {negative_feedback_result['status']}")
        print(f"   Message: {negative_feedback_result['message']}")
        
        print("\n=== Test completed successfully! ===")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status code: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_error_cases():
    """Test various error cases for the feedback endpoint."""
    
    print("\n=== Testing Error Cases ===\n")
    
    # Test 1: Invalid satisfaction score
    print("1. Testing invalid satisfaction score...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/feedback",
            json={
                "user_name": "test_user_123",
                "satisfaction_score": 1.5,  # Invalid: > 1.0
                "comment": "This should fail"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print("✅ Correctly rejected invalid satisfaction score")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Feedback without prior chat
    print("\n2. Testing feedback without prior chat...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/feedback",
            json={
                "user_name": "new_user_without_chat",
                "satisfaction_score": 0.8,
                "comment": "This should fail - no prior chat"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 404:
            print("✅ Correctly rejected feedback without prior chat")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    print("API Feedback Test Script")
    print("Make sure your API server is running on localhost:8000")
    print("=" * 50)
    
    # Test the main flow
    test_chat_and_feedback()
    
    # Test error cases
    test_error_cases()
    
    print("\n" + "=" * 50)
    print("Test script completed!") 