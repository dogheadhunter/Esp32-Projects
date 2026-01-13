from metadata_enrichment import MetadataEnricher

e = MetadataEnricher()
chunk = {
    'text': 'Before the great war of 2077, Vault-Tec built many vaults',
    'wiki_title': 'Pre-War History'
}
result = e.enrich_chunk(chunk)
print(f'time_period: {result["time_period"]}')
print(f'time_period_confidence: {result["time_period_confidence"]}')
print(f'year_min: {result["year_min"]}')
print(f'year_max: {result["year_max"]}')
print(f'is_pre_war: {result["is_pre_war"]}')
print(f'is_post_war: {result["is_post_war"]}')
