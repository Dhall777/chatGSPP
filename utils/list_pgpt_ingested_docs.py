from pgpt_python.client import PrivateGPTApi

# create PGPTAPI client instance
client = PrivateGPTApi(base_url="http://localhost:8001")

# app health check
#print(client.health.health())

# list ingested documents
for doc in client.ingestion.list_ingested().data:
    print(doc.doc_id)
