#!/bin/bash

# Script to run tests for assurhabitat_agents project
# Usage: ./run_tests.sh [options]
#
# Options:
#   -v, --verbose     Run tests in verbose mode
#   -c, --coverage    Generate coverage report
#   -f, --fast        Skip slow tests
#   -h, --help        Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
VERBOSE=""
COVERAGE=""
FAST=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=src/assurhabitat_agents --cov-report=html --cov-report=term"
            shift
            ;;
        -f|--fast)
            FAST="-m 'not slow'"
            shift
            ;;
        -h|--help)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose     Run tests in verbose mode"
            echo "  -c, --coverage    Generate coverage report"
            echo "  -f, --fast        Skip slow tests"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}   Running AssurHabitat Agents Tests${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Please install test dependencies:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
echo ""

# Build pytest command
PYTEST_CMD="pytest tests/ $VERBOSE $COVERAGE $FAST"

# Execute
if $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}===========================================${NC}"
    echo -e "${GREEN}   All tests passed! ✓${NC}"
    echo -e "${GREEN}===========================================${NC}"
    
    # Show coverage report location if generated
    if [ -n "$COVERAGE" ]; then
        echo ""
        echo -e "${YELLOW}Coverage report generated:${NC}"
        echo "  HTML: htmlcov/index.html"
    fi
else
    echo ""
    echo -e "${RED}===========================================${NC}"
    echo -e "${RED}   Some tests failed! ✗${NC}"
    echo -e "${RED}===========================================${NC}"
    exit 1
fi

