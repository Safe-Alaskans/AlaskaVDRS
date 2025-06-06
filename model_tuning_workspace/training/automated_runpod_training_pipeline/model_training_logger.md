# Model training logger

## v0.3
- Increased synthetic data points to 63
- Left other hyperparams the same
- Took around 4 mins to train on a single A100
- Training loss achieved: 0.262900

### Example Model output:
```
In the morning hours, a 30-year-old female (V) was found unresponsive by her brother after he was informed of her suicidal intentions. V was discovered in her living room on the couch with a shotgun in her possession. V had previously called her brother to tell him of her plans before the discovery. The body was found in a state incompatible with life. V had a medical history of chronic lumbar pain, PTSD, and anxiety. The cause of death was a self-inflicted gunshot wound to the head. The manner of death was classified as suicide. No other circumstances are known.
```
**Analysis:**
Model seems to be improving, I think the synthetic data should provide details on how the weapon was found.
Also, the model does not provide the medical specific injury details here.
Overall though, this seems like a good state based upon the information (info on expected inputs at test time) we have at this time.

## v0.2
Multiple experiments ran on GPU, the below is the best performing model which is labelled and trained as v0.2
- Same DPs as v0.1
- Increased # epochs to 3
- Decreased batches to:
  - `per_device_train_batch_size`=2
  - `gradient_accumulation_steps`=4
- Ran inference model in the same pipeline on GPU.
- Training loss achieved: 0.315800

### Model output:
```
In the morning hours, a 67-year-old non-binary individual (V) was found deceased by paramedics. V was discovered wearing athletic attire in their apartment, which showed signs of a violent altercation. An investigation revealed an escalating noise complaint dispute between V and two other residents, including a middle-aged non-binary individual and a senior male who was related to another resident. V sustained multiple blunt force trauma injuries, including three distinct cranial lacerations with associated skull fractures, and defensive wounds on their upper body and forearms. The injuries were consistent with being struck by a trophy. The cause of death was blunt force trauma to the head due to multiple impacts with a trophy-like object. The manner of death was classified as homicide. No other circumstances are known.
```
**Analysis:**
- Model is doing many things well
- Model is incorrectly providing the victim's clothing for some reason - this will be fixed.
- Not enough details on the suspects - this is likely due to pipeline limitations, but will be fixed.
- Suspects are not given S1, S2, etc. - this will be fixed.

## v0.1
- Trained model on 43 synthetic data points. 
- Model was ineffective because it started to repeat parts of the system message.