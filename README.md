# 🎓 Study Smart

**AI-powered personal tutor available 24/7.**

Study Smart is a modern web application that helps students master any topic. Simply enter a topic or assignment, and the AI will generate structured explanations, cheat sheets, study plans, and self-check quizzes. Video - https://youtu.be/j5qqtsdnQ_g

![Study Smart Dashboard](docs/dashboard-preview.png)

---

## 🚀 Features

- **🧠 AI-Powered Content**: Instantly generates explanations, summaries, and step-by-step study plans using Gemini/Qwen models.
- **⚡ Reactive UI**: Single-Page Application (SPA) feel using **HTMX** and **Alpine.js** without the complexity of React/Vue.
- **🎨 Modern Design**: Beautiful, responsive interface built with **Tailwind CSS**.
- **🌍 Internationalization**: Built with i18n for EN/RU/DE/FR/ES; **launches on English + Russian** (DE/FR/ES translations are in progress).
- **🔐 Secure Authentication**: Email/Password login + **Magic Link** (passwordless) authentication.
- **💳 Subscriptions**: Integrated **Stripe** payments for tiered plans (Guest, Free, Pro, Pro+).
- **🛡️ Security**: XSS protection (Bleach), CSRF, HSTS/HTTPS enforcement, rate limiting, idempotent Stripe webhooks.

## 🛠️ Tech Stack

This project demonstrates a modern, efficient, and scalable architecture:

| Component     | Technology                                                                                                    | Description                           |
| ------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| **Backend**   | ![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white)                  | Core framework, ORM, Auth             |
| **Database**  | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)      | Relational data storage               |
| **Frontend**  | ![HTMX](https://img.shields.io/badge/HTMX-3D72D7?style=flat&logo=htmx&logoColor=white)                        | Dynamic interactions (HATEOAS)        |
| **Styling**   | ![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white) | Utility-first CSS framework           |
| **Scripting** | ![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0?style=flat&logo=alpine.js&logoColor=white)         | Lightweight client-side interactivity |
| **Tasks**     | ![Celery](https://img.shields.io/badge/Celery-37814A?style=flat&logo=celery&logoColor=white)                  | Async background tasks                |
| **Cache**     | ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)                     | Caching and Message Broker            |
| **Deploy**    | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)                  | Containerization (Multi-stage build)  |

## 🏗️ Architecture

The project follows a **Service-Oriented Architecture** within Django (Django Services Pattern):

- **Apps**: Separated by domain (`accounts`, `prompts`, `subscriptions`).
- **Services**: Business logic is decoupled from Views (e.g., `PromptsService`, `SubscriptionService`).
- **Templates**: Component-based approach using Django `{% include %}` and partials.

## 🏁 Getting Started

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/study-smart.git
    cd study-smart
    ```

2.  **Environment Setup**
    Copy the example environment file:

    ```bash
    cp .env.example .env
    ```

    _Note: The default `.env` is configured for local development._

3.  **Run with Docker**

    ```bash
    docker compose up --build -d
    ```

4.  **Access the App**
    The app is served by nginx on [http://localhost:8080](http://localhost:8080).
    - **Admin Panel**: [http://localhost:8080/admin](http://localhost:8080/admin)
    - _To create a superuser:_
      ```bash
      docker compose exec web python manage.py createsuperuser
      ```

> **Deploying to production?** See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the full
> runbook (required env vars, Stripe webhook setup, HSTS ramp-up, backups).

### 🧪 Running Tests

The project includes a test suite (pytest). Test tooling lives in
`requirements-dev.txt`, so run it via the dedicated `test` service (the
production `web` image ships prod dependencies only):

```bash
docker compose --profile test run --rm test
```

CI (GitHub Actions, `.github/workflows/ci.yml`) runs the same suite, the Django
system check, and a migration check on every push and pull request.

## 📂 Project Structure

```bash
.
├── apps/               # Django Apps (Domain Logic)
│   ├── accounts/       # User Auth & Profiles
│   ├── core/           # Shared utilities
│   ├── prompts/        # AI Generation Logic
│   └── subscriptions/  # Stripe & Plans
├── config/             # Project Settings
├── docker/             # Docker configurations
├── static/             # Static Assets (Tailwind input)
├── templates/          # HTML Templates (HTMX Partials)
└── tests/              # Automated Tests
```

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

---
