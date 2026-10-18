import {NextResponse} from 'next/server';
import {read} from '@/lib/server-chain';
import {preview} from '@/lib/evidence-preview';
import type {Take} from '@/lib/domain';
export async function POST(req:Request){try{const {id,url}=await req.json();if(typeof id!=='string'||!/^take-\d+$/.test(id)||typeof url!=='string'||url.length>2000)throw Error('Choose a take and paste a permanent evidence URL.');const info=await read<Record<string,string>>('TakeResolver','preflight',[id,url]);const take=await read<Take>('Takes','get_take',[id]);const source=await preview(url,take.rule,info);return NextResponse.json({info,...source,message:'URL shape and allowlist verified by contract read. Capture metadata and source text were fetched for this non-authoritative preview. Validators repeat these checks on submission. This preview does not decide the verdict.'})}catch(e){return NextResponse.json({error:e instanceof Error?e.message:'Evidence preflight failed'},{status:400})}}
