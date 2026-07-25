"""Databricks AI Search (formerly Vector Search) defaults for Kissa."""

# Free Edition: STANDARD endpoint; Direct Vector Access is not supported —
# prefer Delta Sync indexes over direct upsert indexes.
DEFAULT_ENDPOINT_TYPE = "STANDARD"
DEFAULT_NUM_RESULTS = 5
DEFAULT_QUERY_TYPE = "ANN"
