import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    answer_correctness,
    context_precision,
    context_recall,
)
import warnings
warnings.filterwarnings('ignore')
from typing import List, Dict
from langchain_core.documents import Document
import pandas as pd
import os


class RAGEvaluator:
    def __init__(self):
        self.metrics = [
            faithfulness,
            answer_relevancy,
            answer_correctness,
            context_precision,
            context_recall,
        ]
        self.artefact_path = os.path.join(os.getcwd(), "artefact")
        os.makedirs(self.artefact_path, exist_ok=True)

    def evaluate_single_interaction(self, user_input: str, relevant_docs: List, answer: str) -> Dict[str, float]:
        contexts = []
        for doc in relevant_docs:
            if isinstance(doc, Document):
                contexts.append(doc.page_content)
            elif isinstance(doc, str):
                contexts.append(doc)
            else:
                contexts.append(str(doc))

        ground_truth_data = json.load(open('fpt_shop_ground_truth.json', 'r', encoding='utf-8'))

        best_score = 0
        matched_gt = ""
        for entry in ground_truth_data:
            score = fuzz.partial_ratio(entry['question'].strip().lower(), user_input.strip().lower())
            if score > best_score:
                best_score = score
                matched_gt = entry['ground_truth']

        threshold = 70
        if best_score < threshold:
            matched_gt = ""

        data = {
            "question": [user_input],
            "answer": [answer],
            "contexts": [contexts],
            "reference": [matched_gt],  
        }

        dataset = Dataset.from_dict(data)

        try:
            results = evaluate(dataset, self.metrics)
            self._save_interaction_data(user_input, answer, contexts, results)
            return results
        except Exception as e:
            print(f"Error in evaluation: {e}")
            return {}

    def _save_interaction_data(self, user_input: str, answer: str, contexts: List[str], results: Dict[str, float]):
        csv_path = os.path.join(self.artefact_path, "rag_evaluation_log.csv")

        row = {
            "id":uuid.uuid4(),
            "question": user_input,
            "answer": answer,
            "contexts": " | ".join(contexts),
            "faithfulness": results.get("faithfulness"),
            "answer_relevancy": results.get("answer_relevancy"),
            "answer_correctness": results.get("answer_correctness"),
            "context_precision": results.get("context_precision"),
            "context_recall": results.get("context_recall"),
        }

        try:
            df = pd.DataFrame([row])
            if os.path.exists(csv_path):
                df.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                df.to_csv(csv_path, mode='w', header=True, index=False)
            print(f"Appended evaluation to {csv_path}")
        except Exception as e:
            print(f"Error saving evaluation to CSV: {e}")


_evaluator = None

def get_evaluator():
    global _evaluator
    if _evaluator is None:
        _evaluator = RAGEvaluator()
    return _evaluator

def evaluate_rag_interaction(user_input: str, relevant_docs: List, answer: str) -> Dict[str, float]:
    evaluator = get_evaluator()
    return evaluator.evaluate_single_interaction(user_input, relevant_docs, answer)
