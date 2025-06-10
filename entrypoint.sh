#!/bin/bash

echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to be ready..."
sleep 15

echo "Pulling SafeAlaskans NVDRS model from HuggingFace..."
ollama pull SafeAlaskans/Llama-3.1-8B-Chat-NVDRS-NarrativeGeneration-GGUF:latest

echo "Creating nvdrs-model alias..."
ollama create nvdrs-model -f - <<EOF
FROM SafeAlaskans/Llama-3.1-8B-Chat-NVDRS-NarrativeGeneration-GGUF:latest
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
EOF

echo "Model setup complete! Available at localhost:11434"
ollama list

wait $OLLAMA_PID