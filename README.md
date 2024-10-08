# ChatGSPP prototype

## Technical overview
* using privateGPT's [fully local setup configuration](https://docs.privategpt.dev/installation/getting-started/installation#local-llama-cpp-powered-setup) for the LLM and tokenizer
* custom web scraping bot that scrapes raw HTML data per web page (using depth-first search), cleans it, formats it as a Pandas DataFrame, then saves the data frame as a CSV 
* configured chatGSPP to use **Mistral-7B** for the LLM and tokenization
* currently using **BAAI** for embedding and **Qdrant** as the vector database
* the LLM's queried data is scraped from the main GSPP website using the web-scraper.py file (mentioned below)
* the demo custom UI resources are located within the `~/ui/gspp-ui` directory, and uses PrivateGPT's [Python SDK](https://docs.privategpt.dev/api-reference/overview/sd-ks) to make API calls
	* the demo custom UI is built using Flask and a barebones HTML file

## How to run chatGSPP
* pull the repo
* create a virtual environment (highly recommended)
* export your hugging face API auth token
	* `export HF_TOKEN=your-token`
* install dependencies and LLM/etc
	* `pip install make flask poetry pgpt_python docx2txt==0.8`
	* `poetry install --extras "ui llms-llama-cpp embeddings-huggingface vector-stores-qdrant"`
	* `poetry run python scripts/setup`
* run the web-scraper.py file
	* `python web-scraper.py`
* ingest the scraped.csv file using [this documentation](https://docs.privategpt.dev/manual/document-management/ingestion), specifically the "bulk local ingestion" part
	* ingestion script would look something like this:
		* `make ingest ~/chatGSPP/ingested_data -- --log-file ~/chatGSPP/ingested_data/ingestion_errors.log`
* reference [this documentation](https://docs.privategpt.dev/installation/getting-started/installation#local-llama-cpp-powered-setup) to load the dependencies and start the API server, specifically the "local, llama-cpp powered setup" part
	* `PGPT_PROFILES=local make run`
* now you can start the demo UI server by
	* navigating to `~/ui/gspp-ui`
	* running `python gspp-ui-app.py`
* navigate to the demo custom UI via http://localhost:5000 and ask the bot some questions
	* can also access the built-in Gradio UI for testing via http://localhost:8001
* to-do: create a cool UI so we can add this functionality to GSPP's website :)

## More documentation!
Full documentation on installation, dependencies, configuration, running the server, deployment options,
ingesting local documents, API details and UI features can be found here: https://docs.privategpt.dev/

## Project Summary
ChatGSPP is built on top of PrivateGPT. PrivateGPT is a production-ready AI project that allows you to ask questions about your documents using the power
of Large Language Models (LLMs), even in scenarios without an Internet connection. 100% private, no data leaves your
execution environment at any point.

The project provides an API offering all the primitives required to build private, context-aware AI applications.
It follows and extends the [OpenAI API standard](https://openai.com/blog/openai-api),
and supports both normal and streaming responses.

The API is divided into two logical blocks:

**High-level API**, which abstracts all the complexity of a RAG (Retrieval Augmented Generation)
pipeline implementation:
- Ingestion of documents: internally managing document parsing,
splitting, metadata extraction, embedding generation and storage.
- Chat & Completions using context from ingested documents:
abstracting the retrieval of context, the prompt engineering and the response generation.

**Low-level API**, which allows advanced users to implement their own complex pipelines:
- Embeddings generation: based on a piece of text.
- Contextual chunks retrieval: given a query, returns the most relevant chunks of text from the ingested documents.

In addition to this, a working [Gradio UI](https://www.gradio.app/)
client is provided to test the API, together with a set of useful tools such as bulk model
download script, ingestion script, documents folder watch, etc.

## Architecture
This project is built on top of PrivateGPT.  Conceptually, PrivateGPT is an API that wraps a RAG pipeline and exposes its
primitives.
* The API is built using [FastAPI](https://fastapi.tiangolo.com/) and follows
  [OpenAI's API scheme](https://platform.openai.com/docs/api-reference).
* The RAG pipeline is based on [LlamaIndex](https://www.llamaindex.ai/).
* The API has [SDK's](https://docs.privategpt.dev/api-reference/overview/sd-ks) available for building custom workflows (like this demo)

The design of PrivateGPT allows to easily extend and adapt both the API and the
RAG implementation. Some key architectural decisions are:
* Dependency Injection, decoupling the different components and layers.
* Usage of LlamaIndex abstractions such as `LLM`, `BaseEmbedding` or `VectorStore`,
  making it immediate to change the actual implementations of those abstractions.
* Simplicity, adding as few layers and new abstractions as possible.
* Ready to use, providing a full implementation of the API and RAG
  pipeline.

Main building blocks:
* APIs are defined in `private_gpt:server:<api>`. Each package contains an
  `<api>_router.py` (FastAPI layer) and an `<api>_service.py` (the
  service implementation). Each *Service* uses LlamaIndex base abstractions instead
  of specific implementations,
  decoupling the actual implementation from its usage.
* Components are placed in
  `private_gpt:components:<component>`. Each *Component* is in charge of providing
  actual implementations to the base abstractions used in the Services - for example
  `LLMComponent` is in charge of providing an actual implementation of an `LLM`
  (for example `LlamaCPP` or `OpenAI`).

## 🤗 Partners & Supporters
PrivateGPT is actively supported by the teams behind:
* [Qdrant](https://qdrant.tech/), providing the default vector database
* [Fern](https://buildwithfern.com/), providing Documentation and SDKs
* [LlamaIndex](https://www.llamaindex.ai/), providing the base RAG framework and abstractions

This project has been strongly influenced and supported by other amazing projects like
[LangChain](https://github.com/hwchase17/langchain),
[GPT4All](https://github.com/nomic-ai/gpt4all),
[LlamaCpp](https://github.com/ggerganov/llama.cpp),
[Chroma](https://www.trychroma.com/)
and [SentenceTransformers](https://www.sbert.net/).
