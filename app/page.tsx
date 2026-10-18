import CalledIt from '@/components/called-it';
import {recorded} from '@/lib/server-chain';
export default function Page(){return <CalledIt initial={recorded} view="feed"/>}
