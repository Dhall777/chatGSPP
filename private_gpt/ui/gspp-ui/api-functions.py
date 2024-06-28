from pgpt_python.client import PrivateGPTApi

# create chatGSPP API client
api_client = PrivateGPTApi(base_url="http://localhost:8001")

# health check
print(api_client.health.health())

# ingest file
#with open("/usr/local/python-apps/privateGPT-test/ingested_data/scraped.csv", "rb") as f:
#    ingested_file_doc_id = api_client.ingestion.ingest_file(file=f).data[0].doc_id
#print("Ingested file doc id: ", ingested_file_doc_id)

# list ingested files
#for doc in api_client.ingestion.list_ingested().data:
#    print(doc.doc_id)

# streaming contextual completions
result = api_client.contextual_completions.prompt_completion(
    prompt="What does GSPP do?",
    use_context=True,
    context_filter={"docs_ids": ["147969f3-dd54-489b-88d1-bf3b07c83384"]},
    include_sources=True,
).choices[0]

print("\n>Contextual completion:")
print(result.message.content)
print(f" Source: {result.sources[0].document.doc_metadata['file_name']}")

