# Test Directory

## Structure

- `v2/`, `v3/`, `v4/`, `v5/` - Version-specific tests
- `integration/` - Cross-contract integration tests
- `utils/` - Test helpers and utilities

## Test Categories

### Unit Tests
- Individual contract functionality
- Function-level testing
- State management verification

### Integration Tests
- Cross-contract interactions
- DEX integration testing
- Flash loan functionality
- Price feed integration

### Security Tests
- Access control verification
- Circuit breaker testing
- Emergency scenarios
- Reentrancy protection

## Test Guidelines

1. All new features must include tests
2. Maintain 100% coverage for critical functions
3. Include both positive and negative test cases
4. Test edge cases and boundary conditions
5. Document test scenarios clearly

## Running Tests

```bash
# Run all tests
npx hardhat test

# Run specific version tests
npx hardhat test test/v5/*

# Run integration tests
npx hardhat test test/integration/*

# Run with coverage
npx hardhat coverage
```

## Test Environment Setup

1. Use Hardhat for local testing
2. Mock external contracts when necessary
3. Use snapshot/revert for state management
4. Maintain consistent test data

## Continuous Integration

- All tests must pass before merging
- Coverage reports generated automatically
- Gas usage optimization checks
- Security scanning integration
