#!/usr/bin/env bash
# Sync root .env into AWS Secrets Manager (JSON key/value).
# Does not print secret values.
#
# Protected keys are never overwritten from local .env (AWS-managed infra):
#   DATABASE_URL, REDIS_URL, ARTIFACTS_BUCKET, ALLOWED_ORIGINS
# Skipped: VITE_* (frontend build-time only), blank values, comments.
#
# Also backfills protected/infra keys from terraform outputs when missing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
TF_DIR="$ROOT/terraform"

REQUIRED_KEYS=(
  DATABASE_URL
  REDIS_URL
  DATA_DIR
  ARTIFACTS_BUCKET
  ALLOWED_ORIGINS
  LLM_PROVIDER
  LLM_API_KEY
  LLM_MODEL
  TTS_PROVIDER
  ELEVENLABS_API_KEY
  ELEVENLABS_DEFAULT_MODEL_ID
  ELEVENLABS_DEFAULT_OUTPUT_FORMAT
  DATABRICKS_HOST
  DATABRICKS_TOKEN
  DATABRICKS_VECTOR_SEARCH_ENDPOINT
  DATABRICKS_VECTOR_SEARCH_INDEX
  DATABRICKS_VECTOR_SEARCH_COLUMNS
  DATABRICKS_CATALOG
  DATABRICKS_SCHEMA
  DATABRICKS_CAST_TABLE
  DATABRICKS_EMBEDDING_ENDPOINT
  IMAGE_PROVIDER
  OPENAI_IMAGE_MODEL
  OPENAI_IMAGE_QUALITY
  TAVILY_API_KEY
)

# Optional — synced from .env when present; empty string allowed in SM
OPTIONAL_KEYS=(
  GEMINI_API_KEY
  GEMINI_TEXT_MODEL
  GEMINI_IMAGE_MODEL
)

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

cd "$TF_DIR"
SECRET_ARN="$(terraform output -raw app_secret_arn)"
REGION="$(terraform output -raw aws_region)"
ARTIFACTS_BUCKET="$(terraform output -raw artifacts_bucket)"
REDIS_URL="$(terraform output -raw redis_url)"
ALLOWED_ORIGINS="$(terraform output -raw allowed_origins)"

CURRENT="$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_ARN" \
  --region "$REGION" \
  --query SecretString \
  --output text)"

printf '%s\n' "${REQUIRED_KEYS[@]}" > /tmp/kissa-required-keys.txt
printf '%s\n' "${OPTIONAL_KEYS[@]}" > /tmp/kissa-optional-keys.txt

export CURRENT ENV_FILE ARTIFACTS_BUCKET REDIS_URL ALLOWED_ORIGINS

python3 -c '
import json, os

required = open("/tmp/kissa-required-keys.txt", encoding="utf-8").read().split()
optional = open("/tmp/kissa-optional-keys.txt", encoding="utf-8").read().split()
protected = {"DATABASE_URL", "REDIS_URL", "ARTIFACTS_BUCKET", "ALLOWED_ORIGINS"}
current = json.loads(os.environ["CURRENT"] or "{}")
updated = []

# Backfill / refresh infra keys from Terraform (never from local Compose .env)
current["REDIS_URL"] = os.environ["REDIS_URL"]
current["ARTIFACTS_BUCKET"] = os.environ["ARTIFACTS_BUCKET"]
current["ALLOWED_ORIGINS"] = os.environ["ALLOWED_ORIGINS"]
current.setdefault("DATA_DIR", "/data")
current.setdefault("DATABASE_URL", "")  # must already exist from RDS seed
for key in optional:
    current.setdefault(key, "")

with open(os.environ["ENV_FILE"], encoding="utf-8") as f:
    for raw in f:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'\''")
        if not key or key.startswith("VITE_") or key in protected or value == "":
            continue
        current[key] = value
        updated.append(key)

missing = [k for k in required if not current.get(k)]
if missing:
    raise SystemExit("Missing required secret keys after sync: " + ", ".join(missing))

print(json.dumps(current))
open("/tmp/kissa-sync-keys.txt", "w").write("\n".join(sorted(set(updated))))
' > /tmp/kissa-app-secret.json
rm -f /tmp/kissa-required-keys.txt /tmp/kissa-optional-keys.txt

aws secretsmanager put-secret-value \
  --secret-id "$SECRET_ARN" \
  --region "$REGION" \
  --secret-string "file:///tmp/kissa-app-secret.json" \
  >/dev/null

rm -f /tmp/kissa-app-secret.json
echo "Updated secrets on $SECRET_ARN"
echo "Synced from .env:"
sed 's/^/  /' /tmp/kissa-sync-keys.txt
rm -f /tmp/kissa-sync-keys.txt
echo
echo "Refreshed from Terraform: REDIS_URL, ARTIFACTS_BUCKET, ALLOWED_ORIGINS"
echo "Protected from .env overwrite: DATABASE_URL, REDIS_URL, ARTIFACTS_BUCKET, ALLOWED_ORIGINS"
