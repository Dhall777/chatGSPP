#!/bin/bash

#for i in {1..4272}; do
for i in {1..100}; do
  make ingest /usr/local/ai-apps/private-gpt/ingested_data/chunk_$i -- --log-file /usr/local/ai-apps/private-gpt/local_data/logs/chunk${i}_ingestion.log;
done

