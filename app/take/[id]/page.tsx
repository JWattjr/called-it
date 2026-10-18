import CalledIt from '@/components/called-it';
import {recorded} from '@/lib/server-chain';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <CalledIt initial={recorded} view="take" takeId={id}/>}
