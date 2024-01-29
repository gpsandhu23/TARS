import logging
import json
from dotenv import load_dotenv
from langchain.evaluation import load_evaluator
from langchain.chat_models import ChatOpenAI
from AI_module.agent import process_user_task

logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

evaluator = load_evaluator("labeled_score_string", llm=ChatOpenAI(model="gpt-4"))

# Function to evaluate a single prediction
def evaluate_single_prediction(input_text, reference):
    prediction = process_user_task(input_text)
    eval_result = evaluator.evaluate_strings(
        prediction=prediction,
        reference=reference,
        input=input_text,
    )
    return eval_result

# Process the JSONL file
def process_evaluations(file_path):
    total_score = 0
    count = 0
    max_score_per_evaluation = 10  # Assuming each evaluation is out of 10
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            result = evaluate_single_prediction(data['input'], data['ideal'])
            print(f"Input: {data['input']}\nIdeal: {data['ideal']}\nEvaluation: {result}\n")
            
            total_score += result['score']
            count += 1

    # Calculate the maximum possible score
    max_possible_score = count * max_score_per_evaluation
    print(f"Accumulated Score: {total_score}/{max_possible_score}")

# Process the evals.jsonl file
process_evaluations('evals/evals.jsonl')