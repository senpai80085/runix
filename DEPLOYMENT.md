# Runix Deployment Guide

## Production Deployment to Google Cloud

This guide walks through deploying Runix to Google Cloud Platform in free-tier mode.

---

## Prerequisites

- ✅ GCP Project: `warm-ring-483118-v9`
- ✅ gcloud CLI installed and authenticated
- ✅ Python 3.11+ installed locally
- ✅ Git installed (for version control)
- ✅ APIs enabled: BigQuery, Cloud Run, Cloud Monitoring, Cloud Build

---

## Phase 1: BigQuery Setup

### Step 1: Create Dataset

```bash
cd c:\Users\PRIYANSHU\OneDrive\Desktop\Senpai

# Create BigQuery dataset in asia-south1 (free tier eligible)
bq mk --location=asia-south1 --dataset warm-ring-483118-v9:runix
```

### Step 2: Deploy Schema

```bash
# Deploy all tables and views
bq query --use_legacy_sql=false < runix\platform\bigquery_schema.sql
```

**Verify**:
```bash
bq ls --project_id=warm-ring-483118-v9 runix
```

You should see:
- `raw_metrics`
- `engineered_features`
- `workload_classifications`
- `optimization_recommendations`
- `latest_recommendations` (view)
- `dashboard_summary` (view)

---

## Phase 2: Service Account Setup

### Step 1: Create Service Account

```bash
gcloud iam service-accounts create runix-monitor \
  --display-name="Runix Monitoring Service Account" \
  --project=warm-ring-483118-v9
```

### Step 2: Grant Permissions

```bash
# Monitoring read-only access
gcloud projects add-iam-policy-binding warm-ring-483118-v9 \
  --member="serviceAccount:runix-monitor@warm-ring-483118-v9.iam.gserviceaccount.com" \
  --role="roles/monitoring.viewer"

# BigQuery data editor (to write analysis results)
gcloud projects add-iam-policy-binding warm-ring-483118-v9 \
  --member="serviceAccount:runix-monitor@warm-ring-483118-v9.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# BigQuery job user (to run queries)
gcloud projects add-iam-policy-binding warm-ring-483118-v9 \
  --member="serviceAccount:runix-monitor@warm-ring-483118-v9.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

---

## Phase 3: Cloud Run Deployment

### Step 1: Build Container

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/warm-ring-483118-v9/runix-ingestion \
  --project=warm-ring-483118-v9 \
  .
```

**Alternative** (if Cloud Build quota exceeded):
```bash
# Build locally with Docker
docker build -t gcr.io/warm-ring-483118-v9/runix-ingestion .
docker push gcr.io/warm-ring-483118-v9/runix-ingestion
```

### Step 2: Deploy to Cloud Run

```bash
gcloud run deploy runix-ingestion \
  --image=gcr.io/warm-ring-483118-v9/runix-ingestion \
  --region=asia-south1 \
  --platform=managed \
  --service-account=runix-monitor@warm-ring-483118-v9.iam.gserviceaccount.com \
  --cpu=0.5 \
  --memory=256Mi \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300s \
  --no-allow-unauthenticated \
  --set-env-vars="PROJECT_ID=warm-ring-483118-v9,REGION=asia-south1,BIGQUERY_DATASET=runix" \
  --project=warm-ring-483118-v9
```

**Free Tier Settings**:
- `--cpu=0.5`: Half vCPU (stays in free tier)
- `--memory=256Mi`: Minimal memory
- `--min-instances=0`: Scale to zero when idle
- `--max-instances=3`: Prevent runaway costs

### Step 3: Get Service URL

```bash
gcloud run services describe runix-ingestion \
  --region=asia-south1 \
  --project=warm-ring-483118-v9 \
  --format="value(status.url)"
```

**Save this URL** - you'll need it for testing.

---

## Phase 4: Testing Deployment

### Test 1: Health Check

```bash
# Get authentication token
TOKEN=$(gcloud auth print-identity-token)

# Test health endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://YOUR-SERVICE-URL/health
```

**Expected response**:
```json
{"status": "healthy"}
```

### Test 2: Mock Analysis

```bash
# Analyze mock bursty workload
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workload_type": "bursty"}' \
  https://YOUR-SERVICE-URL/analyze/mock
```

**Expected**: JSON response with classification and recommendation.

### Test 3: Real Metrics Analysis

```bash
# Analyze real Cloud  Run services (if any exist)
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' \
  https://YOUR-SERVICE-URL/analyze
```

**Expected**: 
- If services exist: Analysis results
- If no services: `{"error": "No metrics found"}` (normal)

### Test 4: Verify BigQuery Data

```bash
# Check if mock data was stored
bq query --use_legacy_sql=false \
  "SELECT * FROM \`warm-ring-483118-v9.runix.workload_classifications\` LIMIT 5"
```

---

## Phase 5: Budget Alert Setup

> ⚠️  **CRITICAL**: Manual step required to prevent unexpected charges

1. Go to: https://console.cloud.google.com/billing/budgets?project=warm-ring-483118-v9
2. Click **CREATE BUDGET**
3. Settings:
   - **Budget name**: Runix Free Tier Budget
   - **Projects**: warm-ring-483118-v9
   - **Amount type**: Specified amount
   - **Target amount**: $1.00 USD
4. **Set alert threshold rules**:
   - Alert at 1% ($0.01)
   - Alert at 50% ($0.50)
   - Alert at 90% ($0.90)
5. **Email notifications**: Add your email
6. Click **FINISH**

---

## Phase 6: Looker Studio Dashboard

Follow the detailed guide in `runix/dashboard/looker_config.md`:

1. Create BigQuery data source
2. Build 9 visualizations
3. Add filters and interactivity
4. Share dashboard

Quick setup link:
```
https://lookerstudio.google.com/create
```

---

## Phase 7: Validation Checklist

- [ ] BigQuery dataset exists with 4 tables + 2 views
- [ ] Service account has correct permissions
- [ ] Cloud Run service deployed and accessible
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Mock analysis works and stores data in BigQuery
- [ ] Budget alert configured (critical!)
- [ ] Looker Studio dashboard created and functional

---

## Cost Monitoring

### Check Monthly Costs

```bash
# View billing for current month
gcloud billing accounts list
gcloud billing accounts get-iam-policy BILLING_ACCOUNT_ID
```

**Or** use the [GCP Console Billing](https://console.cloud.google.com/billing)

### Expected Free Tier Usage

| Service | Monthly Usage | Free Tier Limit | Cost |
|---------|---------------|-----------------|------|
| Cloud Run (CPU) | ~50K vCPU-sec | 180K vCPU-sec | $0 |
| Cloud Run (Memory) | ~100K GB-sec | 360K GB-sec | $0 |
| Cloud Run (Requests) | ~500 requests | 2M requests | $0 |
| BigQuery (Storage) | ~50 MB | 10 GB | $0 |
| BigQuery (Queries) | ~100 MB | 1 TB | $0 |
| Cloud Monitoring | Standard reads | Included | $0 |
| **TOTAL** | | | **$0** ✅ |

---

## Maintenance

### Update Service

```bash
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/warm-ring-483118-v9/runix-ingestion .

gcloud run deploy runix-ingestion \
  --image=gcr.io/warm-ring-483118-v9/runix-ingestion \
  --region=asia-south1 \
  --project=warm-ring-483118-v9
```

### View Logs

```bash
# Stream Cloud Run logs
gcloud run services logs tail runix-ingestion \
  --region=asia-south1 \
  --project=warm-ring-483118-v9
```

### Delete Resources (Cleanup)

```bash
# Delete Cloud Run service
gcloud run services delete runix-ingestion \
  --region=asia-south1 \
 --project=warm-ring-483118-v9

# Delete BigQuery dataset (WARNING: destroys all data)
bq rm -r -f -d warm-ring-483118-v9:runix

# Delete service account
gcloud iam service-accounts delete runix-monitor@warm-ring-483118-v9.iam.gserviceaccount.com \
  --project=warm-ring-483118-v9
```

---

## Troubleshooting

### Issue: "Permission denied" on Cloud Run

**Solution**: Ensure you're authenticated:
```bash
gcloud auth login
gcloud config set project warm-ring-483118-v9
```

### Issue: BigQuery insert errors

**Solution**: Check service account permissions:
```bash
gcloud projects get-iam-policy warm-ring-483118-v9 \
  --flatten="bindings[].members" \
  --filter="bindings.members:runix-monitor"
```

### Issue: Cloud Run cold starts too slow

**Solution**: Set min-instances to 1 (costs ~$5/month):
```bash
gcloud run services update runix-ingestion \
  --min-instances=1 \
  --region=asia-south1 \
  --project=warm-ring-483118-v9
```

### Issue: Exceeded free tier

**Solution**: Check billing dashboard, reduce usage:
- Lower max-instances
- Add request throttling
- Reduce analysis frequency

---

## Next Steps

After deployment:

1. ✅ Run daily analysis with `/analyze` endpoint
2. ✅ Monitor Looker Studio dashboard
3. ✅ Review recommendations weekly
4. ✅ Implement approved optimizations
5. ✅ Track cost savings over time

---

## Support

- **Documentation**: See `README.md` and `runix/dashboard/looker_config.md`
- **Logs**: `gcloud run services logs tail runix-ingestion`
- **BigQuery Console**: https://console.cloud.google.com/bigquery?project=warm-ring-483118-v9
- **Cloud Run Console**: https://console.cloud.google.com/run?project=warm-ring-483118-v9

---

**Runix** - Production Workload Intelligence Platform
Built for Google AI Hackathon 2026
