# Monorepo

```bash

simon_agentic_ai_app/
├── .github/
│   └── workflows/
├── services/
│   ├── frontend/                 
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   └── .dockerignore
│   ├── backend/                  
│   │   ├── src/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .dockerignore
│   ├── middleware/               
│   │   ├── src/
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   └── .dockerignore
│   └── interface/                
│       ├── src/
│       ├── requirements.txt
│       ├── Dockerfile
│       └── .dockerignore
├── lambdas/
│   ├── lambda-bedrock-knowledge/
│   │   ├── src/
│   │   ├── requirements.txt
│   ├── lambda-bedrock-change/
│   │   ├── src/
│   │   ├── requirements.txt
│   ├── lambda-bedrock-ticket/
│   │   ├── src/
│   │   ├── requirements.txt
│   ├── lambda-scheduled-1430/
│   │   ├── src/
│   │   ├── requirements.txt
│   ├── lambda-scheduled-1530/
│   │   ├── src/
│   │   ├── requirements.txt
│   └── lambda-scheduled-1630/
│       ├── src/
│       └── requirements.txt
├── docker-compose.yml            
├── .env.example
├── .gitignore
└── README.md
```