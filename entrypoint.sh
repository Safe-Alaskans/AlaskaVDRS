#!/bin/bash

echo "Starting Ollama server..."
ollama serve &

echo "Waiting for Ollama to be ready..."
sleep 15

ollama run hf.co/SafeAlaskans/Llama-3.1-8B-Chat-NVDRS-NarrativeGeneration-GGUF:latest