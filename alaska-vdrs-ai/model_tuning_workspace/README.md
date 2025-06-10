# Model Tuning Workspace

## Setup environment

### Venv
Ensure you are inside the root directory before running the following commands.
1. Install `virtualenv` package
```bash
python -m venv .venv
```
2. Activate the virtual environment
```bash
source .venv/bin/activate 
# or
.venv\Scripts\activate     # Windows
```
3. Install required packages
```bash
pip install -r requirements.txt
```

### Environment variables
Take a look at the `.env.example` file to see what environment variables are required. 
Create a `.env` file in the root directory and fill in the required values.


## Backlog

The below items are known to be required but have not been implemented yet due to time constraints.

 - Potential for extraction step to be added in before narrative generation step
   - This would involve extracting key information from the source documents before generating the narrative.
   - This allows the narrative generation to have a very clean context to work with, maximising the quality of the narratives.
 - More eval `Validators`. In order of importance (most important first):
   - Circumstance(s) validator - Ensures all key info about circumstance(s) is included
   - Chronological order validator - Ensures events are in chronological order
   - Abbreviation validator - Ensures no abbreviations are used other than V, S, V/S
   - No copying validator - Ensures no copying word for word from source docs
   - Physical/mental health validator - Ensures physical/mental health issues are only mentioned if relevant
   - Irrelevant circumstances validator - Ensures irrelevant circumstances are not included
   - Writing style validator - Ensures writing style is concise and informative
   - No toxicology/autopsy validator - Ensures no in-depth toxicology/autopsy reports are included
   - To be ranked (because discovered after initial ranking above):
     - Timings validator - Ensures no specific times of day are included
     - Stating in the negative validator - Ensures model does not state things in the negative as this is usually irrelevant
