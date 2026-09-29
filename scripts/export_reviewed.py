#!/usr/bin/env python3
"""Export only explicitly reviewed records and reviewed portions of text."""
import argparse,gzip,json,pathlib,datetime,importlib.util
p=argparse.ArgumentParser();p.add_argument('--raw',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/raw');p.add_argument('--output',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/reviewed-records.json');a=p.parse_args()
spec=importlib.util.spec_from_file_location('dataset',pathlib.Path(__file__).with_name('dataset.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
selected={
'events':['0002ca9a-633c-46b3-9e5c-46656bfd909c','00046052-6e72-4394-97fd-4927bc0852ca','00051d87-0ed4-48f6-9b77-460a9cb3efa6','0007028f-2bb4-42d2-a75d-dc50fd29e139','00110e63-11c5-4f7d-8869-58cd1f557b87','00142a42-e623-420e-85a6-831406ab78c3','001e7dd3-be88-4f1c-8a90-6194ee51af8e'],
'chat_messages':['00006a0b-c468-40b4-9de3-f189410db719','00022c9f-2672-4019-80fc-ed5779cec0ed','0002851a-44db-4f92-91d6-e4f7b47e1a8a','00035349-5009-46a9-8c44-f1d5759c3265'],
'computer_use_sessions':['00036389-31c7-41ee-9de8-73f3d85d8c6d','0008813b-0e28-46d3-9bee-de05f99cedd3','00094e1a-ce0c-437c-a5c0-9ae8f9e44a76'],
'agent_memories':['0000a3d5-36ee-416d-a2a8-f155583edd58','0000ae36-c795-48a5-9afc-738bde2f0da3'],
'village_goals':['075e909b-9d44-4725-b11a-57c2079570de','0a7bfa90-f68f-4d57-afd4-6df5d9914e30','0d8c2395-b05e-476d-b914-90c1d6429dfc','0e58f48d-2fa2-4223-9205-37bbb228a87c'],
'agent_goals':['1f113278-c13c-47d6-8d53-10a4fc9b99ba','2462677d-677d-4f3e-aed3-52ccf1e7e2e4','25c64750-ffe8-4d07-8f9c-a15690ed16e1','25ff80f7-f15d-404c-afa8-9f00b647edc0','2b95ac82-3553-4a02-ae1c-70afd990f8eb'],
'summaries':['000b4301-4557-4a9f-b83e-ccf12e2786a3'],
'computer_use_turns':['00002725-e6f7-4e92-b001-336cfc0090b9','00002b24-e392-4558-bf6b-04a3c9e49e6e','000035dd-8cdc-478d-9253-09b74eb80b11','000037cc-2378-4d58-9e81-8cc8f831188d','00005e9f-7b24-4901-aeb2-1d3d2efa0627']}
sessions={}
with gzip.open(a.raw/'computer_use_sessions.jsonl.gz','rt') as f:
 for line in f:
  r=json.loads(line);sessions[r['id']]=r['agent_id']
records=[]
for table,ids in selected.items():
 wanted=set(ids)
 with gzip.open(a.raw/(table+'.jsonl.gz'),'rt') as f:
  for line in f:
   row=json.loads(line)
   if row['id'] not in wanted:continue
   n=m.normalized(row,sessions);note='Reviewed content field; other source fields are omitted.';form='Content field';field='content'
   if table=='events':content=row['data']['content'];field='data.content'
   elif table=='computer_use_sessions':content=row['session_goal'];field='session_goal'
   elif table=='village_goals':content=row['goal'];field='goal'
   elif table=='agent_goals':content=row['name'];field='name'
   elif table=='computer_use_turns':
    content=json.dumps({k:row['agent_action'].get(k) for k in ['action','coordinate','text']},indent=2);field='agent_action';note='Reviewed action only. Model messages, tool output, and screenshots are omitted.'
   else:content=row['content']
   if table=='agent_memories':content=content.split('\n\n')[0];form='Excerpt';note='Only the reviewed opening paragraph is published; the remainder of the memory is omitted.'
   if table=='summaries':content='\n'.join(content.splitlines()[1:4]);form='Excerpt';note='Only three reviewed entries are published. This is an AI-generated summary, not independently verified evidence.'
   if 'localhost:5002' in content:content=content.replace('localhost:5002','[local application address omitted]');form='Redacted content';note='The local application address was removed. Other source fields are omitted.'
   records.append({'id':n['id'],'table':table,'date':n['date'],'agent':n['agent'],'kind':n['kind'],'field':field,'content':content,'form':form,'review_note':note})
   wanted.remove(row['id'])
   if not wanted:break
 if wanted:raise ValueError('Missing reviewed records: '+str(wanted))
result={'version':1,'revision':json.loads((a.raw/'snapshot.json').read_text())['revision'],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'A manually reviewed, non-representative selection. Only the displayed content field or excerpt is included, not complete raw records.','records':records}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2));print('Exported',len(records),'reviewed records')
