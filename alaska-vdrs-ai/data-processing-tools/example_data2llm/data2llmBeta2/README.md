# data2llm Beta 2
### main = data2llm.py >> start there!

This is a command-line tool for processing and chunking various types of files (PDF, EPUB, TXT) into smaller, more manageable chunks. It uses OpenAI's API for text processing and chunking, and it can save the processed chunks as JSON files.


#### Current Features:

- Processes and chunks PDF, EPUB, and TXT files into 5000 token chunks
- Uses OpenAI's API for text cleaning, processing, and formatting
- Saves processed chunks as JSON files (either as single files or one per chunk)
- If the user does not request chunked JSON files, large files are soft chunked for the OpenAI context window and then merged back together before being saved as a single JSON file.
- Ability to also save the raw text output (mostly for debugging purposes)
- Validates exported JSON files



#### Updates, Bugs, and Areas of Improvement:

- Further testing is always welcome. Please report any bugs or issues you find. I have only tested on Windows + VSCode so far.
- I made a number of changes/improvements from the original script to switch to using modules, so any excess or stray code needs to be cleaned up.
- Integration with Prompt_Toolkit needs more work. If we're going to use data2llm.py to start and launch the current modules, at some point we will want to add additional modules which could be enabled or disabled by the user through that interface. For example, this may provide support to allow users to convert to markdown instead of JSON, or perhaps use a module that processes all text locally instead of using OpenAI.
- Some of the logging isn't properly stylized with Prompt_Toolkit yet.
- Enabling debug mode doesn't actually do anything. It should enable more detailed logging in the console. I believe this is partially implemented but not working.
- The Prompt_Toolkit progress bars need some work. We can remove the ETA/time function and debug the way it displays progress over the total number of files, and displays one for the number of 