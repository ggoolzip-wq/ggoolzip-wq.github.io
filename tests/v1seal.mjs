// 테스트 도우미: 예전(v1) 금고 암호문 만들기 (대표 키 HKDF → AES-GCM), 개발 pepper
const [,, mainKey, userId, json] = process.argv; const enc = new TextEncoder(); const pepper = 'ggoolzip-dev-pepper';
const ikm = await crypto.subtle.importKey('raw', enc.encode(mainKey.trim()), 'HKDF', false, ['deriveKey']);
const salt = new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode('ggoolzip-vault-salt:' + pepper)));
const k = await crypto.subtle.deriveKey({ name: 'HKDF', hash: 'SHA-256', salt, info: enc.encode('ggoolzip-subkeys:v1:' + userId) }, ikm, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
const iv = crypto.getRandomValues(new Uint8Array(12));
const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: enc.encode(userId) }, k, enc.encode(json)));
const b64 = u => Buffer.from(u).toString('base64'); console.log(JSON.stringify({ iv: b64(iv), ct: b64(ct) }));
