"""Results manager for storing and exporting evaluation results."""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..core.exceptions import ProcessingError


class ResultsManager:
    """Manager for storing and exporting evaluation results."""
    
    def __init__(self, results_dir: Optional[str] = None):
        """
        Initialize results manager.
        
        Args:
            results_dir: Directory to store results (defaults to questions/results)
        """
        if results_dir is None:
            # Default to questions/results relative to this module
            questions_dir = Path(__file__).parent.parent.parent
            self.results_dir = questions_dir / 'results'
        else:
            self.results_dir = Path(results_dir)
        
        self.results: List[Dict[str, Any]] = []
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create answers subdirectory for individual question results
        self.answers_dir = self.results_dir / 'answers'
        self.answers_dir.mkdir(parents=True, exist_ok=True)
    
    def add_result(self, question_id: str, model_name: str, question_type: str,
                   llm_answer: str, correct_answer: str, evaluation: Dict[str, Any],
                   processing_time: float, error: str = "", question_data: Optional[Dict[str, Any]] = None):
        """
        Add evaluation result.
        
        Args:
            question_id: Question identifier
            model_name: Name of the LLM model
            question_type: Type of question
            llm_answer: LLM response
            correct_answer: Correct answer
            evaluation: Evaluation results
            processing_time: Time taken to process
            error: Error message if any
            question_data: Additional question data for individual JSON files
        """
        result = {
            'question_id': question_id,
            'model_name': model_name,
            'question_type': question_type,
            'llm_answer': llm_answer,
            'correct_answer': correct_answer,
            'is_correct': evaluation.get('is_correct'),
            'score': evaluation.get('score'),
            'details': evaluation.get('details', ''),
            'processing_time': processing_time,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        # Save individual question result as JSON
        self._save_individual_result(question_id, result, question_data)
    
    def _save_individual_result(self, question_id: str, result: Dict[str, Any], question_data: Optional[Dict[str, Any]] = None):
        """
        Save individual question result as JSON file.
        
        Args:
            question_id: Question identifier
            result: Result data
            question_data: Additional question data
        """
        try:
            # Create comprehensive result data
            individual_result = {
                'question_id': question_id,
                'evaluation': {
                    'model_name': result['model_name'],
                    'question_type': result['question_type'],
                    'llm_answer': result['llm_answer'],
                    'correct_answer': result['correct_answer'],
                    'is_correct': result['is_correct'],
                    'score': result['score'],
                    'details': result['details'],
                    'processing_time': result['processing_time'],
                    'error': result['error'],
                    'timestamp': result['timestamp']
                }
            }
            
            # Add question data if provided
            if question_data:
                individual_result['question_data'] = question_data
            
            # Save to individual JSON file
            json_filepath = self.answers_dir / f"{question_id}.json"
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(individual_result, f, indent=2, ensure_ascii=False)
            
            print(f"Individual result saved to {json_filepath}")
            
        except Exception as e:
            print(f"Warning: Failed to save individual result for question {question_id}: {e}")
    
    def export_to_csv(self, filepath: str):
        """
        Export results to CSV.
        
        Args:
            filepath: Path to CSV file
            
        Raises:
            ProcessingError: If export fails
        """
        if not self.results:
            print("No results to export")
            return
        
        try:
            fieldnames = ['question_id', 'model_name', 'question_type', 'llm_answer', 
                         'correct_answer', 'is_correct', 'score', 'details', 
                         'processing_time', 'error', 'timestamp']
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"Results exported to {filepath}")
        except Exception as e:
            raise ProcessingError(f"Failed to export results to CSV: {e}")
    
    def calculate_precision_recall_f1(self, results_subset: List[Dict]) -> Dict[str, float]:
        """
        Calculate precision, recall, and F1 score for a subset of results.
        
        Args:
            results_subset: Subset of results to analyze
            
        Returns:
            Dictionary with metrics
        """
        if not results_subset:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'accuracy': 0.0}
        
        # Filter out results without ground truth (None values)
        valid_results = [r for r in results_subset if r['is_correct'] is not None]
        
        if not valid_results:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'accuracy': 0.0}
        
        # For binary classification (correct/incorrect)
        true_positives = sum(1 for r in valid_results if r['is_correct'] and r['score'] > 0.5)
        false_positives = sum(1 for r in valid_results if not r['is_correct'] and r['score'] > 0.5)
        false_negatives = sum(1 for r in valid_results if r['is_correct'] and r['score'] <= 0.5)
        true_negatives = sum(1 for r in valid_results if not r['is_correct'] and r['score'] <= 0.5)
        
        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (true_positives + true_negatives) / len(valid_results) if valid_results else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'accuracy': accuracy,
            'total_samples': len(valid_results)
        }
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics.
        
        Returns:
            Summary statistics dictionary
        """
        if not self.results:
            return {}
        
        total_questions = len(set(r['question_id'] for r in self.results))
        total_evaluations = len(self.results)
        
        # Overall metrics
        overall_metrics = self.calculate_precision_recall_f1(self.results)
        
        # Accuracy by model (legacy metric)
        accuracy_by_model = {}
        metrics_by_model = {}
        for model in set(r['model_name'] for r in self.results):
            model_results = [r for r in self.results if r['model_name'] == model]
            model_results_valid = [r for r in model_results if r['is_correct'] is not None]
            
            if model_results_valid:
                correct = sum(1 for r in model_results_valid if r['is_correct'])
                accuracy_by_model[model] = correct / len(model_results_valid)
                metrics_by_model[model] = self.calculate_precision_recall_f1(model_results)
        
        # Accuracy by type (legacy metric)
        accuracy_by_type = {}
        metrics_by_type = {}
        for qtype in set(r['question_type'] for r in self.results):
            type_results = [r for r in self.results if r['question_type'] == qtype]
            type_results_valid = [r for r in type_results if r['is_correct'] is not None]
            
            if type_results_valid:
                correct = sum(1 for r in type_results_valid if r['is_correct'])
                accuracy_by_type[qtype] = correct / len(type_results_valid)
                metrics_by_type[qtype] = self.calculate_precision_recall_f1(type_results)
        
        # Average processing time
        processing_times = [r['processing_time'] for r in self.results if r['processing_time'] > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Score distribution
        scores = [r['score'] for r in self.results if r['score'] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_questions': total_questions,
            'total_evaluations': total_evaluations,
            'overall_metrics': overall_metrics,
            'accuracy_by_model': accuracy_by_model,  # Legacy
            'accuracy_by_type': accuracy_by_type,    # Legacy
            'metrics_by_model': metrics_by_model,
            'metrics_by_type': metrics_by_type,
            'average_processing_time': avg_processing_time,
            'average_score': avg_score,
            'errors': len([r for r in self.results if r['error']])
        }
    
    def print_summary(self):
        """Print comprehensive summary statistics."""
        summary = self.generate_summary()
        
        print("\n" + "="*70)
        print("EVALUATION SUMMARY")
        print("="*70)
        print(f"Total Questions: {summary.get('total_questions', 0)}")
        print(f"Total Evaluations: {summary.get('total_evaluations', 0)}")
        print(f"Errors: {summary.get('errors', 0)}")
        print(f"Average Processing Time: {summary.get('average_processing_time', 0):.2f}s")
        print(f"Average Score: {summary.get('average_score', 0):.3f}")
        
        # Overall metrics
        overall = summary.get('overall_metrics', {})
        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Accuracy:  {overall.get('accuracy', 0):.3f}")
        print(f"  Precision: {overall.get('precision', 0):.3f}")
        print(f"  Recall:    {overall.get('recall', 0):.3f}")
        print(f"  F1 Score:  {overall.get('f1', 0):.3f}")
        print(f"  Samples:   {overall.get('total_samples', 0)}")
        
        # Metrics by model
        print(f"\nPERFORMANCE BY MODEL:")
        print(f"{'Model':<35} {'Acc':<6} {'Prec':<6} {'Rec':<6} {'F1':<6} {'Samples':<8}")
        print("-" * 70)
        for model, metrics in summary.get('metrics_by_model', {}).items():
            print(f"{model:<35} {metrics.get('accuracy', 0):.3f}  {metrics.get('precision', 0):.3f}  "
                  f"{metrics.get('recall', 0):.3f}  {metrics.get('f1', 0):.3f}  {metrics.get('total_samples', 0):<8}")
        
        # Metrics by question type
        print(f"\nPERFORMANCE BY QUESTION TYPE:")
        print(f"{'Question Type':<25} {'Acc':<6} {'Prec':<6} {'Rec':<6} {'F1':<6} {'Samples':<8}")
        print("-" * 70)
        for qtype, metrics in summary.get('metrics_by_type', {}).items():
            print(f"{qtype:<25} {metrics.get('accuracy', 0):.3f}  {metrics.get('precision', 0):.3f}  "
                  f"{metrics.get('recall', 0):.3f}  {metrics.get('f1', 0):.3f}  {metrics.get('total_samples', 0):<8}")
    
    def save_summary_json(self, filepath: Optional[str] = None):
        """
        Save summary as JSON file.
        
        Args:
            filepath: Path to JSON file (defaults to results_dir/evaluation_summary.json)
        """
        if filepath is None:
            filepath = self.results_dir / 'evaluation_summary.json'
        
        try:
            summary = self.generate_summary()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"Summary saved to {filepath}")
        except Exception as e:
            raise ProcessingError(f"Failed to save summary: {e}")
    
    def save_summary_txt(self, filepath: Optional[str] = None):
        """
        Save summary as TXT file.
        
        Args:
            filepath: Path to TXT file (defaults to results_dir/evaluation_summary.txt)
        """
        if filepath is None:
            filepath = self.results_dir / 'evaluation_summary.txt'
        
        try:
            summary = self.generate_summary()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("EVALUATION SUMMARY\n")
                f.write("="*70 + "\n")
                f.write(f"Total Questions: {summary.get('total_questions', 0)}\n")
                f.write(f"Total Evaluations: {summary.get('total_evaluations', 0)}\n")
                f.write(f"Errors: {summary.get('errors', 0)}\n")
                f.write(f"Average Processing Time: {summary.get('average_processing_time', 0):.2f}s\n")
                f.write(f"Average Score: {summary.get('average_score', 0):.3f}\n")
                
                # Overall metrics
                overall = summary.get('overall_metrics', {})
                f.write(f"\nOVERALL PERFORMANCE:\n")
                f.write(f"  Accuracy:  {overall.get('accuracy', 0):.3f}\n")
                f.write(f"  Precision: {overall.get('precision', 0):.3f}\n")
                f.write(f"  Recall:    {overall.get('recall', 0):.3f}\n")
                f.write(f"  F1 Score:  {overall.get('f1', 0):.3f}\n")
                f.write(f"  Samples:   {overall.get('total_samples', 0)}\n")
                
                # Metrics by model
                f.write(f"\nPERFORMANCE BY MODEL:\n")
                f.write(f"{'Model':<35} {'Acc':<6} {'Prec':<6} {'Rec':<6} {'F1':<6} {'Samples':<8}\n")
                f.write("-" * 70 + "\n")
                for model, metrics in summary.get('metrics_by_model', {}).items():
                    f.write(f"{model:<35} {metrics.get('accuracy', 0):.3f}  {metrics.get('precision', 0):.3f}  "
                           f"{metrics.get('recall', 0):.3f}  {metrics.get('f1', 0):.3f}  {metrics.get('total_samples', 0):<8}\n")
                
                # Metrics by question type
                f.write(f"\nPERFORMANCE BY QUESTION TYPE:\n")
                f.write(f"{'Question Type':<25} {'Acc':<6} {'Prec':<6} {'Rec':<6} {'F1':<6} {'Samples':<8}\n")
                f.write("-" * 70 + "\n")
                for qtype, metrics in summary.get('metrics_by_type', {}).items():
                    f.write(f"{qtype:<25} {metrics.get('accuracy', 0):.3f}  {metrics.get('precision', 0):.3f}  "
                           f"{metrics.get('recall', 0):.3f}  {metrics.get('f1', 0):.3f}  {metrics.get('total_samples', 0):<8}\n")
            
            print(f"Summary saved to {filepath}")
        except Exception as e:
            raise ProcessingError(f"Failed to save summary as TXT: {e}")
    
    def save_summary_md(self, filepath: Optional[str] = None):
        """
        Save summary as Markdown file.
        
        Args:
            filepath: Path to MD file (defaults to results_dir/evaluation_summary.md)
        """
        if filepath is None:
            filepath = self.results_dir / 'evaluation_summary.md'
        
        try:
            summary = self.generate_summary()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Evaluation Summary\n\n")
                
                f.write("## Overview\n\n")
                f.write(f"- **Total Questions**: {summary.get('total_questions', 0)}\n")
                f.write(f"- **Total Evaluations**: {summary.get('total_evaluations', 0)}\n")
                f.write(f"- **Errors**: {summary.get('errors', 0)}\n")
                f.write(f"- **Average Processing Time**: {summary.get('average_processing_time', 0):.2f}s\n")
                f.write(f"- **Average Score**: {summary.get('average_score', 0):.3f}\n\n")
                
                # Overall metrics
                overall = summary.get('overall_metrics', {})
                f.write("## Overall Performance\n\n")
                f.write(f"- **Accuracy**: {overall.get('accuracy', 0):.3f}\n")
                f.write(f"- **Precision**: {overall.get('precision', 0):.3f}\n")
                f.write(f"- **Recall**: {overall.get('recall', 0):.3f}\n")
                f.write(f"- **F1 Score**: {overall.get('f1', 0):.3f}\n")
                f.write(f"- **Samples**: {overall.get('total_samples', 0)}\n\n")
                
                # Metrics by model
                f.write("## Performance by Model\n\n")
                f.write("| Model | Accuracy | Precision | Recall | F1 Score | Samples |\n")
                f.write("|-------|----------|-----------|--------|----------|----------|\n")
                for model, metrics in summary.get('metrics_by_model', {}).items():
                    f.write(f"| {model} | {metrics.get('accuracy', 0):.3f} | {metrics.get('precision', 0):.3f} | "
                           f"{metrics.get('recall', 0):.3f} | {metrics.get('f1', 0):.3f} | {metrics.get('total_samples', 0)} |\n")
                
                # Metrics by question type
                f.write("\n## Performance by Question Type\n\n")
                f.write("| Question Type | Accuracy | Precision | Recall | F1 Score | Samples |\n")
                f.write("|---------------|----------|-----------|--------|----------|----------|\n")
                for qtype, metrics in summary.get('metrics_by_type', {}).items():
                    f.write(f"| {qtype} | {metrics.get('accuracy', 0):.3f} | {metrics.get('precision', 0):.3f} | "
                           f"{metrics.get('recall', 0):.3f} | {metrics.get('f1', 0):.3f} | {metrics.get('total_samples', 0)} |\n")
            
            print(f"Summary saved to {filepath}")
        except Exception as e:
            raise ProcessingError(f"Failed to save summary as MD: {e}")
    
    def clear_results(self):
        """Clear all stored results."""
        self.results.clear()
    
    def get_results_count(self) -> int:
        """Get the number of stored results."""
        return len(self.results)
    
    def get_results_by_model(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Get results for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of results for the model
        """
        return [r for r in self.results if r['model_name'] == model_name]
    
    def get_results_by_question_type(self, question_type: str) -> List[Dict[str, Any]]:
        """
        Get results for a specific question type.
        
        Args:
            question_type: Type of question
            
        Returns:
            List of results for the question type
        """
        return [r for r in self.results if r['question_type'] == question_type]