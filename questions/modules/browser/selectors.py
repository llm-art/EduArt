"""
Centralized selector strategies for Zanichelli exercise automation.

This module contains all CSS selectors and their fallback strategies,
eliminating duplication across the codebase.
"""

from typing import List, Dict, Any


class SelectorStrategies:
    """Centralized selector strategies for different UI elements."""
    
    # Login and Authentication Selectors
    ENTRA_BUTTON = [
        'button:has-text("ENTRA")',
        'a:has-text("ENTRA")',
        'button:has-text("Entra")',
        'a:has-text("Entra")',
        'button:text-matches("ENTRA", "i")',
        'a:text-matches("ENTRA", "i")',
        '.btn:has-text("ENTRA")',
        '.button:has-text("ENTRA")',
        '[role="button"]:has-text("ENTRA")',
        '.login-btn',
        '.auth-btn',
        '[data-testid*="login"]',
        '[data-testid*="entra"]'
    ]
    
    USERNAME_FIELD = [
        'input[placeholder="Inserisci l\'email o il cellulare"]',
        'input[placeholder*="email o il cellulare"]',
        'input[placeholder*="email"]',
        'input[placeholder*="cellulare"]',
        'input[type="email"]',
        'input[type="text"]',
        'input[name*="email"]',
        'input[name*="username"]',
        'input[name*="user"]',
        'input[id*="email"]',
        'input[id*="username"]',
        'input[id*="user"]',
        '.modal input[type="text"]:first-of-type',
        '.modal input:first-of-type'
    ]
    
    PASSWORD_FIELD = [
        'input[placeholder="Inserisci la tua password"]',
        'input[placeholder*="Inserisci la tua password"]',
        'input[placeholder*="password"]',
        'input[type="password"]',
        'input[name*="password"]',
        'input[name*="pass"]',
        'input[id*="password"]',
        'input[id*="pass"]',
        '.modal input[type="password"]:first-of-type',
        '.modal input:nth-of-type(2)'
    ]
    
    LOGIN_SUBMIT = [
        'z-modal button:has-text("ENTRA")',
        'idp-login-modal button:has-text("ENTRA")',
        '.sc-idp-login-modal button:has-text("ENTRA")',
        '.modal button:has-text("ENTRA")',
        '[role="dialog"] button:has-text("ENTRA")',
        '.popup button:has-text("ENTRA")',
        '.overlay button:has-text("ENTRA")',
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("ENTRA")',
        'button:has-text("Entra")',
        'button:has-text("LOGIN")',
        'button:has-text("ACCEDI")',
        '.btn-primary',
        '.submit-btn',
        '.login-submit'
    ]
    
    # Cookie Banner Selectors
    COOKIE_ACCEPT = [
        'button:has-text("Accetta")',
        'button:has-text("Accetto")',
        'button:has-text("Accetta tutti")',
        'button:has-text("Accept")',
        'button:has-text("OK")',
        'button:has-text("Continua")',
        '[id*="cookie"] button',
        '[class*="cookie"] button',
        '[data-testid*="cookie"] button',
        '.modal button:has-text("Accetta")',
        '.overlay button:has-text("Accetta")',
        '.cookie-banner button',
        '.privacy-banner button'
    ]
    
    COOKIE_BANNER_ELEMENTS = [
        '[id*="cookie"]', '[class*="cookie"]', '[data-testid*="cookie"]',
        '[id*="consent"]', '[class*="consent"]', '[data-testid*="consent"]',
        '.ot-sdk-container', '#onetrust-consent-sdk', '.ot-fade-in',
        '[id*="onetrust"]', '[class*="onetrust"]', '[class*="ot-"]'
    ]
    
    # Exercise Card Selectors
    EXERCISE_CARDS = [
        'z-card:has(button:has-text("Anteprima"))',
        'z-card[clickable]',
        'z-card',
    ]
    
    ANTEPRIMA_BUTTON = [
        '[slot="action"] button:has-text("Anteprima")',
        '[slot="action"] button:has-text("ANTEPRIMA")',
        'button:has-text("Anteprima")',
        'button:has-text("ANTEPRIMA")',
        'a:has-text("Anteprima")',
        'a:has-text("ANTEPRIMA")',
        '.btn:has-text("Anteprima")',
        '.button:has-text("Anteprima")'
    ]
    
    # Exercise Action Buttons
    SVOLGI_BUTTON = [
        'button:has-text("SVOLGI")',
        'button:has-text("Svolgi")',
        'button:has-text("svolgi")',
        'button:text-matches("SVOLGI", "i")',
        '.modal button:has-text("SVOLGI")',
        '.drawer button:has-text("SVOLGI")',
        '.popup button:has-text("SVOLGI")',
        '[role="dialog"] button:has-text("SVOLGI")',
        '.overlay button:has-text("SVOLGI")',
        'a:has-text("SVOLGI")',
        '[role="button"]:has-text("SVOLGI")',
        '.btn:has-text("SVOLGI")',
        '.button:has-text("SVOLGI")',
        'button:has-text("INIZIA")',
        'button:has-text("AVVIA")',
        'button:has-text("START")'
    ]
    
    INIZIA_BUTTON = [
        'button:has-text("INIZIA")',
        'button:has-text("Inizia")',
        'button:has-text("inizia")',
        'button:text-matches("INIZIA", "i")',
        'a:has-text("INIZIA")',
        'a:has-text("Inizia")',
        '[role="button"]:has-text("INIZIA")',
        '.btn:has-text("INIZIA")',
        '.button:has-text("INIZIA")',
        'button:has-text("AVVIA")',
        'button:has-text("START")',
        'button:has-text("CONTINUA")',
        '.start-btn',
        '.inizia-btn',
        '.continue-btn'
    ]
    
    TERMINA_PROVA_BUTTON = [
        'button:has-text("TERMINA PROVA")',
        'button:has-text("Termina prova")',
        'button:has-text("TERMINA")',
        'button:has-text("FINE")',
        'button:has-text("COMPLETA")',
        'button:has-text("FINISH")',
        '.finish-btn',
        '.termina-btn',
        '.complete-btn'
    ]
    
    # Question Navigation Selectors
    CURRENT_QUESTION_DATA_INDEX = [
        '.slick-slide.slick-active.slick-current[data-index]',
        '.slick-slide.slick-active[data-index]',
        '.slick-current[data-index]',
        '[data-index].slick-active',
        '[data-index].slick-current',
        '[data-index][class*="active"]',
        '[data-index][class*="current"]'
    ]
    
    PAGINATION_ACTIVE = [
        '.pagination .active',
        '.pagination .current',
        '.pagination .selected',
        '.pagination [class*="active"]',
        '.pagination button[class*="active"]',
        '.pagination a[class*="active"]'
    ]
    
    PAGINATION_ELEMENTS = [
        '.pagination button',
        '.pagination a',
        '.pagination span',
        '[class*="pagination"] button',
        '[class*="pagination"] a',
        '[class*="pagination"] span'
    ]
    
    NEXT_QUESTION_NAVIGATION = [
        'button:has-text("Avanti")',
        'button:has-text("Prossima")',
        'button:has-text("Next")',
        'button:has-text(">")',
        '.pagination .next',
        '.pagination [class*="next"]',
        '.pagination button:last-child',
        '.pagination a:last-child'
    ]
    
    # Content Extraction Selectors
    EXERCISE_TITLE = [
        'div[class*="sc-kRZjnb"] div[class*="sc-ejXMOB"]',
        'div[class*="sc-kRZjnb"]',
        'h1:has-text("pittura")',
        'h2:has-text("pittura")',
        'h3:has-text("pittura")',
        ':has-text("La pittura rinascimentale")',
        ':has-text("pittura rinascimentale")',
        'h1', 'h2', 'h3',
        '.title',
        '[class*="title"]'
    ]
    
    CARD_TITLE = [
        '[slot="text"] .body-2-sb',
        '[slot="text"] div:first-child',
        '[slot="text"] .emQEvG',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        '.title', '.exercise-title', '.card-title',
        '[class*="title"]', '[class*="heading"]'
    ]
    
    QUESTION_CONTENT = [
        ':has-text("La pittura rinascimentale") ~ div',
        ':has-text("La pittura rinascimentale") + div',
        ':has-text("La pittura rinascimentale"):not(input):not(button) ~ *:has(img)',
        ':has-text("La pittura rinascimentale"):not(input):not(button) ~ *:has(input[type="checkbox"])',
        ':has-text("La pittura rinascimentale"):not(input):not(button) ~ *:has(label)',
        'div:has-text("La pittura rinascimentale") ~ div:has(img)',
        'div:has-text("La pittura rinascimentale") ~ div:has(input)',
        'div:has-text("La pittura rinascimentale") ~ div:has(label)',
        'div:has-text("Individua le affermazioni corrette")',
        'div:has-text("riferite all\'immagine")',
        'div:has-text("Individua") div:has(img)',
        'div:has-text("affermazioni") div:has(input)',
        'div:has(input[type="checkbox"]) div:has-text("A.")',
        'div:has(input[type="checkbox"]) div:has-text("B.")',
        'div:has(label):has-text("A.")',
        'div:has(label):has-text("B.")',
        'div:has(img):has-text("Individua")',
        'div:has(img):has-text("affermazioni")',
        'div:has(img) + div:has(input)',
        'div:has(img) ~ div:has(input)',
        'form:has(input[type="checkbox"])',
        'div:has(input[type="checkbox"]):has(label)',
        'fieldset:has(input[type="checkbox"])',
        'main div:has(img):has(input)',
        'main div:has(img):has(label)',
        'article div:has(img):has(input)',
        'section div:has(img):has(input)',
        '.question-content',
        '.exercise-content',
        '.problem-content',
        '.quiz-content',
        'div:has(input[type="checkbox"])',
        'div:has(label)',
        'div:has(img):not([class*="header"]):not([class*="nav"]):not([class*="footer"])'
    ]
    
    # Image Detection Selectors
    QUESTION_IMAGES = [
        '.question img',
        '.content img',
        '.exercise img',
        'img[src*=".jpg"]',
        'img[src*=".jpeg"]',
        'img[src*=".png"]',
        'img[src*=".gif"]',
        'img[src*=".webp"]',
        '.question-content img',
        '.exercise-content img',
        '.problem img',
        '.artwork img',
        'img[width]:not([width="16"]):not([width="24"]):not([width="32"])',
        'img[height]:not([height="16"]):not([height="24"]):not([height="32"])',
        'main img',
        'article img',
        '.main-content img'
    ]
    

    # Answer Interaction Selectors
    ANSWER_CLICK_INTERACTION = [
      # Custom checkbox labels (PRIORITY - most common pattern for multiple choice)
      'label:has(input[type="checkbox"])',
      'label:has(input[type="checkbox"][name="answers"])',
      
      # Direct label selectors for custom checkboxes
      'label[class*="sc-"]',  # Matches styled components pattern
      
      # Radio button labels and inputs
      'label:has(input[type="radio"])',
      'input[type="radio"]',
      
      # Completamento chiuso
      '.choiceChip span[role="button"]',
      '.choiceChip span[role="button"][tabindex=*]',
      
      # Positioning/drag-and-drop elements
      '[draggable="true"]',
      '.sc-kQFRQl',  # Drop targets
      'button.sc-izXThL',  # Clickable positioning buttons
      '.sc-dNHLo button',  # Alternative positioning buttons
      '[class*="blank"]',  # Blank spaces
      '[class*="drop"]',  # Drop zones
      
      # Text inputs for completamento aperto
      'input[type="text"]:not([readonly])',
      'textarea:not([readonly])',
      
      # LAST RESORT: Direct checkbox inputs (often hidden, avoid if possible)
      'input[type="checkbox"]',
      'input[type="checkbox"][name="answers"]'
    ]
    
    @classmethod
    def get_selectors(cls, selector_type: str) -> List[str]:
        """Get selectors for a specific type."""
        return getattr(cls, selector_type, [])
    
    @classmethod
    def get_all_selector_types(cls) -> List[str]:
        """Get all available selector types."""
        return [attr for attr in dir(cls) if not attr.startswith('_') and isinstance(getattr(cls, attr), list)]
    
    @classmethod
    def create_data_index_selector(cls, data_index: int) -> List[str]:
        """Create selectors for specific data-index values."""
        return [
            f'div[data-index="{data_index}"] a',
            f'[data-index="{data_index}"] a',
            f'.slick-slide[data-index="{data_index}"] a'
        ]
    
    @classmethod
    def get_click_strategies(cls) -> List[Dict[str, Any]]:
        """Get different click strategies for handling modal overlays."""
        return [
            {'name': 'direct', 'force': False, 'position': None},
            {'name': 'force', 'force': True, 'position': None},
            {'name': 'center', 'force': False, 'position': {'x': 0, 'y': 0}}
        ]