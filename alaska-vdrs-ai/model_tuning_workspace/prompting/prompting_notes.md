# Prompting notes

This document is used to help aid development of the prompting, logging what the model struggled with and how this was overcome.
It is used for development purposes only to show how the iterations and is not to be used for evaluation purposes.
Each version is an iteration of the prompting, where problems were identified.

## v10 - Claude-3.5-Sonnet
 - Model not including the compound concentration when relevant
   - Detailed that this should be included when relevant

## v9 - Claude-3.5-Sonnet
 - Model providing a slight bit too much detail
   - Re-worded the prompt to be more specific about what is required

## v8 - Claude-3.5-Sonnet
 - Model not starting with in the x hours, which seems to be the way which narratives should be started.
   - Model now told to start with "In the "morning|afternoon|evening|unknown hours leading up to the incident, ..."
 - Model putting the prior medical conditions before the story
   - Model now told to put the prior medical conditions after the story

## v7 - Claude-3.5-Sonnet
 - It almost seems as if the model is trying to fill out a word count by adding in the negatives
   - Removed the word count requirement

## v6 - Claude-3.5-Sonnet
 - Model still including unuseful information
   - Model now told explicitly to exclude information from reports when no information of use is present. 

## v5 - Claude-3.5-Sonnet
 - Model is better at not including irrelevant information, but still includes some
   - More detail on what is considered relevant provided

## v4 - Claude-3.5-Sonnet
 - Model is still including lots of irrelevant information
   - Model is now given more detail on what is considered relevant
 - Model is including lots of information from the postmortem report
   - Attempted solution: Model now told to ensure no in-depth toxicology/autopsy reports are included 

## v3 - Claude-3.5-Sonnet
 - Model stating things in the negative which are irrelevant
   - Attempted solution: Model now told to not state things in the negative

## v2 - Claude-3.5-Sonnet
 - Model is mentioning specific hours of the day
   - Attempted solution: Model now told to exclude specific times of day. 
   - Also, a validator should be added to ensure this is adhered to.
 - Model including lots of irrelevant information
   - Attempted solution: Model now told not to summarize the reports, but to: "create a narrative that tells a story of the incident based upon these report"

## v1 - Claude-3.5-Sonnet
 - Included random factual information it found in reports such as the indoor temperature of a house
   - Attempted solution: Model now told to include only extremely relevant information
 - Formatting was in paragraphs
   - Attempted solution: Model now told to format in a single text block