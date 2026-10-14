"""Recompute public paper aggregates and matched-budget selections from scalar summaries."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1]
DATA_PATHS={'explicit_state_final138.json': 'methods/explicit_state/results/final138.json', 'shared_field_final529.json': 'methods/shared_field/results/final529.json', 'learning_histories.json': 'methods/shared_field/results/learning_histories.json', 'matched274.json': 'methods/shared_field/results/matched274.json', 'source_adaptation.json': 'methods/explicit_state/results/source_adaptation.json'}
def read(name):return json.loads((ROOT/DATA_PATHS[name]).read_text('utf-8'))
def close(a,b):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10),(a,b)
def main():
    e=read('explicit_state_final138.json');c=read('shared_field_final529.json')
    er=e['records'];cr=c['records'];assert len(er)==97 and len(cr)==101
    en=sum(x['scalars'] for x in er);cn=sum(x['scored_B_scalars'] for x in cr)
    ep=math.sqrt(sum(sum(x['SSE']) for x in er)/en);ea=sum(sum(x['SAE']) for x in er)/en
    cp=math.sqrt(sum(sum(y['SSE'] for y in x['channel']) for x in cr)/cn);ca=sum(sum(y['SAE'] for y in x['channel']) for x in cr)/cn
    close(ep,e['aggregate']['RMSE_uT']);close(ea,e['aggregate']['MAE_uT']);close(cp,c['pool_RMSE_uT']);close(ca,c['pool_MAE_uT'])
    groups={tip:[x['MSE'] for x in cr if x['tip']==tip] for tip in {x['tip'] for x in cr}}
    balanced=c['normalization_scale_uT']*math.sqrt(sum(sum(v)/len(v) for v in groups.values())/len(groups));close(balanced,c['equal_domain_equal_sequence_RMSE_uT'])
    curves=read('learning_histories.json');matched=read('matched274.json')
    for arm,values in curves['arms'].items():
        rows=[x for x in values if x['age']<=274];assert [x['age'] for x in rows]==list(range(1,275))
        best=min(rows,key=lambda x:x['dev']);fixed=rows[-1];assert best['age']==matched[arm]['best_age']
        close(curves['scale_uT']*math.sqrt(best['dev']),matched[arm]['best_RMSE_uT']);close(curves['scale_uT']*math.sqrt(fixed['dev']),matched[arm]['fixed274_RMSE_uT'])
    pure=curves['arms']['pure_frame'];assert len(pure)==600 and min(pure,key=lambda x:x['dev'])['age']==529
    controls=read('source_adaptation.json')['pooled_RMSE_uT'];benefit=100*(1-controls['measured_measured']/controls['generated_generated'])
    print(json.dumps(dict(status='PUBLIC_SCALAR_RECOMPUTATION_PASS',explicit_sequences=len(er),shared_sequences=len(cr),explicit_scalars=en,shared_scalars=cn,explicit_pooled_RMSE_uT=ep,explicit_MAE_uT=ea,shared_pooled_RMSE_uT=cp,shared_MAE_uT=ca,shared_equal_domain_equal_sequence_RMSE_uT=balanced,source_adaptation_reduction_percent=benefit,matched274_arms=5,selected_shared_epoch=529,P95='Frozen exact residual quantiles; cannot recompute quantiles from SSE/SAE alone'),indent=2))
if __name__=='__main__':main()
