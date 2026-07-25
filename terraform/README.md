# Kahani AWS infrastructure (api + worker on ECS, web on Vercel)

## What this creates

| Resource | Purpose |
|----------|---------|
| VPC + NAT | Private ECS/RDS/Redis |
| RDS Postgres 16 | App DB + LangGraph checkpoints |
| ElastiCache Redis 7 | ARQ job queue |
| S3 | Artifact bucket (`ARTIFACTS_BUCKET`) |
| ECR | `kahani-*-api` image (shared by api + worker) |
| ALB | Public entry for API |
| ACM | Cert for `api.uselamp.app` |
| ECS Fargate | `api` (uvicorn) + `worker` (arq) |
| IAM OIDC | GitHub Actions deploy role |

**Web is not on ECS** — deploy `web/` to Vercel and set `VITE_API_BASE_URL=https://api.uselamp.app`.

## Prerequisites

- AWS CLI credentials with rights to create the above
- Terraform >= 1.5
- Cloudflare zone for `uselamp.app`
- GitHub repo for Actions OIDC

## Apply

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit: github_org, aws_region, etc.

terraform init
terraform plan
terraform apply
```

First apply uses **HTTP on the ALB** (`enable_https = false`) so the stack comes up before the ACM cert is issued.

## Cloudflare DNS (`api.uselamp.app`)

1. After apply, read ACM validation records:

   ```bash
   terraform output acm_validation_records
   ```

2. In Cloudflare → DNS → Add record(s) from that output (usually a `_acme-challenge` CNAME).  
   Set **Proxy status = DNS only** (grey cloud).

3. Wait until ACM status is **Issued** (AWS Console → Certificate Manager).

4. Add production API CNAME:

   | Type | Name | Target | Proxy |
   |------|------|--------|-------|
   | CNAME | `api` | value of `terraform output alb_dns_name` | DNS only (recommended) |

5. Re-apply with HTTPS:

   ```hcl
   # terraform.tfvars
   enable_https = true
   ```

   ```bash
   terraform apply
   ```

   ALB will listen on **443** and redirect **80 → 443**.

6. If using Cloudflare orange-cloud proxy later, set SSL/TLS mode to **Full (strict)**.

## Vercel (`uselamp.app`)

1. Import the `web/` project (or deploy via GitHub Actions).
2. Add domains `uselamp.app` and `www.uselamp.app` in Vercel; follow Vercel’s Cloudflare DNS instructions (usually CNAME/`www` + apex).
3. Environment variable:

   ```
   VITE_API_BASE_URL=https://api.uselamp.app
   ```

4. Rebuild/redeploy after setting the variable (Vite bakes it at build time).

## Secrets

All app runtime env for api/worker comes from one Secrets Manager JSON secret
(`…/app/secrets`). Sync from root `.env`:

```bash
./scripts/sync-app-secrets.sh
```

That copies every non-empty `KEY=value` from `.env` into the secret, except:

- `VITE_*` (frontend build-time only)
- Protected AWS infra keys (never overwritten by local Compose values):
  `DATABASE_URL`, `REDIS_URL`, `ARTIFACTS_BUCKET`, `ALLOWED_ORIGINS`

ECS also injects image/research keys when present in the secret JSON:
`IMAGE_PROVIDER`, `OPENAI_IMAGE_MODEL`, `OPENAI_IMAGE_QUALITY`, `TAVILY_API_KEY`,
plus optional `GEMINI_API_KEY` / `GEMINI_TEXT_MODEL` / `GEMINI_IMAGE_MODEL`.
After adding new keys to `modules/ecs` `app_secret_keys`, sync secrets first,
then `terraform apply` so task definitions pick them up.

Force new ECS deployments after secret **or** task-definition changes:

```bash
aws ecs update-service --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_api) \
  --task-definition $(terraform output -raw api_task_definition_arn) \
  --force-new-deployment
aws ecs update-service --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_worker) \
  --task-definition $(terraform output -raw worker_task_definition_arn) \
  --force-new-deployment
```

## GitHub Actions

Set repository **secrets / variables**:

| Name | Type | Value |
|------|------|--------|
| `AWS_ACCESS_KEY_ID` | secret | IAM user access key (deploy user) |
| `AWS_SECRET_ACCESS_KEY` | secret | IAM user secret key |
| `AWS_REGION` | variable | e.g. `ap-south-2` |
| `ECR_REPOSITORY` | variable | `terraform output -raw ecr_repository_name` |
| `ECS_CLUSTER` | variable | `terraform output -raw ecs_cluster_name` |
| `ECS_SERVICE_API` | variable | `terraform output -raw ecs_service_api` |
| `ECS_SERVICE_WORKER` | variable | `terraform output -raw ecs_service_worker` |
| `VITE_API_BASE_URL` | variable | `https://api.uselamp.app` |
| `VERCEL_TOKEN` | secret | from Vercel |
| `VERCEL_ORG_ID` | secret | from Vercel |
| `VERCEL_PROJECT_ID` | secret | from Vercel |

(`AWS_ROLE_ARN` / OIDC is optional; workflows use access keys.)
## First image push (before CI)

```bash
aws ecr get-login-password --region $(terraform output -raw aws_region) \
  | docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url | cut -d/ -f1)

docker build -t $(terraform output -raw ecr_repository_url):latest -f backend/Dockerfile backend
docker push $(terraform output -raw ecr_repository_url):latest

aws ecs update-service --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_api) --force-new-deployment
aws ecs update-service --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_worker) --force-new-deployment
```

## Worker + ARQ

The **worker** ECS service runs `arq worker.settings.WorkerSettings`. The **api** enqueues jobs on Redis; the worker consumes them (script generation, attachment indexing). No public hostname for the worker.
