# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a **Busan Tourism & Multicultural Support Chat Application** built with Python Flet (Flutter web framework). It provides multilingual chat services for tourists and multicultural families living in Busan, South Korea.

### Core Components

- **main.py**: Primary Flet application entry point with multi-page routing and configuration
- **pages/**: Page modules implementing the Flet multi-page architecture
- **rag_utils.py**: RAG (Retrieval-Augmented Generation) utilities with vector databases and language detection
- **cache_manager.py**: Hash-based caching system for PDF embeddings

### Key Features

- **Multilingual Support**: Korean, English, Japanese, Chinese, Vietnamese, French, German, Thai, Tagalog
- **RAG Integration**: Multiple specialized vector databases for different content types
- **Firebase Integration**: Real-time chat with Firebase Realtime Database
- **MBTI Tourism**: Personalized tourism recommendations based on MBTI types
- **Specialized Services**: Waste disposal info, foreign worker safety, Busan food recommendations

## Development Commands

### Running the Application

```bash
# Main application (development mode)
python main.py

# Production mode with Docker
docker build -t buchat .
docker run -p 8000:8000 buchat

# Install dependencies
pip install -r requirements.txt
```

### Data Management

```bash
# Cache management
python cache_manager.py status    # Check cache status
python cache_manager.py rebuild   # Force cache rebuild
python cache_manager.py clear     # Clear all cache

# Vector database creation
python create_multicultural_family_db.py  # Create multicultural family DB
python make_simple_vector_db.py           # Create simple vector DB
```

### Utility Scripts

```bash
# Busan tourism data
python busan_photo_crawler.py     # Crawl Busan photos
python check_gallery_titles.py    # Validate gallery titles

# Country selection utility
python foreign_country_select.py  # Country selection helper
```

## Configuration

### Required Environment Variables

```bash
GEMINI_API_KEY=your_gemini_api_key
MODEL_NAME=gemini-2.0-flash-lite
FIREBASE_DB_URL=your_firebase_database_url
FIREBASE_KEY_JSON=your_firebase_service_account_json
CLOUDTYPE=1  # For production deployment
```

### Configuration Files

- **config.py**: Auto-generated from environment variables on startup
- **config.example.py**: Template for configuration
- **firebase_key.json**: Firebase service account credentials (auto-generated from env)
- **firebase_key.json.example**: Template for Firebase credentials

## Architecture

### Flet Multi-Page Application Architecture

The application follows a functional page-based architecture where each page is implemented as a function that returns Flet UI components:

- **NationalitySelectPage(page, on_select, on_foreign_select, on_back)**: Initial language/nationality selection
- **HomePage(page, lang, on_create, on_find, on_quick, on_change_lang, on_back, on_mbti_tourism)**: Main dashboard with service options
- **CreateRoomPage(page, lang, on_create, on_back)**: Chat room creation interface
- **ChatRoomPage(page, room_id, room_title, user_lang, target_lang, ...)**: Real-time chat interface with AI assistance
- **MBTITourismPage(page, lang, on_back, selected_mbti_value, result_view_value)**: MBTI-based tourism recommendations
- **ForeignCountrySelectPage(page, on_select, on_back)**: Country-specific services

### Page Routing System

The main.py implements a routing system that:
- Maintains page state in memory
- Provides navigation callbacks between pages
- Handles responsive design based on screen size
- Manages language state across pages

### RAG System Architecture

The application uses multiple specialized vector databases:

- **다문화.pkl**: Multicultural family guidance (Korean life guide)
- **외국인근로자.pkl**: Foreign worker safety and legal information
- **부산의맛.pkl**: Busan food and restaurant information

#### Language Detection System

Automatic language detection in `rag_utils.py` using regex patterns for:
- Korean (한글), English, Japanese (ひらがな/カタカナ), Chinese (中文)
- Vietnamese, French, German, Thai, Tagalog patterns
- Returns appropriate language codes for response generation

### Vector Database Caching

Uses MD5 hash-based caching for efficient PDF processing:
- **Cache validation**: Compares file hashes in `cache_info.json` to detect changes
- **Automatic regeneration**: Creates new embeddings when PDFs change
- **Performance optimization**: Skips expensive embedding generation for unchanged files

### Data Sources

- **JSON Data Files**:
  - `부산의맛(2025).json`: Busan restaurant data
  - `택슐랭(2025).json`: Taek-seuling (Korean Michelin) restaurant data
  - `부산광역시_쓰레기처리정보.json`: Waste disposal information
  - `jangmachul.json`, `onyul.json`: Safety information for foreign workers
  - `mbti_recommendations_multilang.json`: MBTI tourism recommendations

## Dependencies

### Core Framework
- **flet**: Main UI framework (Flutter for Python)
- **flet-webview**: WebView integration for enhanced functionality
- **firebase-admin**: Firebase integration for real-time chat

### AI & ML
- **google-generativeai**: Gemini AI integration for chat responses
- **langchain**: LLM framework with RAG capabilities
- **langgraph**: Advanced LLM workflows (optional, graceful fallback)
- **chromadb**: Vector database for embeddings

### Utilities
- **qrcode**: QR code generation for room sharing
- **geocoder**: Location services for local recommendations
- **pypdf**: PDF processing for RAG document ingestion

## Important Notes

### Firebase Integration
- Application gracefully degrades when Firebase is unavailable
- Chat functionality requires proper Firebase configuration
- Database URL and service account credentials are mandatory for chat features

### Model Configuration
- Default model: `gemini-2.0-flash-lite`
- Model can be configured via `MODEL_NAME` environment variable
- API key required for all AI features

### Vector Database Management
- Multiple specialized databases for different content types
- Hash-based caching prevents unnecessary re-processing
- Cache management tools available for debugging and optimization

### Development Patterns
- Each page is a pure function that returns Flet UI components
- State management through callback functions passed between pages
- Responsive design implemented in each page component
- Language state maintained at the application level