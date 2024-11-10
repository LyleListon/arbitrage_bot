from setuptools import setup, find_packages

setup(
    name="arbitrage_bot_dashboard",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask==3.0.3',
        'flask-socketio==5.3.6',
        'flask-cors==4.0.2',
        'eventlet==0.35.2',
        'python-dotenv==1.0.0',
        'web3==6.5.0',
        'eth-account==0.9.0',
        'requests==2.32.2',
        'tenacity==8.2.2',
        'pandas',
        'numpy'
    ],
    entry_points={
        'console_scripts': [
            'run-dashboard=dashboard.app:main',
        ],
    }
)
