#!/bin/bash
# Runix Platform Setup Script
# Creates BigQuery dataset and tables, sets up budget alerts

set -e  # Exit on error

# Configuration
PROJECT_ID="warm-ring-483118-v9"
REGION="asia-south1"
DATASET="runix"
BUDGET_AMOUNT="1"
BUDGET_THRESHOLD="0.01"  # 1% of $1 = $0.01

echo "🚀 Setting up Runix Platform on GCP..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Step 1: Create BigQuery Dataset
echo "📊 Creating BigQuery dataset '$DATASET' in $REGION..."
bq mk --location=$REGION --dataset $PROJECT_ID:$DATASET || echo "Dataset already exists"

# Step 2: Create Tables
echo "📋 Creating BigQuery tables..."
bq query --use_legacy_sql=false < bigquery_schema.sql

# Step 3: Set up Budget Alert
echo "💰 Creating budget alert (\$$BUDGET_AMOUNT with $BUDGET_THRESHOLD threshold)..."
# Note: Budget creation requires billing account ID
# User will need to create this manually via console or provide billing account ID

cat << EOF

⚠️  MANUAL STEP REQUIRED: Budget Alert Setup

Please create a budget alert manually:
1. Go to: https://console.cloud.google.com/billing/budgets?project=$PROJECT_ID
2. Click "CREATE BUDGET"
3. Settings:
   - Name: Runix Budget Alert
   - Projects: warm-ring-483118-v9
   - Amount: \$1.00 USD
   - Threshold: 1% (\$0.01)
   - Email notifications: Your email
4. Click "FINISH"

EOF

# Step 4: Create Service Account
echo "🔑 Creating service account for Runix..."
SA_NAME="runix-monitor"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
  --display-name="Runix Monitoring Service Account" \
  --project=$PROJECT_ID || echo "Service account already exists"

# Grant monitoring viewer role (read-only)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/monitoring.viewer"

# Grant BigQuery data editor role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.dataEditor"

echo ""
echo "✅ Platform setup complete!"
echo ""
echo "Service Account: $SA_EMAIL"
echo "BigQuery Dataset: $PROJECT_ID:$DATASET"
echo ""
echo "Next steps:"
echo "1. Create budget alert (see instructions above)"
echo "2. Deploy Cloud Run service: ./deploy.sh"
echo "3. Configure Looker Studio dashboard"
