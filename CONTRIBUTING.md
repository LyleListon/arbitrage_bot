# Contributing to Arbitrage Bot

Thank you for your interest in contributing to the Arbitrage Bot project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and constructive environment for all contributors.

## How to Contribute

1. Fork the repository
2. Create a new branch for your feature/fix: `git checkout -b feature-name`
3. Make your changes
4. Write/update tests if necessary
5. Run tests locally to ensure everything passes
6. Commit your changes: `git commit -m "Description of changes"`
7. Push to your fork: `git push origin feature-name`
8. Create a Pull Request

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the documentation if you're changing functionality
3. Ensure all tests pass
4. Link any relevant issues in your PR description
5. Request review from maintainers

## Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   pip install -r requirements.txt
   ```
3. Copy `configs/local.template.json` to `configs/local.json` and configure
4. Run tests to ensure everything is set up correctly

## Testing

- Run JavaScript tests: `npx hardhat test`
- Run Python tests: `python -m pytest test/`

## Reporting Bugs

When reporting bugs, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Node.js version, Python version)
- Relevant logs or error messages

## Feature Requests

For feature requests, please:

- Clearly describe the feature
- Explain why it would be useful
- Provide examples of how it would be used
- Consider potential impacts on existing functionality

## Questions or Need Help?

- Create an issue with the "question" label
- Provide as much context as possible

## Security Issues

For security issues, please DO NOT create a public issue. Instead:

1. Document the issue
2. Send details privately to the maintainers
3. Allow time for a response before disclosure

Thank you for contributing!
