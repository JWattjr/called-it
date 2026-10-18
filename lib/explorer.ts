export const EXPLORER='https://explorer-studio.genlayer.com';
export function explorer(kind:'address'|'tx',value:string){
 if(!(kind==='address'?/^0x[\da-f]{40}$/i:/^0x[\da-f]{64}$/i).test(value))throw Error('Invalid explorer identifier');
 return `${EXPLORER}/${kind}/${value}`;
}
