# Training

## Multi-GPU vs single GPU - LoRA training
As we will be deploying our system on 2x 4090's, it could be interesting to see if we could effectively train on them both.
This section aims to summarise the research to see if this is possible.

### TLDR
Due to our relatively large context sizes, we will not be able to train on a single 4090.
Due to the potential complexity and experimentation required to get multi-GPU training working, it is not worth the time it would take at this stage.
Therefore to begin, we will train on a single cloud GPU (Runpod) which has more vRAM. We will use the 2x 4090's for fast inference ob vLLM. 

### Multi-GPU research
 - Unfortunately, Ollama doesn't support multi-GPU training unless you pay for the enterprise version.
 - Axolotl does support multi-GPU training with both DeepSpeed and FDSP + QLoRA. Deepspeed for QLoRA is not well documented and there seems to be Github issues, so not sure worth it. I also believe FDSP has some stability issues.
   - If using DeepSpeed, ZeRO-2 is the best option for us as it has a good balance between speed and memory usage. 
 - I believe the best option is to use Axolotl, but it may not be worth the effort to get multi-GPU training working.

### Single GPU research
 - Token usage based upon evals
   - Each input doc is around 1000 tokens. For now therefore the input is 3000 tokens as the evals have 3 files.
   - Each output narrative is around 300-400 tokens, but for more complex cases we can expect up to 700 tokens.
   - Total tokens per datapoint therefore is 3000 + 700 = 3700 tokens. With a buffer we will land around 4000 tokens.
     - *If* we find more docs are going to be input by the abstractors in the future, then we should train accordingly. 
 - Based upon online calculators, we will not be able to train on a single 4090 with this token size.
 - Perhaps a A6000 (48GB vRAM) would be sufficient.

## Providers researched
 - Unsloth - Best performance
 - Axolotl