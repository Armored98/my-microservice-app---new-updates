# Todo List Web App with GCP Kubernetes

This project is a **Todo List Web Application** deployed on **Google Cloud Platform (GCP)** using **Kubernetes** and **Docker**.  
It follows a microservices-style architecture with a **frontend** and **backend**, each containerized and orchestrated by Kubernetes.  
A managed **Cloud SQL (Postgres)** database is used to persist todos.

---

## 📂 Project Structure

```
├── backend
│   ├── app.py                # Backend API (Flask/FastAPI)
│   ├── Dockerfile            # Dockerfile for backend service
│   └── requirements.txt      # Python dependencies
│
├── frontend
│   ├── app.py                # Frontend service
│   ├── auth.html             # Authentication page
│   ├── base.html             # Base template
│   ├── index.html            # Main Todo page
│   ├── frontend_templates_*  # Additional HTML templates
│   ├── Dockerfile            # Dockerfile for frontend service
│   └── requirements.txt      # Python dependencies
│
└── k8s
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── k8s_auth-secret.yaml
    ├── k8s_db-secret.yaml
    └── .DS_Store
```

---

## 🚀 Features
- **Frontend**: Simple web interface to manage todos with authentication.
- **Backend**: REST API connected to a Cloud SQL Postgres database.
- **Database**: Cloud SQL (Postgres 15) with private IP for secure connectivity.
- **Containerization**: Dockerized frontend and backend services.
- **Orchestration**: Kubernetes deployments and services for scalability & reliability.
- **CI/CD**: Automated builds & deployments via GitHub Actions + GCP.

---

## 🛠️ Setup & Deployment

### 1. Enable Required GCP APIs
```bash
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

### 2. Create Cloud SQL Instance
```bash
gcloud sql instances create my-sql-instance \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

Create database & user:
```bash
gcloud sql databases create mydatabase --instance=my-sql-instance
gcloud sql users create myuser --instance=my-sql-instance --password=mypassword
```

Update `k8s/k8s_db-secret.yaml` with your DB credentials and `backend-deployment.yaml` with the instance **private IP**.

---

### 3. Build & Push Docker Images
```bash
# Authenticate Docker with GCP
gcloud auth configure-docker

# Build & push frontend
docker build -t gcr.io/PROJECT_ID/frontend:latest ./frontend
docker push gcr.io/PROJECT_ID/frontend:latest

# Build & push backend
docker build -t gcr.io/PROJECT_ID/backend:latest ./backend
docker push gcr.io/PROJECT_ID/backend:latest
```

---

### 4. Deploy to Kubernetes
```bash
gcloud container clusters create microservice-cluster --num-nodes=2 --zone=us-central1-a
gcloud container clusters get-credentials microservice-cluster --zone=us-central1-a

# Apply Kubernetes manifests
kubectl apply -f k8s/
```

Get external IP:
```bash
kubectl get service frontend-service
```
Open the external IP in your browser to access the app.

---

### 5. Testing
- **Self-healing**:  
  ```bash
  kubectl delete pod <pod-name>
  ```
- **Scaling**:  
  ```bash
  kubectl scale deployment frontend-deployment --replicas=3
  kubectl scale deployment backend-deployment --replicas=3
  ```

---

## 🔄 CI/CD with GitHub Actions
1. Add the provided `Deployment-Pipeline.yml` to `.github/workflows/`.
2. Create a **GCP Service Account** with:
   - Artifact Registry Admin  
   - Kubernetes Engine Developer  
   - Storage Admin  
3. Download the JSON key and add it to GitHub →  
   **Settings → Secrets → Actions → New repository secret → `GCP_CREDENTIALS`**

Now every push to `main` triggers build & deployment automatically.

---

## 👥 Contributors
- **Rasheed Alghamdi**  
- **Faisal Almudarra**  
- **Majed Alghasib**

---

## 📜 License
This project is for educational purposes as part of a **Cloud Software Engineering Capstone**.  
Feel free to fork and adapt for your own use.
