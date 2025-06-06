# LoRAMaker
## An easy way to generate question-answer pairs from a directory of JSON files.
### Question-answer pairs can then be used for training or as a dataset for a large language model.


## LoRARanker
**SCRIPT PROMPT MUST BE CUSTOMIZED BEFORE USE** _currently configured for SBIR question and answer ranking_
### LoRARanker is a tool designed to rank question-answer pairs extracted from a directory of JSON files. It utilizes the OpenAI API to evaluate and rank each question-answer pair based on their quality and relevance to a given topic or criteria.

### Low ranked questions can then be removed from the dataset as a part of a seperate step.

## LoRASplitter
### LoRASplitter is a tool that loads a JSON file containing ranked question-answer pairs, and then creates a new file with pairs rainked 41 and above (the top 60% of the dataset).
