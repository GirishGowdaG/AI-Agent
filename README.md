# Resume Screening Agent

AI-powered resume screening tool using Google ADK for multi-agent orchestration and Gemini API for intelligent resume analysis.

## Features

- 📄 Multi-PDF resume upload (up to 50 files)
- 📝 Job description text input
- 🤖 4 Specialized AI Agents: Parser → Analyzer → Matcher → Ranker
- 📊 Real-time processing with progress tracking
- 📈 Ranked results table with match explanations
- 🎯 Skill gap analysis and strengths highlighting
- 📥 Export results as CSV/PDF

## Quick Start

### 1. Get API Key

Get your free Gemini API key from: https://ai.google.dev/gemini-api

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Copy the example secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit and add your API key
nano .streamlit/secrets.toml
```

### 4. Run the Application

```bash
streamlit run app.py
```

## Architecture

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Streamlit   │◄──▶│   ADK Runner    │◄──▶│ Gemini API   │
│   Frontend   │    │  (Orchestrator) │    │ (1.5-flash)  │
└──────────────┘    └─────────────────┘    └──────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ Parser  │      │ Matcher │      │ Ranker  │
    │ Agent   │      │ Agent   │      │ Agent   │
    └─────────┘      └─────────┘      └─────────┘
```

## Agent Pipeline

1. **Parser Agent**: Extracts name, skills, experience, education from resume PDFs
2. **Analyzer Agent**: Extracts required skills/experience from job description
3. **Matcher Agent**: Computes semantic similarity scores (40% skills, 40% experience, 20% education)
4. **Ranker Agent**: Generates final ranking with explanations

## Project Structure

```
├── app.py                 # Streamlit application
├── src/
│   ├── agents/           # AI agents
│   │   ├── parser.py     # Resume parsing
│   │   ├── analyzer.py   # Job description analysis
│   │   ├── matcher.py    # Candidate matching
│   │   └── ranker.py     # Candidate ranking
│   ├── models/           # Data models
│   │   ├── resume.py
│   │   ├── job.py
│   │   ├── match.py
│   │   └── candidate.py
│   ├── utils/            # Utilities
│   │   ├── serialization.py
│   │   ├── validation.py
│   │   ├── export.py
│   │   └── pdf_extractor.py
│   ├── runner.py         # Agent orchestration
│   └── config.py         # Configuration
├── tests/
│   ├── property/         # Property-based tests
│   └── unit/             # Unit tests
└── requirements.txt
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run property-based tests only
pytest tests/property/ -v

# Run unit tests only
pytest tests/unit/ -v
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Streamlit | Interactive UI |
| Agent Framework | Google ADK | Multi-agent orchestration |
| AI Models | Gemini 1.5 Flash | Resume parsing + semantic matching |
| PDF Handling | PyMuPDF | Text extraction |
| Testing | Hypothesis | Property-based testing |
| Export | pandas, reportlab | CSV/PDF generation |

## License

MIT License
