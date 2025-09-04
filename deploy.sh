#!/bin/bash

# URL Shortener Backend Deployment Script for Google Cloud Run
# Make sure you have gcloud CLI installed and authenticated

set -e

# Configuration
PROJECT_ID="loyal-bit-471103-h0"  # Replace with your project ID
REGION="us-central1"
SERVICE_NAME="url-shortener-backend"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting deployment of URL Shortener Backend to Google Cloud Run${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}⚠️  Not authenticated with gcloud. Running authentication...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}📋 Setting project to $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable redis.googleapis.com

# Build Docker image
echo -e "${YELLOW}🏗️  Building Docker image...${NC}"
docker build -t $IMAGE_NAME .

# Push to Container Registry
echo -e "${YELLOW}📤 Pushing image to Container Registry...${NC}"
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80 \
    --timeout 300 \
    --set-env-vars "DEBUG=False,APP_NAME=URL Shortener,BASE_URL=https://$SERVICE_NAME-$REGION.a.run.app"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}📊 Health Check: $SERVICE_URL/health${NC}"
echo -e "${GREEN}📚 API Docs: $SERVICE_URL/docs${NC}"

echo -e "${BLUE}📝 Next steps:${NC}"
echo -e "1. Set up Cloud SQL PostgreSQL database"
echo -e "2. Set up Redis instance (Memorystore)"
echo -e "3. Configure environment variables"
echo -e "4. Run database migrations"

echo -e "${YELLOW}💡 To set environment variables:${NC}"
echo -e "gcloud run services update $SERVICE_NAME --region=$REGION \\"
echo -e "  --set-env-vars DATABASE_URL=your-db-url,REDIS_URL=your-redis-url,JWT_SECRET_KEY=your-secret"
