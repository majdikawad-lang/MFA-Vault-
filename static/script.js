async function captureHand(){
let r=await fetch('/capture_hand',{method:'POST'});
let d=await r.json();
document.getElementById('status').innerHTML='✔️';
}
async function verifyHand(){
let r=await fetch('/verify_hand',{method:'POST'});
let d=await r.json();
document.getElementById('status').innerHTML='✔️';
}
