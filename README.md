# Alaska VDRS AI Modernization Project

### Purpose:
Fine-tune an LLM to assist in generating an incident narrative (based on multiple input documents) that is submitted to the National Violent Death Reporting System (NVDRS) Database hosted by the Center for Disease Control (CDC). See additional details below under "Project Background." The LLM will be locally hosted on-premises and accessed through a simple web interface. The web interface will facilitate the collection of all files within a "case" required to craft a narrative. After uploading the documents, the fine-tuned LLM and custom prompt(s) generate a draft narrative for professional review that can be rated on quality, re-generated with user feedback, and/or used by a trained abstractor to complete a draft narrative for an NVDRS submission.

### Next Step: Complete (or as close as possible) an alpha fine-tuned local model by November 1st.
LLM: Continue fine-tune of Llama 3.1 8b based on chunked JSON dataset and resulting loramaker queries.
LLM Hosting: Pick an identified local LLM API host and document API calls.
LoRA: Package LoRA within GGUF model for easy deployment.
RAG Solution / Vector Database: Make deployment decision.

### Next Step: Complete front-end interface for November 1st demo that qualifies for beta production.
Video: Create a simpler, polished video that appropriately demos the project, our progress, and where we want to go in under three minutes.
Interface: Optimize existing HTML/CSS. Transform dummy buttons into call-ready state. Get as close to a production-ready interface beta as we can.
Delivery: Package complete front-end interface with any requirement instructions in a final .ZIP. Test prior to November 1st.

### Next Step: Deliver draft outline and early structure of security documentation for SoA IT feedback.
Delivery: Tyler sends Riley a draft of a security documentation outline to ask if it meets their IT team's early expectations.


### [🔗 Link to Project Planning Files 🗒️ << Contains Early Demo Video](https://tylersystemscom-my.sharepoint.com/:f:/g/personal/tyler_tylersystems_com/EoMQpHH-veBNnYFlDdPDM7ABmAhi-KOVk9zr-6zhAO5F7g?e=Wd0Ts5)
#### Request access from Tyler if you're unable to access the folder. Files hosted here on GitHub AND on the OneDrive Shared Folder (also referenced as Sharepoint, Shared Drive, OneDrive) are required to gain a full context of the project.

## 📂 Repo Structure
#### Directory:
- **Reference Data** -> Training datasets, examples, and documentation related to creating an NVDRS report.
  - **Reference Data/Coding Manual** -> Examples of the NVDRS coding manual PDF chunked into machine-readable JSON files of 5,000 tokens or less using the data2llm toolset. Example of question-answer pairs (generic, non-tested) based on the JSON knowledgebase that would be used to fine-tune an LLM.
- **alphaUI** -> Demo early front-end for an incident narrative generation tool.
- **Tool Library** -> Existing tools or libraries contributing to the project.

## Project Background
When someone dies a violent death in the State of Alaska, numerous government processes report the event to Alaska State and United States Federal government agencies. This includes summarizing various statistics taken from law enforcement reports, medical examination data, and up to 35 other documents to be abstracted by an Alaska Violent Death Reporting System (Alaska VDRS) professional. 

This professional abstractor collects ~800 statistics to be properly coded and submitted into a National Violent Death Reporting System (NVDRS) database through a Center for Disease Control (CDC) web portal. This process is currently done manually and is very labor intensive, resulting in delayed reporting and reduced opportunities for government to respond to violent death crisis. The goal is to generate a (600?) word summary generated based on the input documents. The resulting (600?) word summary is called an "incident narrative."

This project seeks to modernize Alaska VDRS reporting utilizing Artificial Intelligence (AI), specifically Large Language Models (LLMs), to generate incident narratives based on a variety of input documents to improve the accuracy and speed of NVDRS reporting. Output narratives are always reviewed by a trained professional, in this case, an Alaska VDRS abstractor.

-	Document length, currently expecting: 1-15 pages per document (4 page avg.)
-	Number of documents currently expecting: 3-8 documents, up to ~35 unique types (templates?)

More details to come.
