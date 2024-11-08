import requests
import os
from dotenv import load_dotenv
import time


def main():
    address = '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801'
    
    # Use Etherscan API
    api_url = f'https://api.etherscan.io/api'
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': 0,
        'endblock': 99999999,
        'page': 1,
        'offset': 10,
        'sort': 'desc'
    }
    
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                print(f"Latest transactions for {address}:")
                for tx in data['result']:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(tx['timeStamp'])))
                    value_eth = float(tx['value']) / 1e18
                    print(f"\nTransaction at {timestamp}")
                    print(f"From: {tx['from']}")
                    print(f"To: {tx['to']}")
                    print(f"Value: {value_eth:.6f} ETH")
                    print(f"Hash: {tx['hash']}")
                    print(f"Status: {'Success' if tx['txreceipt_status'] == '1' else 'Failed'}")
            else:
                print(f"Error: {data['message']}")
    except Exception as e:
        print(f"Error checking Etherscan: {str(e)}")
    
    # Also check current balance
    params = {
        'module': 'account',
        'action': 'balance',
        'address': address,
        'tag': 'latest'
    }
    
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                balance_eth = float(data['result']) / 1e18
                print(f"\nCurrent balance: {balance_eth:.6f} ETH")
            else:
                print(f"Error getting balance: {data['message']}")
    except Exception as e:
        print(f"Error checking balance: {str(e)}")


if __name__ == '__main__':
    main()
