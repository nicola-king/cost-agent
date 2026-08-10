async function api(path){const r=await fetch(path);if(!r.ok)throw new Error(`${path}: ${r.status}`);return r.json();}
window.CCI={api};
