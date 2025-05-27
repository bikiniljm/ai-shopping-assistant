# AI Shopping Assistant

An AI-powered shopping assistant that helps users find products through natural language conversations and image uploads.

## Project Structure

```
.
├── frontend/         # React + Vite frontend
├── backend/          # FastAPI backend
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Environment variables needed in `.env`:
- `VITE_API_URL`: Backend API URL

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Environment variables needed in `.env`:
- `OPENAI_API_KEY`: OpenAI API key
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

## Deployment

### Frontend (AWS Amplify)
1. Connect repository to AWS Amplify
2. Configure environment variables in Amplify Console
3. Deploy will trigger automatically on push

### Backend (Elastic Beanstalk)
1. Initialize EB CLI: `eb init`
2. Create environment: `eb create`
3. Deploy: `eb deploy`

## Features

- Natural language product search
- Image-based product search
- Product recommendations
- Conversational shopping experience
- Session management
- Responsive design

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Serper API key (for product search)
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- EB CLI (Elastic Beanstalk CLI) installed
- Docker installed (for backend deployment)

## Environment Setup

### Backend Setup

1. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv backend/venv

# Activate virtual environment
# On Windows:
backend\venv\Scripts\activate
# On macOS/Linux:
source backend/venv/bin/activate
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Create a `.env` file in the `backend` directory:
```env
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
```

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Create a `.env` file in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

1. Start the backend server:
```bash
# From the backend directory
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
# From the frontend directory
npm run dev
```

3. Access the application at `http://localhost:3000`

## Deployment

### AWS Deployment

#### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- EB CLI (Elastic Beanstalk CLI) installed
- Docker installed (for backend deployment)

#### Backend Deployment (Elastic Beanstalk)

1. Create Dockerfile in backend directory:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Initialize EB CLI:
```bash
cd backend
eb init -p docker ai-shopping-assistant
```

3. Create .ebignore file:
```
venv/
__pycache__/
*.pyc
.env.local
```

4. Create Elastic Beanstalk environment:
```bash
eb create ai-shopping-assistant-prod
```

5. Set environment variables in AWS Console:
- Go to Elastic Beanstalk > Environments > Your Environment
- Configuration > Software > Environment properties
- Add:
  - OPENAI_API_KEY
  - SERPER_API_KEY

6. Deploy:
```bash
eb deploy
```

#### Frontend Deployment (AWS Amplify)

1. Initialize Amplify:
```bash
cd frontend
amplify init
```

2. Add environment variables in Amplify Console:
- Go to AWS Amplify Console > Your App > Environment variables
- Add:
  - NEXT_PUBLIC_API_URL (your Elastic Beanstalk URL)

3. Connect repository:
- Go to AWS Amplify Console
- Click "New app" > "Host web app"
- Choose your Git provider
- Select repository and branch
- Follow the setup wizard

4. Update build settings (amplify.yml):
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

#### Domain Setup and HTTPS

1. Configure Custom Domain in Elastic Beanstalk:
- Go to Elastic Beanstalk Console
- Select your environment
- Configuration > Load balancer > Add listener
- Configure SSL certificate using AWS Certificate Manager

2. Configure Custom Domain in Amplify:
- Go to Amplify Console > Domain management
- Add domain
- Follow DNS validation steps

#### Monitoring and Scaling

1. Backend Monitoring (Elastic Beanstalk):
- Configure CloudWatch alarms:
  ```bash
  eb health
  ```
- Set up auto-scaling:
  - Go to Configuration > Capacity
  - Modify Auto Scaling group settings

2. Frontend Monitoring (Amplify):
- Access built-in analytics in Amplify Console
- Set up CloudWatch alarms for additional metrics

#### Cost Optimization

1. Elastic Beanstalk:
- Use t3.micro or t3.small instances for development
- Enable auto-scaling based on demand
- Configure proper instance termination policies

2. Amplify:
- Use build caching to reduce build minutes
- Implement proper cache headers for static assets
- Consider using CloudFront for global content delivery

#### Security Best Practices

1. Network Security:
- Configure VPC for Elastic Beanstalk
- Set up security groups with minimal required access
- Enable AWS WAF for web application firewall

2. Application Security:
- Store secrets in AWS Secrets Manager
- Enable AWS Shield for DDoS protection
- Implement proper CORS policies

3. Monitoring & Compliance:
- Enable AWS CloudTrail
- Set up AWS Config rules
- Implement proper logging and monitoring

#### Backup and Disaster Recovery

1. Create backup plan:
- Regular snapshots of EBS volumes
- Database backups if applicable
- Code repository backups

2. Disaster Recovery:
- Document recovery procedures
- Test recovery process regularly
- Maintain up-to-date deployment documentation

## Project Structure

```
.
├── backend/
│   ├── chatbot/          # Chatbot logic and handlers
│   ├── models/           # Data models and business logic
│   ├── tests/           # Test cases
│   └── main.py          # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/      # Next.js pages
│   │   └── types/      # TypeScript type definitions
│   └── public/         # Static assets
└── README.md
```

## API Documentation

Once the backend server is running, you can access:
- API documentation: `http://localhost:8000/docs`
- Alternative documentation: `http://localhost:8000/redoc`

## Development Guidelines

1. Code Style
   - Backend: Follow PEP 8 guidelines
   - Frontend: Follow ESLint configuration

2. Type Safety
   - Backend: Use Python type hints
   - Frontend: Use TypeScript strict mode

3. Testing
   - Write unit tests for new features
   - Run tests before submitting PRs

## Environment Variables

### Backend Variables

| Variable | Description | Required |
|----------|-------------|----------|
| OPENAI_API_KEY | OpenAI API key for chat and image analysis | Yes |
| SERPER_API_KEY | Serper API key for product search | Yes |

### Frontend Variables

| Variable | Description | Required |
|----------|-------------|----------|
| NEXT_PUBLIC_API_URL | Backend API URL | Yes |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## AWS Setup

### 1. AWS Account Setup

1. Create an AWS Account if you don't have one:
   - Go to [AWS Console](https://aws.amazon.com/)
   - Click "Create an AWS Account"
   - Follow the registration process

2. Create an IAM Admin User:
   - Go to IAM Console
   - Create a new IAM user with AdministratorAccess
   - Save the Access Key ID and Secret Access Key

3. Required IAM Permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "elasticbeanstalk:*",
                   "ec2:*",
                   "ecs:*",
                   "ecr:*",
                   "cloudwatch:*",
                   "s3:*",
                   "amplify:*",
                   "iam:*",
                   "cloudformation:*"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

### 2. AWS CLI Setup

1. Install AWS CLI:
   ```bash
   # macOS (using Homebrew)
   brew install awscli

   # Windows (using winget)
   winget install -e --id Amazon.AWSCLI

   # Linux
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

2. Configure AWS CLI:
   ```bash
   aws configure
   ```
   Enter:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., us-east-1)
   - Default output format (json)

### 3. Elastic Beanstalk CLI Setup

1. Install EB CLI:
   ```bash
   # macOS (using Homebrew)
   brew install aws-elasticbeanstalk

   # Using pip (all platforms)
   pip install awsebcli

   # Verify installation
   eb --version
   ```

2. Configure EB CLI:
   ```bash
   # Initialize EB CLI in your project
   cd backend
   eb init

   # Follow the prompts:
   # - Select a region
   # - Select an application name
   # - Select Python platform
   # - Set up SSH for instances
   ```

### 4. Docker Setup

1. Install Docker:
   ```bash
   # macOS
   brew install --cask docker

   # Windows
   winget install Docker.DockerDesktop

   # Linux (Ubuntu)
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. Start Docker:
   - macOS/Windows: Open Docker Desktop
   - Linux: `sudo systemctl start docker`

3. Verify installation:
   ```bash
   docker --version
   docker ps
   ```

### 5. AWS Services Setup

1. Create ECR Repository (Optional, for custom Docker images):
   ```bash
   aws ecr create-repository --repository-name ai-shopping-assistant
   ```

2. Create S3 Bucket (for application versions):
   ```bash
   aws s3 mb s3://ai-shopping-assistant-deployments
   ```

3. Create Elastic Beanstalk Application:
   ```bash
   eb init ai-shopping-assistant --platform docker --region us-east-1
   ```

4. Set up Amplify CLI:
   ```bash
   # Install Amplify CLI
   npm install -g @aws-amplify/cli

   # Configure Amplify
   amplify configure

   # Follow the prompts to create a new IAM user for Amplify
   ```

### 6. Security Setup

1. Create SSL Certificate (for custom domain):
   ```bash
   # Request certificate
   aws acm request-certificate \
       --domain-name yourdomain.com \
       --validation-method DNS \
       --region us-east-1
   ```

2. Set up AWS Secrets Manager:
   ```bash
   # Store API keys
   aws secretsmanager create-secret \
       --name ai-shopping-assistant/prod \
       --secret-string '{"OPENAI_API_KEY":"your-key","SERPER_API_KEY":"your-key"}'
   ``` 