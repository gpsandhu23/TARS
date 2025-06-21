# API Feedback System

This document describes the user feedback system implemented in the TARS API, similar to the feedback functionality in the Slack app.

## Overview

The API now supports user feedback collection through a dedicated endpoint that integrates with LangSmith for feedback tracking and analysis.

## Features

- **Feedback Collection**: Users can submit satisfaction scores and comments for API responses
- **LangSmith Integration**: All feedback is automatically logged to LangSmith for analysis
- **Run ID Tracking**: Each chat response includes a run ID that links feedback to specific conversations
- **Validation**: Input validation ensures feedback scores are within valid ranges
- **Error Handling**: Comprehensive error handling for various edge cases

## API Endpoints

### 1. Chat Endpoint (Enhanced)

**POST** `/chat`

Sends a message to the TARS agent and returns a response with a run ID for feedback tracking.

**Request Body:**
```json
{
  "message": "Your message here",
  "user_name": "user_identifier"
}
```

**Response:**
```json
{
  "response": "Agent response text",
  "run_id": "unique_run_identifier"
}
```

### 2. Feedback Endpoint (New)

**POST** `/feedback`

Submits user feedback for a previous chat response.

**Request Body:**
```json
{
  "user_name": "user_identifier",
  "satisfaction_score": 0.8,
  "comment": "Optional feedback comment"
}
```

**Parameters:**
- `user_name` (string, required): Must match the user_name from a previous chat request
- `satisfaction_score` (float, required): Score between 0.0 and 1.0
  - 0.0-0.3: Negative feedback
  - 0.4-0.6: Neutral feedback  
  - 0.7-1.0: Positive feedback
- `comment` (string, optional): Additional feedback text

**Response:**
```json
{
  "status": "success",
  "message": "Feedback submitted successfully",
  "feedback_id": "langsmith_feedback_id"
}
```

## Usage Flow

1. **Send Chat Request**: User sends a message via `/chat` endpoint
2. **Receive Response**: API returns response with run ID
3. **Submit Feedback**: User submits feedback via `/feedback` endpoint using the same user_name
4. **Feedback Logged**: Feedback is automatically logged to LangSmith

## Example Usage

### Python Example

```python
import requests

# Step 1: Send chat request
chat_response = requests.post("http://localhost:8000/chat", json={
    "message": "Hello, can you help me?",
    "user_name": "john_doe"
})

chat_data = chat_response.json()
print(f"Response: {chat_data['response']}")
print(f"Run ID: {chat_data['run_id']}")

# Step 2: Submit feedback
feedback_response = requests.post("http://localhost:8000/feedback", json={
    "user_name": "john_doe",
    "satisfaction_score": 0.9,
    "comment": "Very helpful response!"
})

feedback_data = feedback_response.json()
print(f"Feedback status: {feedback_data['status']}")
```

### cURL Example

```bash
# Send chat request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "user_name": "test_user"}'

# Submit feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"user_name": "test_user", "satisfaction_score": 0.8, "comment": "Good response!"}'
```

## Error Handling

### Common Error Responses

**400 Bad Request**: Invalid satisfaction score
```json
{
  "detail": "Satisfaction score must be between 0.0 and 1.0"
}
```

**404 Not Found**: No recent conversation for user
```json
{
  "detail": "No recent conversation found for this user. Please send a message first."
}
```

**500 Internal Server Error**: LangSmith integration failure
```json
{
  "detail": "Failed to submit feedback to LangSmith"
}
```

## Implementation Details

### Run ID Tracking

- Each chat request generates a unique run ID using LangSmith's `get_current_run_tree()`
- Run IDs are stored in memory (in production, use a proper database)
- Feedback is linked to specific conversations via run ID

### LangSmith Integration

- Feedback is automatically sent to LangSmith using the `create_feedback` method
- Feedback key is set to "user_satisfaction"
- Comments include user feedback text for context

### Validation

- Satisfaction scores must be between 0.0 and 1.0
- User must have a recent conversation before submitting feedback
- All inputs are validated using Pydantic models

## Testing

Use the provided test script to verify the feedback functionality:

```bash
python TARS/surfaces/API/test_feedback.py
```

The test script demonstrates:
- Complete chat and feedback flow
- Error case handling
- Input validation

## Production Considerations

1. **Database Storage**: Replace in-memory run ID storage with a proper database
2. **Authentication**: Add user authentication and authorization
3. **Rate Limiting**: Implement rate limiting for feedback submissions
4. **Monitoring**: Add metrics and monitoring for feedback collection
5. **Data Retention**: Implement data retention policies for feedback data

## Comparison with Slack App

The API feedback system mirrors the Slack app's feedback functionality:

| Feature | Slack App | API |
|---------|-----------|-----|
| Feedback Collection | Emoji reactions | Explicit scores |
| Run ID Tracking | ✅ | ✅ |
| LangSmith Integration | ✅ | ✅ |
| Real-time Updates | ✅ | ❌ (stateless) |
| User Identification | Slack user ID | user_name parameter |

The main difference is that the API uses explicit satisfaction scores (0.0-1.0) while the Slack app uses emoji reactions that are mapped to scores. 