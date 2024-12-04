from setuptools import setup, find_packages

setup(
    name="arbitrage_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'web3>=6.11.1',
        'python-dotenv>=1.0.0',
        'requests>=2.31.0',
        'aiohttp>=3.9.1',
        'eth-typing>=3.5.1',
        'eth-utils>=2.3.1',
        'typing-extensions>=4.8.0',
        'pydantic>=2.5.2',
        'SQLAlchemy>=2.0.23',
        'psutil>=5.9.6',
        'python-json-logger>=2.0.7',
        'tenacity>=8.2.3',
        'eth-abi>=4.2.1'
    ],
)
