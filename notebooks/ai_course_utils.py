# ai_course_utils.py
# Universal utilities for all notebooks - Model-agnostic implementation
# Version 2.0 - Data files as user inputs, not environment variables

import os
import pandas as pd
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv


# Load .env from current directory or parent directory
load_dotenv()  # Try current directory
if not os.getenv('LLM_PROVIDER'):  # If not loaded, try parent
    load_dotenv('../.env')

# ============================================================================
# UNIVERSAL LLM LOADER - Works with ANY provider
# ============================================================================

def load_llm_from_env():
    """
    Load LLM based on environment configuration.
    Supports: OpenAI, Gemini, Mistral, Claude, etc.
    
    Environment variables (API Keys only):
    - LLM_PROVIDER: openai, google-genai, mistralai, anthropic
    - LLM_MODEL: model name for the provider
    - LLM_TEMPERATURE: temperature setting (default 0.7)
    - OPENAI_API_KEY, GOOGLE_API_KEY, etc.
    """
    load_dotenv()
    
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("LLM_MODEL")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    print(f"Loading LLM: {provider} / {model}")
    
    # OpenAI (ChatGPT, GPT-4, etc.)
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            temperature=temperature
        )
    
    # Google Gemini
    elif provider in ["google", "google-genai", "gemini"]:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model or "gemini-pro",
            temperature=temperature
        )
    
    # Mistral AI
    elif provider == "mistralai":
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=model or "mistral-small-latest",
            temperature=temperature
        )
    
    # Anthropic Claude
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "claude-3-sonnet-20240229",
            temperature=temperature
        )
    
    # Default fallback
    else:
        print(f"WARNING: Unknown provider '{provider}', defaulting to OpenAI")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            temperature=temperature
        )

# ============================================================================
# USE CASE CONFIGURATION LOADER - Takes file path as parameter
# ============================================================================

def load_use_case_config(filepath: str) -> Dict[str, str]:
    """
    Load use case configuration from Excel file.
    
    Expected columns: 'Prompt Type', 'Prompt Value'
    
    Args:
        filepath: Path to use case Excel file (user-provided)
        
    Returns:
        Dictionary mapping prompt types to values
        
    Example:
        config = load_use_case_config("use_case_Movie_Recommendation.xlsx")
        system_prompt = config.get("agent_prompt")
    """
    try:
        df = pd.read_excel(filepath)
        
        config = {}
        for _, row in df.iterrows():
            prompt_type = row['Prompt Type']
            prompt_value = row['Prompt Value']
            config[prompt_type] = prompt_value
        
        print(f"Use case loaded: {filepath}")
        print(f"  Components: {', '.join(config.keys())}")
        
        return config
        
    except FileNotFoundError:
        print(f"ERROR: Use case file not found: {filepath}")
        print("Please provide a valid file path")
        raise
    except Exception as e:
        print(f"ERROR: Error loading use case: {str(e)}")
        raise

# ============================================================================
# TAXONOMY LOADER - Takes file path as parameter
# ============================================================================

def load_taxonomy_from_excel(filepath: str) -> Dict:
    """
    Load movie taxonomy from Excel file.
    
    Expected columns: Genre Name, Genre Description, Movies Included, 
                      Movies Excluded, Recommend using guidelines
    
    Args:
        filepath: Path to taxonomy Excel file (user-provided)
        
    Returns:
        Dictionary with genre information
        
    Example:
        taxonomy = load_taxonomy_from_excel("Movie_Recommendation_Taxonomy_File.xlsx")
        genres = list(taxonomy.keys())
    """
    try:
        df = pd.read_excel(filepath)
        
        taxonomy = {}
        for _, row in df.iterrows():
            genre_name = row['Genre Name']
            taxonomy[genre_name] = {
                'description': row.get('Genre Description', ''),
                'included': row.get('Movies Included', ''),
                'excluded': row.get('Movies Excluded', ''),
                'guidelines': row.get('Recommend using guidelines', '')
            }
        
        print(f"Taxonomy loaded: {filepath}")
        print(f"  Genres: {len(taxonomy)} ({', '.join(list(taxonomy.keys())[:3])}...)")
        
        return taxonomy
        
    except FileNotFoundError:
        print(f"ERROR: Taxonomy file not found: {filepath}")
        print("Please provide a valid file path")
        raise
    except Exception as e:
        print(f"ERROR: Error loading taxonomy: {str(e)}")
        raise

# ============================================================================
# PDF LOADER FOR RAG - Takes file path as parameter
# ============================================================================

def load_pdf_for_rag(filepath: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Load and process PDF file for RAG.
    
    Args:
        filepath: Path to PDF file (user-provided)
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        
    Returns:
        Tuple of (documents, vectorstore, retriever)
        
    Example:
        docs, vectorstore, retriever = load_pdf_for_rag("Oscars_2026.pdf")
        results = retriever.invoke("Who won Best Picture?")
    """
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        
        print(f"Loading PDF: {filepath}")
        
        # Load PDF
        loader = PyPDFLoader(filepath)
        documents = loader.load()
        print(f"  Loaded {len(documents)} pages")
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        splits = text_splitter.split_documents(documents)
        print(f"  Created {len(splits)} chunks")
        
        # Create vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(splits, embeddings)
        print(f"  Vector store created")
        
        # Create retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        print(f"  Retriever ready (top 3 results)")
        
        return documents, vectorstore, retriever
        
    except FileNotFoundError:
        print(f"ERROR: PDF file not found: {filepath}")
        print("Please provide a valid file path")
        raise
    except Exception as e:
        print(f"ERROR: Error loading PDF: {str(e)}")
        raise

# ============================================================================
# FILE UPLOAD HELPER (for Streamlit integration)
# ============================================================================

def save_uploaded_file(uploaded_file, destination_folder: str = "uploaded_files") -> str:
    """
    Save an uploaded file (from Streamlit or other UI) to disk.
    
    Args:
        uploaded_file: File object (e.g., from st.file_uploader)
        destination_folder: Folder to save files
        
    Returns:
        Path to saved file
        
    Example (in Streamlit):
        uploaded = st.file_uploader("Upload use case")
        if uploaded:
            filepath = save_uploaded_file(uploaded)
            config = load_use_case_config(filepath)
    """
    # Create folder if doesn't exist
    os.makedirs(destination_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(destination_folder, uploaded_file.name)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    print(f"File saved: {filepath}")
    return filepath

# ============================================================================
# CONFIGURATION DISPLAY
# ============================================================================

def display_config():
    """Display current API configuration from .env file."""
    load_dotenv()
    
    print("=" * 70)
    print("API CONFIGURATION (.env file)")
    print("=" * 70)
    print(f"LLM Provider:    {os.getenv('LLM_PROVIDER', 'openai')}")
    print(f"LLM Model:       {os.getenv('LLM_MODEL', 'gpt-4o-mini')}")
    print(f"Temperature:     {os.getenv('LLM_TEMPERATURE', '0.7')}")
    print()
    print("API Keys Status:")
    
    keys = {
        "OPENAI_API_KEY": "OpenAI",
        "GOOGLE_API_KEY": "Google",
        "MISTRAL_API_KEY": "Mistral",
        "ANTHROPIC_API_KEY": "Anthropic",
        "SERPER_API_KEY": "Serper (Web Search)"
    }
    
    for key, name in keys.items():
        status = "Set" if os.getenv(key) else "Not set"
        print(f"  {name:20} {status}")
    
    print("=" * 70)
    print("\nData Files:")
    print("  Provide file paths as function parameters")
    print("  Example: load_use_case_config('your_file.xlsx')")
    print("=" * 70)

# ============================================================================
# PROVIDER TESTING
# ============================================================================

def test_llm_provider(test_query: str = "Say hello in one sentence"):
    """
    Test the current LLM provider configuration.
    
    Args:
        test_query: Query to test with
    """
    try:
        llm = load_llm_from_env()
        response = llm.invoke(test_query)
        
        print("\nLLM Test Successful!")
        print(f"Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"\nERROR: LLM Test Failed: {str(e)}")
        return False

# ============================================================================
# SAMPLE .ENV FILE GENERATOR
# ============================================================================

def create_sample_env_file(filepath: str = ".env.sample"):
    """Create a sample .env file with all API configuration options."""
    
    sample_content = """# AI Course Configuration File
# Copy this to .env and fill in your API keys

# ============================================
# LLM Provider Configuration
# ============================================
# Options: openai, google-genai, mistralai, anthropic
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7

# ============================================
# API Keys (only need the ones you'll use)
# ============================================

# OpenAI (ChatGPT, GPT-4)
OPENAI_API_KEY=sk-proj-...

# Google (Gemini)
# GOOGLE_API_KEY=...

# Mistral AI
# MISTRAL_API_KEY=...

# Anthropic (Claude)
# ANTHROPIC_API_KEY=...

# Google Serper (Web Search)
SERPER_API_KEY=...

# ============================================
# NOTE: Data Files Not Here
# ============================================
# Data files (use case, taxonomy, PDFs) are provided as:
# - Function parameters in notebooks
# - File uploads in Streamlit UI
# - Direct file paths when running locally
#
# Examples:
#   load_use_case_config("path/to/use_case.xlsx")
#   load_taxonomy_from_excel("path/to/taxonomy.xlsx")
#   load_pdf_for_rag("path/to/document.pdf")
"""
    
    with open(filepath, 'w') as f:
        f.write(sample_content)
    
    print(f"Sample environment file created: {filepath}")
    print("  Copy this to .env and add your API keys")

# ============================================================================
# QUICK SETUP HELPER
# ============================================================================

def quick_setup():
    """Quick setup helper for new users."""
    print("\n" + "=" * 70)
    print("AI COURSE - QUICK SETUP")
    print("=" * 70)
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("\nWARNING: No .env file found!")
        create_sample_env_file()
        print("\nNext steps:")
        print("  1. Copy .env.sample to .env")
        print("  2. Add your API keys to .env")
        print("  3. Run this setup again")
        return False
    
    # Display config
    display_config()
    
    # Test LLM
    print("\nTesting LLM connection...")
    success = test_llm_provider()
    
    if success:
        print("\nAPI Setup complete!")
        print("\nData Files:")
        print("  Provide file paths when calling functions:")
        print("    config = load_use_case_config('use_case.xlsx')")
        print("    taxonomy = load_taxonomy_from_excel('taxonomy.xlsx')")
        print("    docs, vs, retriever = load_pdf_for_rag('document.pdf')")
        return True
    else:
        print("\nERROR: Setup incomplete. Please check your .env configuration.")
        return False

# ============================================================================
# STREAMLIT HELPERS
# ============================================================================

def get_streamlit_file_uploader_config():
    """
    Get configuration for Streamlit file uploaders.
    
    Returns:
        Dictionary with file uploader configurations
        
    Example (in Streamlit):
        config = get_streamlit_file_uploader_config()
        use_case_file = st.file_uploader(**config['use_case'])
    """
    return {
        'use_case': {
            'label': "Upload Use Case File",
            'type': ['xlsx'],
            'help': "Excel file with columns: Prompt Type, Prompt Value"
        },
        'taxonomy': {
            'label': "Upload Taxonomy File",
            'type': ['xlsx'],
            'help': "Excel file with genre classifications"
        },
        'pdf': {
            'label': "Upload PDF Document",
            'type': ['pdf'],
            'help': "PDF file for RAG (e.g., Oscars data, movie guides)"
        }
    }

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("AI Course Utilities Module v2.0")
    print("=" * 70)
    print("\nAPI Keys: Configured in .env file")
    print("Data Files: Provided as function parameters\n")
    print("\nUsage Examples:")
    print("\n1. Load LLM (from .env):")
    print("   from ai_course_utils import load_llm_from_env")
    print("   llm = load_llm_from_env()")
    print("\n2. Load Use Case (file path):")
    print("   from ai_course_utils import load_use_case_config")
    print("   config = load_use_case_config('use_case_Movie_Recommendation.xlsx')")
    print("\n3. Load Taxonomy (file path):")
    print("   from ai_course_utils import load_taxonomy_from_excel")
    print("   taxonomy = load_taxonomy_from_excel('Movie_Recommendation_Taxonomy_File.xlsx')")
    print("\n4. Load PDF for RAG (file path):")
    print("   from ai_course_utils import load_pdf_for_rag")
    print("   docs, vectorstore, retriever = load_pdf_for_rag('The_98th_Academy_Awards___2026.pdf')")
    print("\n5. Quick Setup:")
    print("   from ai_course_utils import quick_setup")
    print("   quick_setup()")
    print("\n" + "=" * 70)
