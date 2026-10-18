// Legacy CLI transport compatibility for gasless StudioNet (documented reference pattern).
const original=globalThis.fetch;
globalThis.fetch=async(input,init)=>{
 const url=typeof input==='string'?input:input instanceof URL?input.href:input.url;
 if(url==='https://studio.genlayer.com/api'){
  const headers=new Headers(init?.headers);headers.set('User-Agent','Mozilla/5.0 CalledIt/1.0');init={...init,headers};
  if(typeof init.body==='string'){
   let body;try{body=JSON.parse(init.body)}catch{}
   if(body?.method==='eth_gasPrice'||body?.method==='eth_maxPriorityFeePerGas')return new Response(JSON.stringify({jsonrpc:'2.0',id:body.id,result:'0x3b9aca00'}),{headers:{'content-type':'application/json'}});
  }
 }
 return original(input,init);
};
