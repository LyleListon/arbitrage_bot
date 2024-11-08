const { Web3 } = require('web3');

async function main() {
    try {
        const rpcUrl = 'https://eth-sepolia.g.alchemy.com/v2/kRXhWVt8YU_8LnGS20145F5uBDFbL_k0';
        console.log('Using RPC URL:', rpcUrl);

        const web3 = new Web3(rpcUrl);

        console.log('Checking connection...');
        const block = await web3.eth.getBlockNumber();
        console.log('Latest block:', block);

        const chainId = await web3.eth.getChainId();
        console.log('Chain ID:', chainId);

        console.log('Connection successful!');
    } catch (error) {
        console.error('Error:', error.message);
        if (error.cause) {
            console.error('Cause:', error.cause);
        }
    }
}

main().catch(console.error);
