// Local-only test entry. Never referenced by production wrangler.toml.
import worker, {epicWeekPurge,epicWeekStart} from '../../../server/worker.js';
export default { ...worker, async fetch(req,env,ctx){
 const u=new URL(req.url);
 if(u.pathname==='/__purge') {
  const e=u.searchParams.has('fail')?{...env,EPIC:{delete:async()=>{throw Error('test R2 failure')}}}:env;
  try{return Response.json(await epicWeekPurge(e,+(u.searchParams.get('now'))||Date.now()));}catch(e){return Response.json({failed:true});}
 }
 if(u.pathname==='/__r2')return Response.json({exists:!!(await env.EPIC.head(u.searchParams.get('key')))});
 if(u.pathname==='/__week')return Response.json({cut:epicWeekStart(+u.searchParams.get('now'))});
 return worker.fetch(req,env,ctx);
}};
