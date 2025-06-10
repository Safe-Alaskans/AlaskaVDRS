# Alaska VDRS AI Modernization Project

## Purpose

Fine-tune an LLM to assist in generating incident narratives based on multiple input documents that are submitted to the National Violent Death Reporting System (NVDRS) Database hosted by the Center for Disease Control (CDC). The LLM is locally hosted on-premises and accessed through a simple web interface that facilitates the collection of all files within a "case" required to craft a narrative. After uploading documents, the fine-tuned LLM generates a draft narrative for professional review that can be rated, re-generated with feedback, and used by trained abstractors to complete NVDRS submissions.

## Project Background

When someone dies a violent death in Alaska, numerous government processes report the event to Alaska State and Federal agencies. This includes summarizing various statistics from law enforcement reports, medical examination data, and up to 35 other documents to be abstracted by an Alaska Violent Death Reporting System (Alaska VDRS) professional.

The abstractor collects ~800 statistics to be properly coded and submitted into the National Violent Death Reporting System (NVDRS) database through a CDC web portal. This process is currently done manually and is very labor intensive, resulting in delayed reporting and reduced opportunities for government response to violent death crisis.

This project modernizes Alaska VDRS reporting utilizing Large Language Models (LLMs) to generate incident narratives based on a variety of input documents, improving the accuracy and speed of NVDRS reporting. Output narratives are always reviewed by trained professionals.

**Document specifications:**

- Document length: 1-15 pages per document (4 page average)
- Number of documents: 3-8 documents, up to ~35 unique types

## Quick Start

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU (recommended)

### Installation

1. **Start all services:**

   ```
   chmod +x entrypoint.sh
   docker-compose up -d
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Ollama API: http://localhost:11434

## Architecture

- **Frontend**: Web interface for document upload and narrative generation
- **Backend**: Flask API server handling file processing and LLM communication
- **Model**: Fine-tuned Llama 3.1 8B model for NVDRS narrative generation

## Model Information

**Fine-tuned Model**: [SafeAlaskans/Llama-3.1-8B-Chat-NVDRS-NarrativeGeneration-GGUF](https://huggingface.co/SafeAlaskans/Llama-3.1-8B-Chat-NVDRS-NarrativeGeneration-GGUF)

- Specialized for NVDRS narrative generation
- Format: GGUF (optimized for local deployment)

## Project Structure

```
alaska-vdrs-ai/
├── frontend/                 # Web interface
├── backend/                  # Flask API server
├── data-processing-tools/    # Document processing utilities
├── model_tuning_workspace/   # Model training and fine-tuning
├── tests/                    # Test suites
docker-compose.yml            # Service orchestration
entrypoint.sh                 # ollama setup from huggingface
README.md                     # This file
```
