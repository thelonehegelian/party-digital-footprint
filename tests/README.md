# API Test Suite

Comprehensive pytest test suite for the Reform UK Messaging Analysis API.

## Test Coverage

### ✅ 54 Tests Passing (100%)

- **Basic API Endpoints** (9 tests) - Health checks, root endpoint, documentation
- **Message Submission** (10 tests) - Single and bulk message processing
- **Phase 2 Endpoints** (11 tests) - Constituencies, candidates, and their relationships
- **Sources & Statistics** (10 tests) - Source management and system statistics
- **Edge Cases & Performance** (14 tests) - Error handling, performance limits, concurrent requests

## Test Categories

### 1. Basic API Tests (`test_api_basic.py`)
- ✅ Health check endpoint
- ✅ Root endpoint and API info
- ✅ OpenAPI documentation availability
- ✅ CORS header configuration
- ✅ Error handling (404, 405, malformed JSON)

### 2. Message Processing Tests (`test_messages.py`)
- ✅ Single message submission and validation
- ✅ Bulk message processing (up to 100 messages)
- ✅ Duplicate message detection
- ✅ Data validation and error responses
- ✅ Candidate message association (Phase 2)
- ✅ Special character and Unicode handling

### 3. Phase 2 Endpoint Tests (`test_phase2_endpoints.py`)
- ✅ Constituencies listing and filtering
- ✅ Candidates management and social media linking
- ✅ Candidate message retrieval and content truncation
- ✅ Phase 2 integration with statistics
- ✅ Geographic scope distribution
- ✅ Constituency-candidate relationship integrity

### 4. Sources & Statistics Tests (`test_sources_and_stats.py`)
- ✅ Sources endpoint data validation
- ✅ Message count accuracy across sources
- ✅ Comprehensive statistics endpoint
- ✅ Geographic and source type distributions
- ✅ Data integrity between endpoints

### 5. Edge Cases & Performance Tests (`test_edge_cases.py`)
- ✅ Extremely long content handling (max 10k chars)
- ✅ Unicode and special character processing
- ✅ Invalid data format handling
- ✅ Bulk submission limits and performance (100 messages)
- ✅ Concurrent request handling (10 simultaneous)
- ✅ Database constraint violations
- ✅ Error recovery mechanisms

## Running Tests

### Prerequisites
```bash
# Install dev dependencies
uv sync --extra dev

# Ensure API server is running
uvicorn src.api.main:app --reload
```

### Run All Tests
```bash
uv run python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Basic API tests only
uv run python -m pytest tests/test_api_basic.py -v

# Phase 2 functionality only
uv run python -m pytest tests/test_phase2_endpoints.py -v

# Performance and edge cases
uv run python -m pytest tests/test_edge_cases.py -v
```

### Run with Coverage
```bash
uv run python -m pytest tests/ --cov=src --cov-report=html
```

## Test Configuration

- **pytest.ini**: Configuration file with test discovery and reporting settings
- **conftest.py**: Shared fixtures and test setup
- **Fixtures Available**: API client, base URL, sample data for all test scenarios

## Test Data

The test suite uses realistic sample data including:
- **UK constituencies** from various regions (England, Scotland, Wales, N. Ireland)
- **Candidate profiles** with social media accounts
- **Political messaging** content with proper validation
- **Phase 2 integration** data for geographic analysis

## Validation Coverage

### API Schema Validation
- ✅ Pydantic model validation for all inputs
- ✅ Required field enforcement
- ✅ Data type validation (strings, integers, dates)
- ✅ Literal validation for enums (source_type, geographic_scope)
- ✅ Content length limits (1-10,000 characters)

### Business Logic Validation  
- ✅ Duplicate message detection
- ✅ Source creation and linking
- ✅ Candidate-constituency relationships
- ✅ NLP keyword extraction integration
- ✅ Geographic scope classification

### Error Handling
- ✅ Graceful handling of invalid requests
- ✅ Comprehensive error messages
- ✅ Proper HTTP status codes
- ✅ Bulk operation partial failure recovery

## Performance Benchmarks

- **Single message**: < 100ms response time
- **Bulk 100 messages**: < 30 seconds processing time  
- **Concurrent requests**: 10 simultaneous requests handled
- **Large content**: Up to 10,000 character messages supported

## Phase 2 Features Tested

- ✅ **Constituency Management**: All UK regions represented
- ✅ **Candidate Profiles**: Social media integration (Twitter, Facebook)
- ✅ **Geographic Analysis**: National, regional, local message classification
- ✅ **Candidate Messages**: Individual candidate message tracking
- ✅ **Data Relationships**: Proper foreign key relationships maintained

## Continuous Integration

This test suite is designed to run in CI/CD environments and provides:
- Comprehensive coverage of all API endpoints
- Realistic data scenarios for Phase 2 functionality
- Performance and load testing capabilities
- Clear pass/fail criteria for deployment gates