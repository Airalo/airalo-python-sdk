# Airalo Python SDK

A Python SDK for integrating with Airalo's Partner API.

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/Airalo/airalo-python-sdk.git
cd airalo-python-sdk

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### From PyPI (Coming Soon)

```bash
pip install airalo-python-sdk
```

## Quick Start

### 1. Configuration

```python
from airalo.config import Config

config = Config({
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'env': 'sandbox'  # or 'production'
})
```

### 2. OAuth Authentication

```python
from airalo.resources.http_resource import HttpResource
from airalo.helpers.signature import Signature
from airalo.services.oauth_service import OAuthService

# Initialize components
http_resource = HttpResource(config)
signature = Signature(config.get('client_secret'))
oauth_service = OAuthService(config, http_resource, signature)

# Get access token
access_token = oauth_service.get_access_token()
```

## Testing the OAuth Service

Run the OAuth example to test your credentials:

```bash
# Edit oauth_example.py with your credentials first
python oauth_example.py
```

## Requirements

- Python 3.7+
- cryptography>=41.0.0

## Development

### Setting up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run linting
pylint airalo/

# Format code
black airalo/
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=airalo
```

## Project Structure

```
airalo-python-sdk/
├── airalo/
│   ├── __init__.py
│   ├── config.py
│   ├── constants/
│   │   ├── api_constants.py
│   │   └── sdk_constants.py
│   ├── exceptions/
│   │   └── airalo_exception.py
│   ├── helpers/
│   │   ├── cached.py
│   │   ├── crypt.py
│   │   └── signature.py
│   ├── resources/
│   │   ├── http_resource.py
│   │   └── multi_http_resource.py
│   └── services/
│       └── oauth_service.py
├── tests/
├── oauth_example.py
├── setup.py
├── requirements.txt
└── README.md
```

## License

MIT License - see LICENSE file for details.

## Support

For API support, please contact Airalo support or visit the [API documentation](https://partners-doc.airalo.com/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.