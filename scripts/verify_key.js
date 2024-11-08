const { ethers } = require('ethers');

async function main() {
    const privateKey = '02e4a21d278fadc16703a7b475576e2cb1dc5deb09c5488b096cc59ac37bf729';

    // Try different methods of creating wallet
    console.log('\nTrying different methods to create wallet...');

    // Method 1: Direct from private key
    try {
        const wallet1 = new ethers.Wallet(privateKey);
        console.log('\nMethod 1 - Direct from private key:');
        console.log('Address:', wallet1.address);
    } catch (e) {
        console.log('Method 1 failed:', e.message);
    }

    // Method 2: With 0x prefix
    try {
        const wallet2 = new ethers.Wallet(`0x${privateKey}`);
        console.log('\nMethod 2 - With 0x prefix:');
        console.log('Address:', wallet2.address);
    } catch (e) {
        console.log('Method 2 failed:', e.message);
    }

    // Method 3: Using fromPrivateKey
    try {
        const wallet3 = ethers.Wallet.fromPrivateKey(Buffer.from(privateKey, 'hex'));
        console.log('\nMethod 3 - Using fromPrivateKey:');
        console.log('Address:', wallet3.address);
    } catch (e) {
        console.log('Method 3 failed:', e.message);
    }

    console.log('\nExpected address: 0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801');
}

main()
    .then(() => process.exit(0))
    .catch(error => {
        console.error(error);
        process.exit(1);
    });
