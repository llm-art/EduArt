"""Question processor orchestrating OCR and vision model services."""

import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.runnables import RunnableLambda

from ..core.config import ProcessorConfig
from ..core.exceptions import ProcessingError, FileOperationError
from ..core.types import QuestionData, ProcessingResult, BatchResult, ProcessingStatus, AnswerResult
from ..services.ocr_service import OCRService
from ..services.vision_service import VisionModelService
from ..services.html_service import HTMLService
from ..managers.prompt_manager import PromptManager
from ..json_manager import JSONManager
from ..config import Config


class QuestionProcessor:
    """Main orchestrator for question processing using OCR and vision models."""
    
    def __init__(self, config: ProcessorConfig):
        """
        Initialize question processor.
        
        Args:
            config: Processing configuration
        """
        self.config = config
        
        # Initialize services
        self.ocr_service = OCRService()
        self.vision_service = VisionModelService()
        self.html_service = HTMLService()
        self.prompt_manager = PromptManager()
        self.json_manager = JSONManager()
        
        # Set up service dependencies
        self.vision_service.set_prompt_manager(self.prompt_manager)
        
        # Paths
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data"
        self.output_path = self.base_path / "output"
    
    def process_single_question(self, exercise: int, question: int) -> ProcessingResult:
        """
        Process a single question through the complete pipeline.
        
        Args:
            exercise: Exercise number
            question: Question number
            
        Returns:
            ProcessingResult with question data or error information
        """
        start_time = time.time()
        result = ProcessingResult(success=False, status=ProcessingStatus.IN_PROGRESS)
        
        try:
            print(f"\n=== Processing Question {exercise}/{question} ===")
            
            # Step 1: Validate input files
            image_path = self.data_path / f"{exercise}/raw/{question}.png"
            html_path = self.data_path / f"{exercise}/raw/{question}.html"
            
            if not image_path.exists():
                raise FileOperationError(f"Image file not found: {image_path}")
            if not html_path.exists():
                raise FileOperationError(f"HTML file not found: {html_path}")
            
            # Step 2: Text extraction (HTML or OCR based on force_ocr setting)
            if self.config.force_ocr:
                print("Step 1: OCR text extraction (forced)...")
                ocr_cache_path = self.output_path / f"{exercise}/ocr/{question}.json"
                text_content = self.ocr_service.process_with_cache(
                    image_path=image_path,
                    ocr_cache_path=ocr_cache_path,
                    force_ocr=True
                )
                ocr_text = text_content
            else:
                print("Step 1: HTML text extraction...")
                text_content = self.html_service.extract_text(html_path)
                ocr_text = text_content  # Use HTML text as the primary text source
            
            # Step 3: Read HTML content (always needed for vision model)
            print("Step 2: Reading HTML content...")
            with open(html_path, 'r', encoding='utf-8') as f:
                html_text = f.read()
            
            # Step 4: Vision model processing
            print("Step 3: Vision model processing...")
            question_data = self.vision_service.process_question(
                image_path=image_path,
                ocr_text=ocr_text,
                html_text=html_text,
                exercise=exercise,
                question=question,
                track_metadata=self.config.metadata_ai
            )

            
            # Step 6: Save results
            print("Step 6: Saving results...")
            self._save_question_data(question_data)
            
            # Mark as completed
            processing_time = time.time() - start_time
            result.mark_completed(question_data, processing_time)
            
            print(f"✅ Question {exercise}/{question} processed successfully in {processing_time:.2f}s")
            print(f"   Type: {question_data.type}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Failed to process question {exercise}/{question}: {e}"
            print(f"❌ {error_msg}")
            
            result.mark_failed(error_msg)
            result.processing_time = processing_time
            
            return result
    
    def process_questions_batch(self, exercise: int, question_range: range) -> BatchResult:
        """
        Process multiple questions in batch.
        
        Args:
            exercise: Exercise number
            question_range: Range of question numbers to process
            
        Returns:
            BatchResult with aggregated results
        """
        start_time = time.time()
        batch_result = BatchResult(
            exercise=exercise,
            total_questions=len(question_range)
        )
        
        print(f"\n=== Batch Processing Exercise {exercise} ===")
        print(f"Questions: {min(question_range)}-{max(question_range)}")
        print(f"Total questions: {len(question_range)}")
        
        # Process each question
        for question in question_range:
            result = self.process_single_question(exercise, question)
            
            # Create pipeline result (for now, only processing stage)
            from ..core.types import PipelineResult
            pipeline_result = PipelineResult(
                exercise=exercise,
                question=question,
                processing_result=result
            )
            
            batch_result.add_result(pipeline_result)
        
        # Calculate total time
        batch_result.total_time = time.time() - start_time
        
        # Print summary
        print(f"\n=== Batch Processing Summary ===")
        print(f"Exercise: {exercise}")
        print(f"Total questions: {batch_result.total_questions}")
        print(f"Successful: {batch_result.successful_questions}")
        print(f"Failed: {batch_result.failed_questions}")
        print(f"Success rate: {batch_result.success_rate:.1f}%")
        print(f"Total time: {batch_result.total_time:.2f}s")
        
        return batch_result
    
    def process_questions_langchain(self, exercise: int, question_range: range) -> List[Dict[str, Any]]:
        """
        Process questions using LangChain pipeline (for backward compatibility).
        
        Args:
            exercise: Exercise number
            question_range: Range of question numbers to process
            
        Returns:
            List of processed question dictionaries
        """
        # Create LangChain runnables
        ocr_runnable = RunnableLambda(self._ocr_step)
        extract_type_runnable = RunnableLambda(self._extract_question_type_step)
        extract_text_runnable = RunnableLambda(self._extract_question_text_step)
        
        # Chain them together
        pipeline = ocr_runnable | extract_type_runnable | extract_text_runnable
        
        # Prepare batch input data
        batch_inputs = [
            {
                "base_path": self.data_path,
                "output_path": self.output_path,
                "exercise": exercise,
                "question": question,
                "force_ocr": self.config.force_ocr
            }
            for question in question_range
        ]
        
        print(f"Starting LangChain batch processing...")
        
        # Use LangChain's batch method
        results = pipeline.batch(
            batch_inputs,
            config={
                "max_concurrency": 1,
                "return_exceptions": True
            }
        )
        
        # Process and save results
        processed_results = []
        for i, result in enumerate(results):
            question = list(question_range)[i]
            
            if isinstance(result, Exception):
                print(f"Error processing question {question}: {result}")
                continue
            
            try:
                # Add image path if applicable
                result.setdefault("image", str(
                    self.data_path / f"{exercise}/imgs/{question}.jpg"
                ) if "has_image" in result else None)
                
                # Save individual result
                parsed_path = self.output_path / f"{exercise}/json/{question}.json"
                parsed_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Remove keys not needed in final output
                for key in ["base_path", "output_path", "force_ocr", "ocr_text"]:
                    result.pop(key, None)
                
                with open(parsed_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                processed_results.append(result)
                
                question_type = result.get("type", "unknown")
                print(f"Successfully processed question {question} (type: {question_type})")
                
            except Exception as e:
                print(f"Error saving question {question}: {e}")
        
        return processed_results
    
    def _generate_answer(self, question_data: QuestionData) -> AnswerResult:
        """
        Generate answer for the question using the vision service.
        
        Args:
            question_data: The processed question data
            
        Returns:
            AnswerResult with generated answer or error information
        """
        start_time = time.time()
        
        try:
            # Convert QuestionData to dictionary format expected by vision service
            question_dict = {
                "exercise": question_data.exercise,
                "question": question_data.question,
                "type": question_data.type,
                "question_title": question_data.question_title,
                "question_text": question_data.question_text,
                "choices": self._serialize_choices(question_data.choices, question_data.type),
                "image": question_data.image_path,
                "language": question_data.language,
                "has_image": question_data.has_image
            }
            
            # Generate answer using vision service
            answer_response = self.vision_service.generate_answer(question_dict)
            
            processing_time = time.time() - start_time
            
            if answer_response.get('success', False):
                result = AnswerResult(success=True)
                result.mark_completed(
                    answer=answer_response.get('generated_answer'),
                    model=answer_response.get('model_name'),
                    raw_response=answer_response.get('raw_response'),
                    used_image=answer_response.get('used_image', False),
                    processing_time=processing_time
                )
                
                # AI call metadata is automatically tracked by vision service
                # Get the latest AI calls from vision service
                if self.config.metadata_ai:
                    latest_ai_calls = self.vision_service.get_ai_calls()
                    if latest_ai_calls:
                        # Add the latest AI call (answer generation) to question data
                        if not question_data.ai_calls:
                            question_data.ai_calls = []
                        question_data.ai_calls.extend(latest_ai_calls[-1:])  # Add only the latest call
                
                print(f"✅ Answer generated successfully: {result.generated_answer}")
                return result
            else:
                result = AnswerResult(success=False)
                result.mark_failed(answer_response.get('error', 'Unknown error'))
                print(f"❌ Answer generation failed: {result.error}")
                return result
                
        except Exception as e:
            processing_time = time.time() - start_time
            result = AnswerResult(success=False)
            result.mark_failed(str(e))
            result.processing_time = processing_time
            print(f"❌ Answer generation error: {e}")
            return result

    def _save_question_data(self, question_data: QuestionData) -> None:
        """Save question data to JSON file."""
        output_file = self.output_path / f"{question_data.exercise}/json/{question_data.question}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary for JSON serialization
        data_dict = {
            "exercise": question_data.exercise,
            "question": question_data.question,
            "type": question_data.type,
            "answers": question_data.answers,
            "question_title": question_data.question_title,
            "question_text": question_data.question_text,
            "choices": self._serialize_choices(question_data.choices, question_data.type),
            "image": question_data.image_path,
            "language": question_data.language,
            "has_image": question_data.has_image
        }

        if data_dict["has_image"] :
            data_dict["image"] = data_dict['image'].replace("raw","imgs").replace(".png",".jpg")

        # Add AI metadata if tracking is enabled and calls exist
        if self.config.metadata_ai and question_data.ai_calls:
            data_dict["ai_calls"] = [
                {
                    "description": call.description,
                    "model_name": call.model_name,
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "total_tokens": call.total_tokens,
                    "processing_time": call.processing_time,
                    "timestamp": call.timestamp
                }
                for call in question_data.ai_calls
            ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
    
    def _serialize_choices(self, choices, question_type: str):
        """
        Serialize choices based on question type.
        
        Args:
            choices: The choices data
            question_type: Type of question
            
        Returns:
            Serialized choices for JSON output
        """
        if not choices:
            return None
        
        if question_type == "completion_closed":
            # completion_closed format: [{"id": "BLANK_1", "options": ["choice1", "choice2"]}]
            return choices  # Keep as-is
        elif question_type == "positioning":
            # positioning format: ["choice1", "choice2", "choice3"]
            return choices  # Keep as-is
        else:
            # Standard multiple choice format: convert Choice objects to dicts
            serialized = []
            for choice in choices:
                if hasattr(choice, 'id') and hasattr(choice, 'text'):
                    # Choice object
                    serialized.append({
                        "id": choice.id,
                        "text": choice.text,
                        "is_correct": getattr(choice, 'is_correct', None)
                    })
                elif isinstance(choice, dict):
                    # Already a dict
                    serialized.append(choice)
                else:
                    # String or other format
                    serialized.append(choice)
            return serialized
    
    # LangChain compatibility methods
    def _ocr_step(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """OCR step for LangChain pipeline."""
        try:
            image_path = data["base_path"] / f"{data['exercise']}/raw/{data['question']}.png"
            ocr_cache_path = data["output_path"] / f"{data['exercise']}/ocr/{data['question']}.json"
            
            ocr_text = self.ocr_service.process_with_cache(
                image_path=image_path,
                ocr_cache_path=ocr_cache_path,
                force_ocr=data.get('force_ocr', False)
            )
            
            return {**data, "ocr_text": ocr_text}
            
        except Exception as e:
            return {**data, "ocr_error": str(e), "ocr_text": ""}
    
    def _extract_question_type_step(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Question type extraction step for LangChain pipeline."""
        try:
            image_path = data["base_path"] / f"{data['exercise']}/raw/{data['question']}.png"
            html_path = data["base_path"] / f"{data['exercise']}/raw/{data['question']}.html"
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_text = f.read()
            
            type_data = self.vision_service.extract_question_type(
                image_path=image_path,
                ocr_text=data["ocr_text"],
                html_text=html_text
            )
            
            return {**data, **type_data}
            
        except Exception as e:
            return {**data, "extraction_error": str(e), "type": "unknown"}
    
    def _extract_question_text_step(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Question text extraction step for LangChain pipeline."""
        try:
            image_path = data["base_path"] / f"{data['exercise']}/raw/{data['question']}.png"
            html_path = data["base_path"] / f"{data['exercise']}/raw/{data['question']}.html"
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_text = f.read()
            
            text_data = self.vision_service.extract_question_text(
                image_path=image_path,
                question_type=data.get("type", "unknown"),
                ocr_text=data["ocr_text"],
                html_text=html_text
            )
            
            return {**data, **text_data}
            
        except Exception as e:
            return {**data, "text_extraction_error": str(e)}