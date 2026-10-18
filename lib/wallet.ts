import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
type Provider={request:(args:{method:string;params?:unknown[]})=>Promise<unknown>;on?:(event:string,fn:(...args:unknown[])=>void)=>void;removeListener?:(event:string,fn:(...args:unknown[])=>void)=>void};
declare global{interface Window{ethereum?:Provider}}
export async function connectWallet(onSent?:(hash:string)=>void){
 const p=window.ethereum;if(!p)throw Error('Install MetaMask or a compatible wallet to post or stake. You can inspect every recorded receipt without one.');
 const accounts=await p.request({method:'eth_requestAccounts'}) as string[];if(!accounts[0])throw Error('Choose an account in your wallet.');
 if(await p.request({method:'eth_chainId'})!=='0xf22f'){
  try{await p.request({method:'wallet_switchEthereumChain',params:[{chainId:'0xf22f'}]})}catch(e){if((e as {code?:number}).code!==4902)throw e;await p.request({method:'wallet_addEthereumChain',params:[{chainId:'0xf22f',chainName:'GenLayer StudioNet',nativeCurrency:{name:'GEN',symbol:'GEN',decimals:18},rpcUrls:['https://studio.genlayer.com/api'],blockExplorerUrls:['https://explorer-studio.genlayer.com']}]})}
 }
 const provider:Provider={request:async args=>{
  if(args.method==='eth_sendTransaction'){
   const tx=args.params?.[0] as Record<string,unknown>;
   const result=await p.request({...args,params:[{...tx,chainId:'0xf22f',type:'0x0',gasPrice:'0x0',value:tx.value??'0x0'}]});
   if(typeof result==='string'&&/^0x[\da-f]{64}$/i.test(result))onSent?.(result);return result;
  }return p.request(args);
 }};
 return {account:accounts[0].toLowerCase(),client:createClient({chain:studionet,account:accounts[0] as `0x${string}`,provider})};
}
