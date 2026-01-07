# ⚡ Runix - Workload Intelligence Platform

**Runix** is a production-grade cloud intelligence platform that observes Cloud Run workloads, learns their behavior using ML, and recommends cost-optimal architectures with AI-powered explanations.

---

## 🌟 Key Features

*   **📊 Live Workload Analysis**: Connects to Google Cloud Monitoring to analyze real-time metrics (CPU, Memory, Requests) from your deployed Cloud Run services.
*   **🧪 Interactive Mock Demo**: Visualizes how the system handles different workload patterns (Bursty, Always-On, Over-Provisioned) without needing live data.
*   **🧠 Gemini AI Integration**: Uses Google's Gemini 1.5 Flash model to generate human-readable, actionable explanations for every optimization recommendation.
*   **💰 Cost Optimization Engine**: Calculates precise potential savings by right-sizing resources (vCPU, Memory) and adjusting auto-scaling settings.
*   **🛡️ Production-Safe**: operates in a read-only mode (Observability), providing recommendations without automatically mutating your infrastructure.

---

## 🛠️ Technology Stack

*   **Backend**: Python 3.10+, Flask
*   **Frontend**: HTML5, CSS3 (Modern Glassmorphism), Vanilla JavaScript
*   **AI/ML**: Google Gemini 1.5 Pro/Flash, Scikit-learn (Clustering)
*   **Cloud Infrastructure**: Google Cloud Run, Cloud Monitoring API
*   **Visualization**: Chart.js for real-time cost comparison

---

## 📂 Project Structure

```
runix/
├── runix/
│   ├── ingestion/       # Cloud Monitoring API clients
│   ├── intelligence/    # Feature extraction & AI explanations
│   ├── optimization/    # Cost calculation logic
│   └── platform/        # Deployment scripts
├── templates/           # Dashboard HTML UI
├── static/              # CSS/JS assets (if any)
├── local_server.py      # Main Flask entry point
├── setup.bat            # One-click Windows setup script
├── requirements.txt     # Python dependencies
└── README.md            # You are here
```

---

## 🚀 Getting Started

### Prerequisites
1.  **Python 3.10+** installed.
2.  **Google Cloud SDK** (gcloud CLI) installed and authenticated.
3.  A **Google Gemini API Key** (Get one at [aistudio.google.com](https://aistudio.google.com/)).

### ⚡ Easy Setup (Windows)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/senpai80085/runix.git
    cd runix
    ```

3.  **Run Setup**:
    Launch the setup script:
    ```cmd
    setup.bat
    ```
    *   **Option 1 (Local)**: Recommended for **Live Analysis** (Cloud Run).
    *   **Option 2 (Docker)**: Recommended for **Mock Demo** (Clean environment).

4.  **Access Dashboard**:
    Open `http://localhost:8080` in your browser.

---

## 🎮 How to Use

### 1. Mock Demo Mode (Default)
Perfect for exploring the platform's capabilities without connecting to a cloud project.
*   Click **"🧪 Mock Demo"**.
*   Select a scenario:
    *   **Bursty Service**: Simulates a spikey workload (recommendation: Scale-to-zero).
    *   **Always-On API**: Simulates steady traffic (recommendation: Reserved instances).
    *   **Over-Provisioned**: Simulates wasted resources (recommendation: Downsizing).
*   View the **AI Insight** card to see Gemini explain the optimization.

### 2. Live Analysis Mode
Analyze your actual usage.
*   Ensure you are authenticated: `gcloud auth application-default login`
*   Click **"📡 Live Analysis"**.
*   Enter your **Cloud Run Service Name** (e.g., `runix-test-workload`).
*   Click **Analyze Service**.

---

## 🔮 Future Scope

*   **Multi-Cloud Support**: Extend monitoring to AWS Lambda and Azure Container Apps.
*   **Drift Detection**: Alert when a workload's behavior changes significantly over time.
*   **CI/CD Integration**: Block deployments if the predicted cost exceeds budget.
*   **Slack/Teams Bot**: Send weekly optimization summaries to engineering teams.

---

## 📄 License

This project is licensed under the MIT License. 
Built with ❤️ for **Google AI Hackathon 2026**.
