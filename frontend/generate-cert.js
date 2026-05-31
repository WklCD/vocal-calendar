import { generateKeyPairSync, createSign, createCertificate } from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const { privateKey, publicKey } = generateKeyPairSync('rsa', {
  modulusLength: 2048,
});

const sign = createSign('SHA256');
sign.update('localhost');
sign.end();
const signature = sign.sign(privateKey);

const certDir = path.join(__dirname, 'certs');
if (!fs.existsSync(certDir)) {
  fs.mkdirSync(certDir, { recursive: true });
}

fs.writeFileSync(path.join(certDir, 'localhost.crt'), publicKey.export({ type: 'spki', format: 'pem' }));
fs.writeFileSync(path.join(certDir, 'localhost.key'), privateKey.export({ type: 'pkcs8', format: 'pem' }));

console.log('SSL certificates generated successfully!');
console.log('Certificate: certs/localhost.crt');
console.log('Private key: certs/localhost.key');
