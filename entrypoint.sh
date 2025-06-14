#!/bin/bash

echo "Starting Ollama server..."
ollama serve &
SERVE_PID=$!

echo "Waiting for Ollama to be ready..."
sleep 15

echo "Pulling model if not already available..."
ollama pull hf.co/SafeAlaskans/Llama-3.1-8B-Chat-NVDRS-NarrativeGeneration-GGUF:latest

echo "Ollama is ready with the model loaded"

# Keep the container running by waiting for the ollama serve process
wait $SERVE_PID