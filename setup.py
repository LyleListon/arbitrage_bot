from setuptools import setup, find_packages

setup(
    name="arbitrage_bot_dashboard",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask==3.1.0',
        'flask-socketio==5.4.1',
        'flask-cors==5.0.0',
        'eventlet==0.38.0',
        'python-dotenv==1.0.1',
        'web3==7.6.0',
        'eth-account==0.13.4',
        'requests==2.32.3',
        'tenacity==9.0.0',
        'pandas',
        'numpy'
    ],
    entry_points={
        'console_scripts': [
            'run-dashboard=dashboard.app:main',
        ],
    }
)
