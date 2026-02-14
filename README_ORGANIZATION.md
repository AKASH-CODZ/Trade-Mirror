# 🛡️ TradeMirror - Organized Project Structure

## 📁 Project Organization

This repository follows a clean separation between **production code** and **development assets** to ensure security and maintainability.

### 🏭 **Production Structure** (`prod/`)
Contains all code that runs in production environments:

```
prod/
├── core/           # Business logic and data processing
│   ├── processor.py      # Main data processing engine
│   ├── database.py       # Secure database operations
│   └── ai_coach.py       # AI-powered trading insights
├── ui/             # User interface components
│   └── app.py            # Main Streamlit application
├── services/       # External service integrations
│   └── integrations/     # Broker APIs, email connectors
├── data/           # Production data storage
│   └── trademirror.db    # Main database file
└── requirements.txt      # Production dependencies
```

### 🛠️ **Development Structure** (`dev/`)
Contains all development, testing, and verification assets:

```
dev/
├── tests/          # Unit and integration tests
│   ├── test_day2_security.py
│   └── test_day2_integration.py
├── scripts/        # Development utilities and runners
│   ├── run_day2_tests.py
│   ├── run_tests.py
│   ├── requirements.txt
│   └── requirements_day2.txt
├── verification/   # Demo and verification scripts
│   ├── process_real_data.py
│   ├── demo.py
│   └── example_usage.py
└── temp/           # Temporary files and caches
    ├── .pytest_cache/
    └── __pycache__/
```

## 🚀 Quick Start

### Production Deployment
```bash
# Install production dependencies
pip install -r prod/requirements.txt

# Run the application
python main.py
# or
streamlit run prod/ui/app.py
```

### Development Setup
```bash
# Install development dependencies
pip install -r dev/requirements-dev.txt

# Run tests
python dev/scripts/run_day2_tests.py

# Process real data
python dev/verification/process_real_data.py your_data.csv
```

## 🔒 Security Benefits

This organization provides several security advantages:

1. **Clear Separation**: Production code is isolated from development artifacts
2. **Reduced Attack Surface**: Only essential files are deployed to production
3. **Dependency Management**: Separate requirements for production vs development
4. **Audit Trail**: Clear distinction between verified production code and experimental features

## 📋 Best Practices

- **Never deploy** the `dev/` directory to production environments
- **Regular cleanup** of `dev/temp/` directory
- **Version control** only production-ready code in `prod/`
- **Security reviews** focused on `prod/` directory contents