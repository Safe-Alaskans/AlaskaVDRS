# Model deployment

This folder contains the necessary files to deploy the model locally. 

## Pre-requisites
- OS: Linux
- Python 3.9 – 3.12
- GPU on the machine

## Local model deployment

### Downloading weights from HuggingFace
To use vLLM to serve the model, we must download a HF model. This can be done on a machine with internet access and then copied to the deployment machine using a USB or other means. 
To do so, we can use the below script:
```
python download_and_save_model.py --hf_model_id {model_id} --output_dir {optional default: ~/.models}
```

### Setting up the model on the deployment machine
Create the dir structure as follows:
```
mkdir -p ~/.models/{model_name}
```

Inside that dir, either pull the model from HF into it or copy the model files into it.
Model files include configs and safetensors. Essentially whatever is in the HF model dir.

As a sanity check, execute:
```
python check_model_location.py --model_dir ~/.models/{model_name}
```

### Serving the model on deployment machine
To serve the model, execute:
- [ ] Need to check about the tokenizer
```
python -m vllm.entrypoints.openai.api_server
--model ~/.models/{model_name}
--host 127.0.0.1
--port 8000
```
