const ethers = require('ethers');

const privateKey = '02e4a21d278fadc16703a7b475576e2cb1dc5deb09c5488b096cc59ac37bf729';
const wallet = new ethers.Wallet(privateKey);
console.log('Address:', wallet.address);
console.log('Expected:', '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801');
