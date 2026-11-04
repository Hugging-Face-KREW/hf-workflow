from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,sys,json,time
from meter import OUT,save
HERE=Path(__file__).resolve().parent
initial=json.loads((OUT/'L11/result.json').read_text())
if initial['status']!='local_pipeline_completed' or not initial['after_feedback']['semantic_complete']:raise SystemExit('Initial local test must pass full coverage before main runs')
IDS=['L01','L02','L03','L04','L05','L06','L07','L08','L09','L10']

def run(identifier):
 log=OUT/(identifier+'-run.log');started=time.time()
 with log.open('a') as f:
  result=subprocess.run([sys.executable,str(HERE/'run_legacy.py'),identifier],stdout=f,stderr=subprocess.STDOUT)
 record={'experiment':identifier,'exit_code':result.returncode,'elapsed_seconds':time.time()-started,'log':str(log)}
 print(identifier,record,flush=True);return record
records=[]
with ThreadPoolExecutor(max_workers=2) as pool:
 for future in as_completed([pool.submit(run,i) for i in IDS]):
  records.append(future.result());save(OUT/'execution-progress.json',records)
print('All bounded existing-family runs ended',flush=True)
