"""
Environment configuration example for RAIL Score Python SDK.

This example demonstrates how to configure the SDK using environment variables,
configuration files, and different deployment environments.
"""

import os
from rail_score_sdk import RailScoreClient
from dotenv import load_dotenv  # pip install python-dotenv

print("=" * 70)
print("RAIL Score SDK - Environment Configuration")
print("=" * 70)

# Example 1: Using Environment Variables
print("\nExample 1: Environment Variables Configuration")
print("-" * 70)

# Load from .env file (recommended for development)
load_dotenv()  # Loads .env file from current directory

# Get configuration from environment
API_KEY = os.getenv('RAIL_API_KEY')
BASE_URL = os.getenv('RAIL_BASE_URL', 'https://api.responsibleailabs.ai')
TIMEOUT = int(os.getenv('RAIL_TIMEOUT', '30'))

print(f"Configuration loaded from environment:")
print(f"  API Key: {'*' * 8}...{API_KEY[-4:] if API_KEY else 'Not set'}")
print(f"  Base URL: {BASE_URL}")
print(f"  Timeout: {TIMEOUT}s")

# Create client from environment
if API_KEY:
    client = RailScoreClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=TIMEOUT
    )
    print("✓ Client initialized from environment variables")
else:
    print("⚠ RAIL_API_KEY not set in environment")

# Example 2: .env File Configuration
print("\n\nExample 2: .env File Configuration")
print("-" * 70)

print("""
Create a .env file in your project root:

# .env file
RAIL_API_KEY=your-rail-api-key-here
RAIL_BASE_URL=https://api.responsibleailabs.ai
RAIL_TIMEOUT=60

# Optional: different environments
RAIL_ENV=development  # development | staging | production

# Optional: logging
RAIL_LOG_LEVEL=INFO
RAIL_LOG_FILE=rail_score.log
""")

# Example 3: Configuration Class
print("\nExample 3: Configuration Class Pattern")
print("-" * 70)

class RailScoreConfig:
    """Configuration class for RAIL Score SDK."""

    def __init__(self, env='development'):
        self.env = env
        self._load_config()

    def _load_config(self):
        """Load configuration based on environment."""
        if self.env == 'development':
            self.api_key = os.getenv('RAIL_API_KEY_DEV', 'dev-key')
            self.base_url = 'https://api-dev.responsibleailabs.ai'
            self.timeout = 30
            self.debug = True
        elif self.env == 'staging':
            self.api_key = os.getenv('RAIL_API_KEY_STAGING', 'staging-key')
            self.base_url = 'https://api-staging.responsibleailabs.ai'
            self.timeout = 45
            self.debug = True
        elif self.env == 'production':
            self.api_key = os.getenv('RAIL_API_KEY_PROD')
            self.base_url = 'https://api.responsibleailabs.ai'
            self.timeout = 60
            self.debug = False
        else:
            raise ValueError(f"Invalid environment: {self.env}")

        # Validate configuration
        if not self.api_key:
            raise ValueError(f"API key not set for environment: {self.env}")

    def create_client(self):
        """Create RAIL Score client with this configuration."""
        return RailScoreClient(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    def __repr__(self):
        return f"RailScoreConfig(env={self.env}, url={self.base_url})"

# Usage
current_env = os.getenv('RAIL_ENV', 'development')
print(f"Loading configuration for: {current_env}")

try:
    config = RailScoreConfig(env=current_env)
    print(f"✓ Configuration loaded: {config}")
    # client = config.create_client()
except ValueError as e:
    print(f"❌ Configuration error: {e}")

# Example 4: Multi-Environment Setup
print("\n\nExample 4: Multi-Environment Setup")
print("-" * 70)

class EnvironmentConfig:
    """Environment-specific configuration."""

    DEVELOPMENT = {
        'api_key_env': 'RAIL_API_KEY_DEV',
        'base_url': 'http://localhost:3000',
        'timeout': 30,
        'retry_attempts': 3,
        'log_level': 'DEBUG'
    }

    STAGING = {
        'api_key_env': 'RAIL_API_KEY_STAGING',
        'base_url': 'https://api-staging.responsibleailabs.ai',
        'timeout': 45,
        'retry_attempts': 3,
        'log_level': 'INFO'
    }

    PRODUCTION = {
        'api_key_env': 'RAIL_API_KEY_PROD',
        'base_url': 'https://api.responsibleailabs.ai',
        'timeout': 60,
        'retry_attempts': 5,
        'log_level': 'WARNING'
    }

    @classmethod
    def get_config(cls, env='development'):
        """Get configuration for specified environment."""
        configs = {
            'development': cls.DEVELOPMENT,
            'staging': cls.STAGING,
            'production': cls.PRODUCTION
        }

        if env not in configs:
            raise ValueError(f"Invalid environment: {env}. Must be one of {list(configs.keys())}")

        config = configs[env].copy()
        config['api_key'] = os.getenv(config['api_key_env'])

        if not config['api_key']:
            raise ValueError(f"API key not set: {config['api_key_env']}")

        return config

# Usage
env = os.getenv('APP_ENV', 'development')
print(f"Current environment: {env}")

try:
    env_config = EnvironmentConfig.get_config(env)
    print(f"Configuration:")
    for key, value in env_config.items():
        if key == 'api_key':
            print(f"  {key}: {'*' * 8}...{value[-4:] if value else 'Not set'}")
        else:
            print(f"  {key}: {value}")
except ValueError as e:
    print(f"❌ Error: {e}")

# Example 5: Configuration File (JSON)
print("\n\nExample 5: JSON Configuration File")
print("-" * 70)

import json

config_example = {
    "development": {
        "base_url": "http://localhost:3000",
        "timeout": 30,
        "retry_attempts": 3,
        "features": {
            "caching": True,
            "logging": True,
            "debug": True
        }
    },
    "production": {
        "base_url": "https://api.responsibleailabs.ai",
        "timeout": 60,
        "retry_attempts": 5,
        "features": {
            "caching": True,
            "logging": False,
            "debug": False
        }
    }
}

print("Example config.json:")
print(json.dumps(config_example, indent=2))

print("""
\nUsage:
import json

with open('config.json') as f:
    config = json.load(f)

env = os.getenv('ENV', 'development')
settings = config[env]

client = RailScoreClient(
    api_key=os.getenv('RAIL_API_KEY'),
    base_url=settings['base_url'],
    timeout=settings['timeout']
)
""")

# Example 6: Docker Environment
print("\nExample 6: Docker Environment Configuration")
print("-" * 70)

print("""
Docker Compose configuration:

# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - RAIL_API_KEY=${RAIL_API_KEY}
      - RAIL_BASE_URL=https://api.responsibleailabs.ai
      - RAIL_TIMEOUT=60
      - APP_ENV=production
    env_file:
      - .env

# .env file (not committed to git)
RAIL_API_KEY=your-production-key-here

# In your application:
client = RailScoreClient(
    api_key=os.environ['RAIL_API_KEY'],
    base_url=os.environ['RAIL_BASE_URL'],
    timeout=int(os.environ['RAIL_TIMEOUT'])
)
""")

# Example 7: Kubernetes Secrets
print("\nExample 7: Kubernetes Secrets Configuration")
print("-" * 70)

print("""
Kubernetes configuration:

# Create secret
kubectl create secret generic rail-score-secrets \\
  --from-literal=api-key=your-rail-api-key-here

# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rail-score-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: your-app:latest
        env:
        - name: RAIL_API_KEY
          valueFrom:
            secretKeyRef:
              name: rail-score-secrets
              key: api-key
        - name: RAIL_BASE_URL
          value: "https://api.responsibleailabs.ai"
        - name: RAIL_TIMEOUT
          value: "60"

# In your application, access as environment variables
client = RailScoreClient(
    api_key=os.environ['RAIL_API_KEY'],
    base_url=os.environ.get('RAIL_BASE_URL', 'https://api.responsibleailabs.ai'),
    timeout=int(os.environ.get('RAIL_TIMEOUT', '30'))
)
""")

# Example 8: AWS Systems Manager Parameter Store
print("\nExample 8: AWS Parameter Store Configuration")
print("-" * 70)

print("""
AWS SSM Parameter Store:

# Store API key (do this once)
aws ssm put-parameter \\
  --name "/myapp/rail-score/api-key" \\
  --value "your-rail-api-key-here" \\
  --type "SecureString"

# In your Python application:
import boto3

def get_rail_config():
    ssm = boto3.client('ssm')

    api_key = ssm.get_parameter(
        Name='/myapp/rail-score/api-key',
        WithDecryption=True
    )['Parameter']['Value']

    return RailScoreClient(
        api_key=api_key,
        base_url='https://api.responsibleailabs.ai'
    )

client = get_rail_config()
""")

# Best Practices
print("\n" + "=" * 70)
print("Environment Configuration - Best Practices")
print("=" * 70)
print("""
1. Security:
   ✓ Never commit API keys to version control
   ✓ Use environment variables or secret management
   ✓ Rotate keys periodically
   ✓ Use different keys for dev/staging/prod
   ✓ Add .env to .gitignore

2. Environment Variables:
   ✓ Use .env file for local development
   ✓ Use python-dotenv to load .env files
   ✓ Provide sensible defaults
   ✓ Validate all required variables are set
   ✓ Document all environment variables

3. Configuration Management:
   ✓ Separate config from code
   ✓ Use environment-specific configs
   ✓ Validate configuration on startup
   ✓ Use configuration classes for complex setups
   ✓ Support multiple configuration sources

4. Deployment:
   ✓ Docker: Use env_file or environment section
   ✓ Kubernetes: Use Secrets and ConfigMaps
   ✓ AWS: Use Parameter Store or Secrets Manager
   ✓ Cloud platforms: Use platform's secret management
   ✓ CI/CD: Use encrypted environment variables

5. Development Workflow:
   ✓ Create .env.example with dummy values
   ✓ Document environment setup in README
   ✓ Use different API keys per developer (if needed)
   ✓ Test with staging environment before production
   ✓ Log configuration (without sensitive data) on startup

6. Error Handling:
   ✓ Check if API key is set before creating client
   ✓ Provide helpful error messages
   ✓ Fail fast if configuration is invalid
   ✓ Log configuration errors
   ✓ Handle missing optional configuration gracefully

Example .env.example file:
# Copy this to .env and fill in your values
RAIL_API_KEY=your-rail-api-key-here
RAIL_BASE_URL=https://api.responsibleailabs.ai
RAIL_TIMEOUT=30
APP_ENV=development

Example .gitignore:
.env
.env.local
*.key
config/secrets.json
""")

print("=" * 70)
print("Environment Configuration Examples Complete!")
print("=" * 70)
