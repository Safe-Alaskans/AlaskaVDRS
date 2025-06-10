# Technical planning for evals

## How evals will work
We will have a test suite written in Python. 

Each eval in the suite will:
- Have an input which will be sent to the model we are evaluating.
- Then that model will provide its output.
- A set of specialised validators which will check the output of the model against what is expected.
- A pass/fail result will be returned based on the validators.

Due to the text-based nature of the narratives, most validators will be a prompted LLM (Using LLM-as-a-judge framework).
Therefore, we will create multiple validators/judges which we can use for different aspects of the narratives.
For example, we will have a judge for checking if the narrative contains PII, another checking if the narrative contains a specific party, and another checking if the narrative contains a specific weapon.
**All attempts will be made to keep the judges as general as possible to allow for reuse across multiple evals.**

## LLM Judge requirements
- Due to the nature of the narratives, we will need an LLM which is not censored to the point it will not answer prompts containing traumatic content.
- Also, we will need a more powerful LLM to run the evaluations on due to the complexity of the narratives.

## Eval specific notes

### PII evals research
Unfortunately tools such as [presidio](https://github.com/microsoft/presidio/) will not provide us all the PII we need to detect.
Our PII requirements vs what presidio can provide are as follows:
 - Names ✅
 - Dates (including DOBs) ✅
 - Locations
   - Cities ✅
   - Street addresses ❌
 - Organisation names ❌

Therefore, we will need to create our own PII detection judge.

- [ ] Continue planning different validators, remaining as general as possible, and begin implementation.
- [ ] Discover an LLM which can handle the content of the narratives.