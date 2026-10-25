"""Validate and freeze a synthetic per-person agent trial; never generates answers.

Uses the Python standard library only. Running this on a partial or malformed trial
fails visibly unless missing adult outputs were deliberately permitted.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,csv,hashlib,json,math,statistics,sys

SCORE_ITEMS={'depression':[3,5,10,13,16,17,21],
             'anxiety':[2,4,7,9,15,19,20],
             'stress':[1,6,8,11,12,14,18]}
NONPARTICIPATION={'declined','consent_not_established'}

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def is_int(value):return isinstance(value,int) and not isinstance(value,bool)
def is_number(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def validate_record(record,route,persona,questions,contract,run_id):
    errors=[];pid=route['person_id']
    if not isinstance(record,dict):return ['Record is not an object']
    required=set(contract['required_top_level'])
    if set(record)!=required:errors.append('Top-level keys differ from the exact response contract')
    if record.get('synthetic_data') is not True:errors.append('synthetic_data must be boolean true')
    if record.get('run_id')!=run_id:errors.append('run_id does not match run metadata')
    if record.get('person_id')!=pid:errors.append('person_id does not match assigned file')
    if record.get('population_layer')!=route['population_layer']:errors.append('population_layer does not match roster')
    if route['population_layer']=='under18_excluded' or persona['age']<18:errors.append('Under-18 output is prohibited')
    participation=record.get('participation')
    if participation not in contract['allowed_participation']:errors.append('Invalid participation status')
    if not isinstance(record.get('simulation_interface'),str) or not record.get('simulation_interface','').strip():errors.append('Missing simulation_interface string')
    summary=record.get('constructed_week_summary')
    if summary is not None and not isinstance(summary,str):errors.append('constructed_week_summary must be string or null')
    if participation in ['completed','partial'] and not isinstance(summary,str):errors.append('An interviewed record needs a brief explicitly fictional recent-context summary')
    for field in ['construction_notes','visible_process_notes']:
        value=record.get(field)
        if not isinstance(value,list) or len(value)>6 or not all(isinstance(x,str) for x in value):errors.append(field+' must be an array of at most six strings')
    ids={q['id'] for q in questions}
    answers=record.get('answers');sources=record.get('answer_source');missing=record.get('missing_reasons')
    if not isinstance(answers,dict) or set(answers)!=ids:errors.append('answers must contain exactly all 54 IDs')
    if not isinstance(sources,dict) or set(sources)!=ids:errors.append('answer_source must contain exactly all 54 IDs')
    if not isinstance(missing,dict):errors.append('missing_reasons must be an object')
    if not isinstance(answers,dict) or not isinstance(sources,dict) or not isinstance(missing,dict):return errors
    null_ids={key for key in ids if answers.get(key) is None}
    if set(missing)!=null_ids:errors.append('missing_reasons keys must equal null-answer IDs')
    for key,reason in missing.items():
        if reason not in contract['allowed_null_reasons']:errors.append(key+': invalid missing reason')
    for q in questions:
        key=q['id'];value=answers.get(key);source=sources.get(key)
        if source not in contract['answer_source_values']:errors.append(key+': invalid answer_source')
        if value is None:
            if source in ['persona_fact','constructed_context']:errors.append(key+': null value cannot be a factual/constructed substantive answer')
            continue
        if q['type']=='select_multiple':
            if not isinstance(value,list) or not value or not all(is_int(v) for v in value):
                errors.append(key+': expected a nonempty integer array');continue
            if len(value)>q['max_selections'] or len(set(value))!=len(value):errors.append(key+': too many or duplicate selections')
            if any(v not in q['allowed_values'] for v in value):errors.append(key+': invalid selection code')
            if any(v in q['exclusive_values'] for v in value) and len(value)!=1:errors.append(key+': exclusive code mixed with other selections')
            declined=value==[99]
            if declined and source!='declined':errors.append(key+': 99 needs declined provenance')
            if not declined and source not in ['persona_fact','constructed_context']:errors.append(key+': ordinary array needs factual/constructed provenance')
        else:
            if q['type'] in ['integer','select_one'] and not is_int(value):errors.append(key+': expected integer code/value');continue
            if q['type']=='decimal' and not is_number(value):errors.append(key+': expected finite numeric value');continue
            if 'allowed_values' in q and value not in q['allowed_values']:errors.append(key+': invalid code/range')
            if 'minimum' in q and (not is_number(value) or value<q['minimum'] or value>q['maximum']):errors.append(key+': outside numeric range')
            if value in [97,98,99] and 'allowed_values' in q:
                expected={97:'not_applicable',98:'unknown',99:'declined'}[value]
                if source!=expected:errors.append(key+': sentinel source must be '+expected)
            elif source not in ['persona_fact','constructed_context']:errors.append(key+': substantive value needs factual/constructed provenance')
        if source=='persona_fact' and key not in ['B01','B02','B03']:errors.append(key+': persona contains no measured recent item response; use constructed_context or an appropriate missing code')
    if participation in NONPARTICIPATION:
        if any(answers.get(key) is not None for key in ids):errors.append('Nonparticipation must have all answers null')
        if any(sources.get(key)!='not_asked' or missing.get(key)!='not_asked' for key in ids):errors.append('Nonparticipation uses not_asked for every item')
        if summary is not None:errors.append('Nonparticipation must not have an invented interview-week summary')
    if participation in ['completed','partial']:
        value=answers.get('B01');age=persona['age'];expected=1 if age<=29 else 2 if age<=44 else 3
        if value not in [None,99,expected]:errors.append('B01 contradicts persona age')
        value=answers.get('B03');expected=1 if persona['months_at_site']<1 else 2 if persona['months_at_site']<6 else 3
        if value not in [None,99,expected]:errors.append('B03 contradicts persona site tenure')
        if route['population_layer']=='primary_worker':
            expected=1 if persona['worker_skill_group']=='General/unskilled' else 2
            if answers.get('B02') not in [None,99,expected]:errors.append('B02 contradicts persona broad manual role')
    if route['population_layer']=='exploratory_staff':
        if answers.get('B02') is not None:errors.append('Exploratory staff B02 must be null')
        if participation in ['completed','partial'] and (sources.get('B02')!='not_applicable' or missing.get('B02')!='not_applicable'):errors.append('Exploratory staff B02 needs not_applicable source/reason')
    days=answers.get('W01');hours=answers.get('W02')
    if is_number(days) and is_number(hours) and hours>24*days:errors.append('W02 exceeds 24 hours per worked day / positive hours with zero days')
    return errors

def score(answers):
    out={}
    for name,indices in SCORE_ITEMS.items():
        values=[answers.get(f'D{i:02}') for i in indices]
        complete=all(is_int(v) and 0<=v<=3 for v in values)
        raw=sum(values) if complete else None
        out['dass_'+name+'_raw']=raw
        out['dass_'+name+'_score']=raw*2 if raw is not None else None
    return out

def stats(values):
    values=[v for v in values if v is not None]
    return dict(n=len(values),mean=statistics.mean(values) if values else None,
      median=statistics.median(values) if values else None,
      sample_sd=statistics.stdev(values) if len(values)>1 else None,
      minimum=min(values) if values else None,maximum=max(values) if values else None)

def write_csv(path,rows,fields):
    with Path(path).open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)

def finalize(packet,run_dir,allow_incomplete=False):
    packet=Path(packet).resolve();run_dir=Path(run_dir).resolve()
    metadata=read_json(run_dir/'run_metadata.json')
    run_id=metadata.get('run_id')
    if not isinstance(run_id,str) or not run_id.strip() or metadata.get('synthetic_data') is not True:raise ValueError('run_metadata.json needs nonempty run_id and synthetic_data=true')
    with (packet/'RUN_ROSTER.csv').open(encoding='utf-8-sig',newline='') as f:roster=list(csv.DictReader(f))
    route_by_id={r['person_id']:r for r in roster}
    expected={r['person_id'] for r in roster if r['population_layer']!='under18_excluded'}
    excluded={r['person_id'] for r in roster if r['population_layer']=='under18_excluded'}
    if len(expected)!=146 or len(excluded)!=4:raise ValueError('Packet routing counts changed; review the packet explicitly')
    questions=read_json(packet/'questionnaire/QUESTIONNAIRE_FULL.json')['questions']
    contract=read_json(packet/'RESPONSE_CONTRACT.json')
    paths={p.stem:p for p in (run_dir/'responses').glob('*.json')}
    extra=set(paths)-expected
    if extra:raise ValueError('Unexpected or excluded-person output files: '+', '.join(sorted(extra)))
    missing=expected-set(paths)
    errors=[];records=[]
    for pid,path in sorted(paths.items()):
        try:
            rec=read_json(path);persona=read_json(packet/'personas'/f'{pid}.json')
            failures=validate_record(rec,route_by_id[pid],persona,questions,contract,run_id)
            errors.extend(pid+': '+e for e in failures)
            if not failures:records.append(rec)
        except Exception as e:errors.append(pid+': '+str(e))
    if missing and not allow_incomplete:errors.append('Missing adult outputs: '+', '.join(sorted(missing)))
    if errors:raise ValueError('Validation failed; no freeze or score outputs written:\n'+'\n'.join(errors))
    input_paths=[packet/'RUN_ROSTER.csv',packet/'PERSONALITY_PROFILES_ALL_150.csv',packet/'questionnaire/QUESTIONNAIRE_FULL.json',packet/'RESPONSE_CONTRACT.json',packet/'RESPONDENT_SUBAGENT_PROMPT.md']
    input_paths.extend(sorted((packet/'personas').glob('*.json')))
    freeze=dict(synthetic_data=True,run_id=run_id,status='incomplete' if missing else 'complete',
      frozen_at_utc=datetime.now(timezone.utc).isoformat(),metadata_sha256=sha(run_dir/'run_metadata.json'),
      input_sha256={str(path.relative_to(packet)):sha(path) for path in input_paths},
      response_sha256={pid:sha(path) for pid,path in sorted(paths.items())},missing_adult_outputs=sorted(missing),excluded_under18=sorted(excluded))
    freeze_path=run_dir/'freeze_manifest.json'
    if freeze_path.exists():
        existing=read_json(freeze_path)
        for key in ['run_id','status','metadata_sha256','input_sha256','response_sha256','missing_adult_outputs','excluded_under18']:
            if existing.get(key)!=freeze.get(key):raise ValueError('An existing freeze differs: '+key+'. Preserve this run and create a separately labeled new run.')
        freeze=existing
    else:freeze_path.write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf-8')
    flat=[];provenance=[]
    for rec in records:
        row={k:rec[k] for k in ['synthetic_data','run_id','person_id','population_layer','participation']}
        for q in questions:
            key=q['id'];value=rec['answers'][key]
            row[key]=';'.join(str(v) for v in value) if isinstance(value,list) else value
            provenance.append(dict(synthetic_data=True,run_id=run_id,person_id=rec['person_id'],item_id=key,
              answer_source=rec['answer_source'][key],missing_reason=rec['missing_reasons'].get(key)))
        row.update(score(rec['answers']));flat.append(row)
    fields=['synthetic_data','run_id','person_id','population_layer','participation']+[q['id'] for q in questions]+[f'dass_{name}_{suffix}' for name in SCORE_ITEMS for suffix in ['raw','score']]
    write_csv(run_dir/'SYNTHETIC_response_table.csv',flat,fields)
    write_csv(run_dir/'SYNTHETIC_item_provenance.csv',provenance,['synthetic_data','run_id','person_id','item_id','answer_source','missing_reason'])
    routing=[]
    for r in roster:
        pid=r['person_id']
        routing.append(dict(synthetic_data=True,person_id=pid,population_layer=r['population_layer'],
          execution_result='excluded_under18_no_questionnaire' if pid in excluded else 'missing_output' if pid in missing else 'validated_record_present'))
    write_csv(run_dir/'routing_log.csv',routing,['synthetic_data','person_id','population_layer','execution_result'])
    description=dict(synthetic_data=True,run_id=run_id,run_status=freeze['status'],
      limitations='Generated role-play only; not human observations, questionnaire validation or an empirical hypothesis test. English proxy does not validate a translation.',
      planned_adults=len(expected),validated_records=len(records),missing_outputs=sorted(missing),excluded_under18=len(excluded),layers={})
    for layer in ['primary_worker','exploratory_staff']:
        subset=[r for r in records if r['population_layer']==layer]
        score_rows=[row for row in flat if row['population_layer']==layer]
        item_summaries={}
        for q in questions:
            key=q['id'];values=[r['answers'][key] for r in subset]
            counts=Counter(json.dumps(v,ensure_ascii=False) for v in values)
            item_summaries[key]=dict(records=len(values),null_answers=sum(v is None for v in values),coded_value_counts=dict(counts))
        description['layers'][layer]=dict(validated_records=len(subset),participation=dict(Counter(r['participation'] for r in subset)),
          score_descriptives={name:stats([row['dass_'+name+'_score'] for row in score_rows]) for name in SCORE_ITEMS},
          answer_sources=dict(Counter(source for rec in subset for source in rec['answer_source'].values())),items=item_summaries)
    (run_dir/'SYNTHETIC_descriptives.json').write_text(json.dumps(description,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return description

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',default=str(Path(__file__).resolve().parent))
    parser.add_argument('--run-dir',required=True)
    parser.add_argument('--allow-incomplete',action='store_true')
    args=parser.parse_args()
    try:
        result=finalize(args.packet,args.run_dir,args.allow_incomplete)
        print(json.dumps({k:result[k] for k in ['synthetic_data','run_id','run_status','planned_adults','validated_records','missing_outputs','excluded_under18']},indent=2))
    except Exception as exc:
        print(str(exc),file=sys.stderr);sys.exit(1)
