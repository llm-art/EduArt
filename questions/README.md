# Zanichelli Exercise Automation - Unified Version

A streamlined, unified Python automation system for processing Zanichelli exercises using Playwright. This version consolidates all functionality into a single, powerful command-line interface.

## 🏗️ Architecture Overview

The unified codebase follows a **modular architecture** with a single entry point:

```
questions/
├── question_downloader.py          # Unified entry point (single command)
├── config.json.template            # Configuration template
├── modules/                        # Modular components
│   ├── __init__.py                 # Main automator export
│   ├── automator.py                # Orchestrator class using composition
│   ├── browser/                    # Browser automation utilities
│   │   ├── browser_manager.py      # Browser lifecycle management
│   │   ├── selectors.py           # Centralized selector strategies
│   │   └── interactions.py        # Common interaction patterns
│   ├── content/                    # Content processing
│   │   ├── extractor.py           # Content extraction logic
│   │   ├── processor.py           # Content processing utilities
│   │   └── validator.py           # Content quality validation
│   ├── files/                      # File management
│   │   ├── manager.py             # File operations & directory management
│   │   └── downloader.py          # Image and content downloading
│   ├── config/                     # Configuration management
│   │   └── manager.py             # Config loading and validation
│   └── workflows/                  # High-level workflows
│       ├── login.py               # Login workflow
│       ├── navigation.py          # Navigation workflow
│       └── question_processor.py  # Question processing workflow
└── data/                          # Output directories
    └── {exercise_number}/
        ├── imgs/                  # Downloaded images
        ├── raw/                   # Screenshots and HTML files
        └── logs/                  # Processing logs
```

## 🎯 Key Features

### 1. **Unified Interface**
- **Single Command**: One command handles all scenarios (single/multiple exercises)
- **Multiple Parameters**: Use `-e 1 -e 3 -e 5` for multiple exercises
- **Comprehensive Processing**: Always processes questions + screenshots + images

### 2. **Automatic Exercise Discovery**
- **Hidden Exercise Detection**: Automatically reveals hidden exercises by clicking "MOSTRA ALTRE" buttons
- **Complete Processing**: Processes all 57 exercises when using `--all`
- **Smart Navigation**: Handles exercise list navigation and recovery

### 3. **Comprehensive Logging**
- **Per-Exercise Logs**: Detailed logs in `/data/{exercise_number}/logs/`
- **Timestamped Entries**: All actions logged with timestamps
- **Error Tracking**: Complete audit trail of processing activities

### 4. **Robust Error Handling**
- **Recovery Logic**: Attempts to recover and continue on failures
- **Detailed Reporting**: Specific error context for debugging
- **Graceful Degradation**: Continues processing even if individual exercises fail

## 🚀 Usage

### Basic Usage

```bash
# Process single exercise
python question_downloader.py -e 1

# Process multiple exercises
python question_downloader.py -e 1 -e 3 -e 5

# Process all exercises (automatically reveals hidden ones)
python question_downloader.py --all

# Run in headless mode
python question_downloader.py -e 1 --headless

# Skip login (for testing)
python question_downloader.py -e 1 --no-login
```

### Advanced Options

```bash
# Custom configuration file
python question_downloader.py -e 1 --config my_config.json

# Disable content validation
python question_downloader.py -e 1 --no-validate-content

# Custom URL
python question_downloader.py -e 1 --url "https://custom-url.com"
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--exercises` | `-e` | Exercise numbers (use multiple times) | Required |
| `--all` | | Process all exercises | False |
| `--url` | `-u` | Exercise list URL | Default Zanichelli URL |
| `--no-login` | | Skip login process | False |
| `--headless` | | Run browser in headless mode | False |
| `--validate-content` | | Validate extracted content quality | True |
| `--config` | `-c` | Configuration file path | config.json |

## 📋 Configuration

Copy [`config.json.template`](config.json.template) to `config.json` and fill in your credentials:

```json
{
  "credentials": {
    "username": "your_email@example.com",
    "password": "your_password"
  },
  "settings": {
    "headless": false,
    "timeout": 30000,
    "screenshot_delay": 2000,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "use_state_persistence": true,
    "state_file": "browser_state.json"
  }
}
```

## 🔧 Module Documentation

### Core Orchestrator

#### [`ZanichelliExerciseAutomator`](modules/automator.py)
Main orchestrator class that coordinates all automation activities.

**Key Methods:**
- `initialize(headless=False)` - Initialize browser and components
- `process_multiple_exercises(url, exercise_indices, ...)` - Unified processing method
- `navigate_to_exercise_list(url)` - Navigate to exercise page
- `perform_login(force_login=False)` - Handle login with session persistence

**Usage:**
```python
async with ZanichelliExerciseAutomator() as automator:
    await automator.initialize(headless=True)
    results = await automator.process_multiple_exercises(
        url="https://exercise-url.com",
        exercise_indices=[0, 2, 4],  # 0-based indices
        validate_content=True
    )
```

### Browser Automation

#### [`BrowserManager`](modules/browser/browser_manager.py)
Manages browser lifecycle, navigation, and screenshots.

**Key Methods:**
- `setup_browser(**config)` - Initialize Playwright browser
- `navigate_to_url(url)` - Navigate to URL with error handling
- `take_screenshot(path, full_page=True)` - Capture screenshots
- `save_state(file_path)` - Save browser session state
- `cleanup()` - Clean up browser resources

#### [`SelectorStrategies`](modules/browser/selectors.py)
Centralized repository of CSS selectors with fallback strategies.

**Key Methods:**
- `get_selectors(selector_type)` - Get selectors for specific elements
- `create_data_index_selector(index)` - Create data-index based selectors

**Selector Types:**
- `EXERCISE_CARDS` - Exercise card elements
- `ANTEPRIMA_BUTTON` - Preview buttons
- `SVOLGI_BUTTON` - Start exercise buttons
- `INIZIA_BUTTON` - Begin buttons
- `NEXT_QUESTION_NAVIGATION` - Question navigation
- `TERMINA_PROVA_BUTTON` - Finish test buttons

#### [`InteractionHandler`](modules/browser/interactions.py)
Common interaction patterns with retry logic.

**Key Methods:**
- `click_with_strategies(selectors, timeout, description)` - Multi-strategy clicking
- `fill_form_field(selectors, value, description)` - Form field filling
- `wait_for_navigation_or_timeout(timeout)` - Navigation waiting

### Content Processing

#### [`ContentExtractor`](modules/content/extractor.py)
Extracts question content, images, and metadata from pages.

**Key Methods:**
- `extract_question_content(question_number)` - Extract question HTML and text
- `detect_question_images()` - Find images in current question
- `get_exercise_info(exercise_index)` - Get exercise metadata

#### [`ContentProcessor`](modules/content/processor.py)
Processes question numbers and navigation state.

**Key Methods:**
- `get_current_question_number()` - Get current question number (1-based)
- `get_total_questions()` - Get total number of questions
- `is_last_question()` - Check if current question is the last one

#### [`ContentValidator`](modules/content/validator.py)
Validates content quality with scoring system.

**Key Methods:**
- `validate_question_content(content)` - Validate extracted content
- `calculate_quality_score(content)` - Calculate 0-100 quality score
- `detect_content_type(content)` - Identify question type

**Validation Output:**
```python
{
    'is_valid': True,
    'quality_score': 85,
    'confidence': 92.5,
    'content_type': 'multiple_choice_multiple',
    'issues': [],
    'warnings': ['Content is quite short']
}
```

### File Management

#### [`FileManager`](modules/files/manager.py)
Handles directory structure, HTML generation, and file operations.

**Key Methods:**
- `create_exercise_directories(exercise_number)` - Create directory structure
- `get_screenshot_path(question_number, exercise_number)` - Get screenshot file path
- `save_html_content(html, question_number, exercise_number, title)` - Save HTML files
- `get_exercise_directories(exercise_number)` - Get directory paths

**Directory Structure:**
```
data/{exercise_number}/
├── imgs/           # Downloaded images
├── raw/            # Screenshots and HTML
└── logs/           # Processing logs
```

#### [`ContentDownloader`](modules/files/downloader.py)
Async image downloading with filtering and optimization.

**Key Methods:**
- `download_multiple_images(image_info_list, question_number, output_dir)` - Batch download
- `filter_content_images(images)` - Filter out UI elements
- `normalize_image_url(src, base_url)` - Normalize image URLs

### Workflows

#### [`LoginWorkflow`](modules/workflows/login.py)
Complete login process with error handling and session persistence.

**Key Methods:**
- `perform_complete_login(force_login=False)` - Full login workflow
- `is_already_logged_in()` - Check login status
- `handle_login_form()` - Fill and submit login form

#### [`NavigationWorkflow`](modules/workflows/navigation.py)
Exercise and question navigation with hidden exercise revelation.

**Key Methods:**
- `get_exercise_cards()` - Get all exercise cards (reveals hidden ones)
- `click_anteprima_button(exercise_index)` - Click preview button
- `navigate_to_next_question()` - Navigate between questions
- `_reveal_all_exercises()` - Automatically reveal hidden exercises

**Hidden Exercise Handling:**
- Automatically detects "MOSTRA ALTRE" buttons
- Clicks to reveal all hidden exercises
- Supports multiple languages and button variations
- Prevents infinite loops with safety limits

#### [`QuestionProcessorWorkflow`](modules/workflows/question_processor.py)
End-to-end question processing workflow.

**Key Methods:**
- `process_all_questions_in_exercise(exercise_number, validate_content=True)` - Process all questions
- `process_single_question(question_number, exercise_number, validate_content=True)` - Process one question

**Processing Steps:**
1. Take screenshot of question
2. Extract question content
3. Validate content quality
4. Save HTML content
5. Process and download images
6. Navigate to next question

### Configuration

#### [`ConfigManager`](modules/config/manager.py)
Configuration loading, validation, and management.

**Key Methods:**
- `load_config()` - Load and validate configuration
- `get_browser_config()` - Get browser-specific settings
- `get_credentials()` - Get login credentials
- `use_state_persistence()` - Check if state persistence is enabled

## 📊 Output Structure

```
data/
└── {exercise_number}/
    ├── imgs/                    # Downloaded question images
    │   ├── 1.jpg               # Question 1 image
    │   ├── 2_1.png             # Question 2, image 1
    │   └── 2_2.jpg             # Question 2, image 2
    ├── raw/                     # Screenshots and HTML content
    │   ├── 1.png               # Question 1 screenshot
    │   ├── 1.html              # Question 1 HTML content
    │   ├── 2.png               # Question 2 screenshot
    │   └── 2.html              # Question 2 HTML content
    └── logs/                    # Processing logs
        └── exercise_{number}_{timestamp}.log
```

## 📝 Log Files

Each exercise generates detailed logs in `/data/{exercise_number}/logs/`:

```
[2024-10-02 10:30:15] Exercise 1 processing started
[2024-10-02 10:30:16] Successfully started exercise 1
[2024-10-02 10:30:18] Question processing completed:
[2024-10-02 10:30:18]   Questions processed: 10
[2024-10-02 10:30:18]   Questions successful: 9
[2024-10-02 10:30:18]   Questions failed: 1
[2024-10-02 10:30:19] Successfully clicked TERMINA PROVA button
[2024-10-02 10:30:20] Exercise 1 completed successfully
```

## 🔍 Content Validation

The system includes comprehensive content validation with detailed reporting:

**Quality Metrics:**
- **Quality Score**: 0-100 based on content indicators
- **Confidence Rating**: 0-100% confidence in extraction accuracy
- **Issue Detection**: Identifies cookie banners, UI elements, etc.
- **Content Type Detection**: Multiple choice, essay, image-based, etc.

**Example Output:**
```
Status: ✓ VALID
Quality Score: 85/100
Confidence: 92.5%
Content Type: multiple_choice_multiple
Issues (0): None
Warnings (1):
  - Content is quite short (less than 50 characters)
```

## 🚦 Error Handling

**Multi-Level Error Handling:**
- **Exercise Level**: Continues with next exercise if one fails
- **Question Level**: Attempts to continue with next question on errors
- **Navigation Level**: Recovery mechanisms for navigation failures
- **Network Level**: Retry logic for network timeouts

**Error Reporting:**
- Detailed error messages with context
- Error categorization (navigation, content, network)
- Suggested troubleshooting steps
- Complete error logs in log files

## 🧪 Programmatic Usage

```python
import asyncio
from modules import ZanichelliExerciseAutomator

async def process_exercises():
    async with ZanichelliExerciseAutomator() as automator:
        # Initialize with custom settings
        await automator.initialize(headless=True)
        
        # Process multiple exercises
        results = await automator.process_multiple_exercises(
            url="https://esercizi.zanichelli.it/argomento/...",
            exercise_indices=[0, 2, 4],  # 0-based indices for exercises 1, 3, 5
            login_required=True,
            validate_content=True
        )
        
        # Check results
        print(f"Exercises processed: {results['exercises_processed']}")
        print(f"Questions processed: {results['total_questions_processed']}")
        print(f"Success rate: {results['exercises_successful']/results['exercises_processed']*100:.1f}%")

# Run the automation
asyncio.run(process_exercises())
```

## 📈 Performance & Statistics

**Processing Statistics:**
- Exercise success/failure rates
- Question processing metrics
- File creation counts (screenshots, HTML, images)
- Processing time per exercise
- Error categorization and frequency

**Example Statistics Output:**
```
✅ Processing completed successfully
Exercises processed: 3
Exercises successful: 3
Exercises failed: 0
Exercise success rate: 100.0%

Total questions processed: 28
Total questions successful: 26
Total questions failed: 2
Question success rate: 92.9%
Average questions per exercise: 9.3

Files saved in:
- Screenshots: /data/[exercise_number]/raw/
- Images: /data/[exercise_number]/imgs/
- HTML content: /data/[exercise_number]/raw/
```

## 🛠️ Development & Extension

### Adding New Selectors
Add to [`SelectorStrategies`](modules/browser/selectors.py):
```python
def get_selectors(self, selector_type: str) -> List[str]:
    selectors = {
        'NEW_ELEMENT': [
            'css-selector-1',
            'css-selector-2',
            'fallback-selector'
        ]
    }
    return selectors.get(selector_type, [])
```

### Creating New Workflows
Create in [`modules/workflows/`](modules/workflows/):
```python
class NewWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.interactions = InteractionHandler(page)
    
    async def perform_workflow(self) -> bool:
        # Implementation
        return True
```

### Extending Content Validation
Enhance [`ContentValidator`](modules/content/validator.py):
```python
def detect_new_content_type(self, content: Dict[str, Any]) -> str:
    # Add new content type detection logic
    return 'new_content_type'
```

## 📝 Requirements

- **Python**: 3.8+
- **Dependencies**: playwright, aiohttp, aiofiles, click

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

**requirements.txt:**
```
playwright>=1.40.0
aiohttp>=3.8.0
aiofiles>=23.0.0
click>=8.0.0
```

## 🔧 Troubleshooting

### Common Issues

**1. Exercise Not Found**
```bash
# Check if exercises are hidden
python question_downloader.py --all  # This will reveal hidden exercises
```

**2. Login Failures**
```bash
# Check credentials in config.json
# Try without headless mode to see login process
python question_downloader.py -e 1 --no-headless
```

**3. Navigation Issues**
```bash
# Check logs in /data/{exercise_number}/logs/
# Try with single exercise first
python question_downloader.py -e 1
```

**4. Content Extraction Issues**
```bash
# Disable content validation to continue processing
python question_downloader.py -e 1 --no-validate-content
```

### Debug Mode

Enable detailed logging by checking the log files in `/data/{exercise_number}/logs/` for:
- Exercise startup status
- Question processing details
- Navigation success/failures
- Error messages with timestamps

## 📄 License

This project maintains the same license as the original codebase.