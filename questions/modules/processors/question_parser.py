"""Question parser for extracting question data from TXT files and creating prompts."""

import re
from typing import Dict, Any, List
from pathlib import Path
from ..core.exceptions import ProcessingError


class QuestionParser:
    """Parser for extracting question data from TXT files."""
    
    PROMPT_TEMPLATES = {
        'multiple_choice_radio': """Stai rispondendo a una domanda di storia dell'arte italiana. Fornisci SOLO la lettera della risposta corretta (A, B, C, D, o E).

{question_content}

Rispondi solo con la lettera:""",
        
        'multiple_choice': """Stai rispondendo a una domanda di storia dell'arte italiana. Fornisci SOLO la lettera della risposta corretta (A, B, C, o D).

{question_content}

Rispondi solo con la lettera:""",
        
        'multiple_choice_check': """Stai rispondendo a una domanda di storia dell'arte italiana. Più risposte possono essere corrette. Fornisci SOLO le lettere di TUTTE le risposte corrette, separate da virgole.

{question_content}

Rispondi solo con le lettere (es. "A, C, E"):""",
        
        'select_errors': """Stai rivedendo un testo di storia dell'arte italiana per trovare errori. Identifica le parole o frasi incorrette nel testo. Fornisci SOLO le parole/frasi incorrette, separate da virgole.

{question_content}

Rispondi solo con le parole/frasi incorrette:""",
        
        'completion_closed': """Stai completando un testo di storia dell'arte italiana. Per ogni spazio vuoto, scegli l'opzione corretta tra quelle proposte. Fornisci le risposte nel formato "BLANK_1: risposta, BLANK_2: risposta".

{question_content}

Rispondi nel formato specificato:""",
        
        'completion_open': """Stai completando un testo di storia dell'arte italiana. Inserisci i termini appropriati per ogni spazio vuoto [BLANK]. Fornisci solo i termini, separati da virgole, nell'ordine in cui appaiono nel testo.

{question_content}

Rispondi solo con i termini:""",
        
        'positioning': """Stai completando un testo di storia dell'arte italiana. Scegli i termini corretti dalla lista proposta per riempire gli spazi vuoti. Fornisci solo i termini scelti, separati da virgole, nell'ordine in cui appaiono nel testo.

{question_content}

Rispondi solo con i termini scelti:""",
        
        'true_false': """Stai valutando affermazioni sulla storia dell'arte italiana. Per ogni affermazione, determina se è Vera o Falsa. Fornisci le risposte nel formato "A: Vero, B: Falso, C: Vero".

{question_content}

Rispondi nel formato specificato:"""
    }
    
    def parse_txt_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse TXT file and extract question components.
        
        Args:
            filepath: Path to the TXT file
            
        Returns:
            Dictionary with question components
            
        Raises:
            ProcessingError: If file cannot be read or parsed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            raise ProcessingError(f"Error reading file {filepath}: {e}")
        
        lines = content.split('\n')
        
        # Extract components
        title = ""
        question_type = ""
        instructions = ""
        question_text = ""
        choices = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("Title:"):
                title = line[6:].strip()
            elif line in ["SCELTA MULTIPLA", "VERO O FALSO", "COMPLETAMENTO APERTO", 
                         "POSIZIONAMENTO", "COMPLETAMENTO CHIUSO", "TROVA ERRORE"]:
                question_type = self._map_question_type(line)
                # Get instructions (next line)
                if i + 1 < len(lines):
                    instructions = lines[i + 1].strip()
                    i += 1
            elif line.startswith("Question:"):
                question_text = line[9:].strip()
                # Continue reading question text until we hit "Choices:" or end
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("Choices:"):
                    if lines[j].strip():
                        question_text += " " + lines[j].strip()
                    j += 1
                i = j - 1
            elif line.startswith("Choices:"):
                # Read all choices
                j = i + 1
                while j < len(lines):
                    choice_line = lines[j].strip()
                    if choice_line:
                        choices.append(choice_line)
                    j += 1
                break
            
            i += 1
        
        return {
            'title': title,
            'question_type': question_type,
            'instructions': instructions,
            'question_text': question_text,
            'choices': choices
        }
    
    def _map_question_type(self, italian_type: str) -> str:
        """Map Italian question type to internal type."""
        mapping = {
            "SCELTA MULTIPLA": "multiple_choice_radio",  # Will be refined based on instructions
            "VERO O FALSO": "true_false",
            "COMPLETAMENTO APERTO": "completion_open",
            "POSIZIONAMENTO": "positioning",
            "COMPLETAMENTO CHIUSO": "completion_closed",
            "TROVA ERRORE": "select_errors"
        }
        return mapping.get(italian_type, "unknown")
    
    def refine_question_type(self, question_data: Dict[str, Any]) -> str:
        """
        Refine question type based on instructions and choices.
        
        Args:
            question_data: Question data dictionary
            
        Returns:
            Refined question type
        """
        base_type = question_data['question_type']
        instructions = question_data['instructions'].lower()
        
        if base_type == "multiple_choice_radio":
            if "tutte le risposte" in instructions or "scegli tutte" in instructions:
                return "multiple_choice_check"
            elif len(question_data['choices']) <= 4:
                return "multiple_choice"
        
        return base_type
    
    def format_question_content(self, question_data: Dict[str, Any]) -> str:
        """
        Format question for LLM prompt.
        
        Args:
            question_data: Question data dictionary
            
        Returns:
            Formatted question content
        """
        content_parts = []
        
        if question_data['title']:
            content_parts.append(f"Titolo: {question_data['title']}")
        
        if question_data['instructions']:
            content_parts.append(f"{question_data['instructions']}")
        
        if question_data['question_text']:
            content_parts.append(f"Domanda: {question_data['question_text']}")
        
        if question_data['choices']:
            content_parts.append("Opzioni:")
            for choice in question_data['choices']:
                content_parts.append(choice)
        
        return "\n\n".join(content_parts)
    
    def create_prompt(self, question_data: Dict[str, Any]) -> str:
        """
        Create complete prompt for LLM.
        
        Args:
            question_data: Question data dictionary
            
        Returns:
            Complete LLM prompt
        """
        question_type = self.refine_question_type(question_data)
        template = self.PROMPT_TEMPLATES.get(question_type, self.PROMPT_TEMPLATES['multiple_choice'])
        question_content = self.format_question_content(question_data)
        
        return template.format(question_content=question_content)
    
    def get_question_id_from_path(self, txt_file: str) -> str:
        """
        Extract question ID from filename.
        
        Args:
            txt_file: Path to TXT file
            
        Returns:
            Question ID
        """
        filename = Path(txt_file).name
        return filename[:4] if filename.endswith('.txt') and len(filename) == 8 else filename
    
    def validate_question_data(self, question_data: Dict[str, Any]) -> bool:
        """
        Validate question data completeness.
        
        Args:
            question_data: Question data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['question_type', 'question_text']
        return all(question_data.get(field) for field in required_fields)