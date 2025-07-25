#!/bin/bash

# Reform UK Messaging API Test Script using curl
# This script tests all API endpoints using curl commands

set -e  # Exit on any error

# Configuration
API_BASE_URL="http://localhost:8000"
CONTENT_TYPE="Content-Type: application/json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data_file=$4
    
    echo -e "${YELLOW}Testing:${NC} $description"
    echo -e "${BLUE}$method${NC} $API_BASE_URL$endpoint"
    
    if [ -n "$data_file" ]; then
        echo -e "${BLUE}Data file:${NC} $data_file"
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "$CONTENT_TYPE" \
            -d @"$data_file" \
            "$API_BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            "$API_BASE_URL$endpoint")
    fi
    
    # Split response and status code
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    echo -e "${BLUE}Response Code:${NC} $http_code"
    echo -e "${BLUE}Response Body:${NC}"
    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        print_success "$description - SUCCESS"
        return 0
    else
        print_error "$description - FAILED (HTTP $http_code)"
        return 1
    fi
}

create_test_data() {
    print_header "Creating Test Data Files"
    
    # Create temporary directory for test data
    TEST_DIR="/tmp/reform_api_test"
    mkdir -p "$TEST_DIR"
    
    # Twitter message
    cat > "$TEST_DIR/twitter_message.json" << 'EOF'
{
    "source_type": "twitter",
    "source_name": "Reform UK Twitter Test",
    "source_url": "https://twitter.com/reformparty_uk",
    "content": "🚨 TEST MESSAGE: Immigration figures show record highs while British families struggle. When will this government put Britain first? #BritainFirst #Immigration #ReformUK #TestMessage",
    "url": "https://twitter.com/reformparty_uk/status/test123456789",
    "published_at": "2024-04-20T12:00:00Z",
    "message_type": "post",
    "metadata": {
        "hashtags": ["BritainFirst", "Immigration", "ReformUK", "TestMessage"],
        "mentions": [],
        "urls": [],
        "metrics": {
            "retweet_count": 50,
            "like_count": 150,
            "reply_count": 25,
            "quote_count": 10
        },
        "tweet_type": "post"
    },
    "raw_data": {
        "tweet_id": "test123456789",
        "author_id": "reformparty_test"
    }
}
EOF

    # Website message
    cat > "$TEST_DIR/website_message.json" << 'EOF'
{
    "source_type": "website",
    "source_name": "Reform UK Website Test",
    "source_url": "https://www.reformparty.uk",
    "content": "TEST ARTICLE: Reform UK Calls for Comprehensive Immigration Reform\n\nReform UK today announced a comprehensive immigration reform package designed to address the ongoing crisis affecting British communities. The party outlined several key policy proposals including enhanced border security, a merit-based immigration system, and increased support for British workers.\n\nThis test article demonstrates the website content submission functionality of the messaging analysis API.",
    "url": "https://www.reformparty.uk/test/immigration-reform-package",
    "published_at": "2024-04-20T14:30:00Z",
    "message_type": "article",
    "metadata": {
        "title": "Reform UK Calls for Comprehensive Immigration Reform",
        "word_count": 78,
        "url_path": "/test/immigration-reform-package",
        "category": "Immigration Policy"
    },
    "raw_data": {
        "scraper": "website_test"
    }
}
EOF

    # Facebook message
    cat > "$TEST_DIR/facebook_message.json" << 'EOF'
{
    "source_type": "facebook",
    "source_name": "Reform UK Facebook Test",
    "source_url": "https://www.facebook.com/ReformPartyUK",
    "content": "🇬🇧 TEST POST: BRITAIN FIRST POLICIES FOR BRITISH PEOPLE 🇬🇧\n\nReform UK is committed to putting British families first. Our comprehensive policy platform includes:\n\n✅ Controlled immigration that serves Britain\n✅ Energy independence through domestic production\n✅ NHS reform that puts patients first\n✅ Education focused on core subjects\n\nThis is a test post for the messaging analysis API. #ReformUK #BritainFirst #TestPost",
    "url": "https://www.facebook.com/ReformPartyUK/posts/test567890123456789",
    "published_at": "2024-04-20T16:45:00Z",
    "message_type": "post",
    "metadata": {
        "post_type": "status",
        "engagement": {
            "likes": 1500,
            "comments": 250,
            "shares": 400
        }
    },
    "raw_data": {
        "post_id": "test567890123456789",
        "page_id": "reformpartyuk_test"
    }
}
EOF

    # Meta Ads message
    cat > "$TEST_DIR/meta_ads_message.json" << 'EOF'
{
    "source_type": "meta_ads",
    "source_name": "Meta Ads Library Test",
    "source_url": "https://www.facebook.com/ads/library",
    "content": "STOP THE BOATS - TEST AD | Britain's borders need control. Mass immigration affects housing, jobs, and public services. Vote Reform UK for common sense immigration policies. | Take Back Control | Learn More About Our Policies",
    "url": "https://www.facebook.com/ads/library/?id=test123456789012345678",
    "published_at": "2024-04-20T08:00:00Z",
    "message_type": "ad",
    "metadata": {
        "page_name": "Reform UK Test",
        "funding_entity": "Reform UK Limited",
        "currency": "GBP",
        "publisher_platforms": ["Facebook", "Instagram"],
        "estimated_audience_size": {
            "lower_bound": 25000,
            "upper_bound": 50000
        },
        "delivery_dates": {
            "start": "2024-04-20T08:00:00Z",
            "stop": "2024-04-27T23:59:59Z"
        },
        "spend": {
            "lower_bound": 2500,
            "upper_bound": 5000
        },
        "impressions": {
            "lower_bound": 250000,
            "upper_bound": 400000
        },
        "demographics": {
            "age": ["35-44", "45-54", "55-64"],
            "gender": ["men", "women"]
        },
        "delivery_regions": ["England", "Wales", "Scotland"]
    },
    "raw_data": {
        "ad_id": "test123456789012345678",
        "page_id": "reformpartyuk_test_ads"
    }
}
EOF

    # Bulk messages
    cat > "$TEST_DIR/bulk_messages.json" << 'EOF'
{
    "messages": [
        {
            "source_type": "facebook",
            "source_name": "Reform UK Facebook Bulk Test",
            "content": "Bulk test message 1: Reform UK stands for British values and common sense policies.",
            "url": "https://www.facebook.com/ReformPartyUK/posts/bulk_test_1",
            "published_at": "2024-04-20T18:00:00Z",
            "message_type": "post"
        },
        {
            "source_type": "twitter",
            "source_name": "Reform UK Twitter Bulk Test",
            "content": "Bulk test message 2: It's time for real change in British politics! #ReformUK #Change",
            "url": "https://twitter.com/reformparty_uk/status/bulk_test_2",
            "published_at": "2024-04-20T18:30:00Z",
            "message_type": "post",
            "metadata": {
                "hashtags": ["ReformUK", "Change"]
            }
        }
    ]
}
EOF

    # Invalid message (missing content)
    cat > "$TEST_DIR/invalid_message.json" << 'EOF'
{
    "source_type": "twitter",
    "source_name": "Reform UK Twitter Test"
}
EOF

    # Invalid source type
    cat > "$TEST_DIR/invalid_source.json" << 'EOF'
{
    "source_type": "invalid_source",
    "source_name": "Test Source",
    "content": "Test content"
}
EOF

    # Duplicate message
    cat > "$TEST_DIR/duplicate_message.json" << 'EOF'
{
    "source_type": "twitter",
    "source_name": "Reform UK Twitter Test",
    "content": "Duplicate test message for API testing purposes",
    "url": "https://twitter.com/reformparty_uk/status/duplicate_test_123",
    "published_at": "2024-04-20T18:00:00Z"
}
EOF

    print_success "Test data files created in $TEST_DIR"
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        exit 1
    fi
    print_success "curl is available"
    
    # Check if jq is available (optional, for pretty JSON)
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed - JSON responses will not be formatted"
    else
        print_success "jq is available for JSON formatting"
    fi
}

test_api_connectivity() {
    print_header "Testing API Connectivity"
    
    # Test root endpoint
    test_endpoint "GET" "/" "Root endpoint"
    
    # Test health check
    test_endpoint "GET" "/health" "Health check endpoint"
}

test_info_endpoints() {
    print_header "Testing Information Endpoints"
    
    # Test sources list
    test_endpoint "GET" "/api/v1/sources" "List sources"
    
    # Test message statistics
    test_endpoint "GET" "/api/v1/messages/stats" "Message statistics"
}

test_single_messages() {
    print_header "Testing Single Message Submission"
    
    # Test each message type
    test_endpoint "POST" "/api/v1/messages/single" "Submit Twitter message" "$TEST_DIR/twitter_message.json"
    test_endpoint "POST" "/api/v1/messages/single" "Submit Website article" "$TEST_DIR/website_message.json"
    test_endpoint "POST" "/api/v1/messages/single" "Submit Facebook post" "$TEST_DIR/facebook_message.json"
    test_endpoint "POST" "/api/v1/messages/single" "Submit Meta Ads message" "$TEST_DIR/meta_ads_message.json"
}

test_bulk_messages() {
    print_header "Testing Bulk Message Submission"
    
    test_endpoint "POST" "/api/v1/messages/bulk" "Submit bulk messages" "$TEST_DIR/bulk_messages.json"
}

test_error_cases() {
    print_header "Testing Error Cases"
    
    # Test missing required field
    echo -e "${YELLOW}Testing:${NC} Invalid message (missing content)"
    response=$(curl -s -w "\n%{http_code}" -X "POST" \
        -H "$CONTENT_TYPE" \
        -d @"$TEST_DIR/invalid_message.json" \
        "$API_BASE_URL/api/v1/messages/single")
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    echo -e "${BLUE}Response Code:${NC} $http_code"
    echo -e "${BLUE}Response Body:${NC}"
    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
    
    if [ "$http_code" -eq 422 ]; then
        print_success "Validation error correctly returned (HTTP $http_code)"
    else
        print_error "Expected validation error (422), got HTTP $http_code"
    fi
    
    # Test invalid source type
    echo -e "\n${YELLOW}Testing:${NC} Invalid source type"
    response=$(curl -s -w "\n%{http_code}" -X "POST" \
        -H "$CONTENT_TYPE" \
        -d @"$TEST_DIR/invalid_source.json" \
        "$API_BASE_URL/api/v1/messages/single")
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    echo -e "${BLUE}Response Code:${NC} $http_code"
    echo -e "${BLUE}Response Body:${NC}"
    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
    
    if [ "$http_code" -eq 422 ]; then
        print_success "Invalid source type correctly rejected (HTTP $http_code)"
    else
        print_error "Expected validation error (422), got HTTP $http_code"
    fi
}

test_duplicate_handling() {
    print_header "Testing Duplicate Message Handling"
    
    # Submit the same message twice
    echo -e "${YELLOW}Submitting message first time:${NC}"
    test_endpoint "POST" "/api/v1/messages/single" "First submission" "$TEST_DIR/duplicate_message.json"
    
    echo -e "\n${YELLOW}Submitting same message again:${NC}"
    response=$(curl -s -w "\n%{http_code}" -X "POST" \
        -H "$CONTENT_TYPE" \
        -d @"$TEST_DIR/duplicate_message.json" \
        "$API_BASE_URL/api/v1/messages/single")
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    echo -e "${BLUE}Response Code:${NC} $http_code"
    echo -e "${BLUE}Response Body:${NC}"
    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
    
    # Check if it's marked as duplicate/warning
    if echo "$response_body" | grep -q "warning\|duplicate" 2>/dev/null; then
        print_success "Duplicate correctly detected"
    else
        print_warning "Duplicate detection may not be working as expected"
    fi
}

final_statistics() {
    print_header "Final API Statistics"
    
    test_endpoint "GET" "/api/v1/messages/stats" "Final message statistics"
    test_endpoint "GET" "/api/v1/sources" "Final sources list"
}

cleanup() {
    print_header "Cleanup"
    
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
        print_success "Test data files cleaned up"
    fi
}

main() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "    Reform UK Messaging API Test Suite (curl)    "
    echo "=================================================="
    echo -e "${NC}"
    
    # Check dependencies
    check_dependencies
    
    # Create test data files
    create_test_data
    
    # Test API connectivity first
    if ! test_api_connectivity; then
        print_error "API server is not responding. Please start it with:"
        echo "  uvicorn src.api.main:app --reload"
        cleanup
        exit 1
    fi
    
    # Run all tests
    test_info_endpoints
    test_single_messages
    test_bulk_messages
    test_error_cases
    test_duplicate_handling
    final_statistics
    
    # Cleanup
    cleanup
    
    print_header "Test Suite Complete"
    print_success "All API tests completed!"
    echo -e "\n${BLUE}Additional Resources:${NC}"
    echo "  • Interactive API docs: $API_BASE_URL/docs"
    echo "  • Redoc documentation: $API_BASE_URL/redoc"
    echo "  • Dashboard: streamlit run dashboard.py"
    echo "  • API specification: API_SPECIFICATION.md"
    echo ""
}

# Check if API server is specified as argument
if [ $# -eq 1 ]; then
    API_BASE_URL="$1"
    echo -e "${YELLOW}Using custom API URL:${NC} $API_BASE_URL"
fi

# Run main function
main