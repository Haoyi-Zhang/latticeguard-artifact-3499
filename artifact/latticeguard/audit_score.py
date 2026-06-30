from __future__ import annotations

def grade(metrics: dict) -> dict:
    score=0; notes=[]
    if metrics.get('obligations',0)>=2500: score+=20
    else: notes.append('increase applicable obligations')
    if metrics.get('predicate_rows',0)>=2000: score+=20
    else: notes.append('increase predicate witness diversity')
    if metrics.get('bounded_model_cases',0)>=70000: score+=20
    else: notes.append('increase finite semantic bound')
    if metrics.get('sources',0)>=100: score+=20
    else: notes.append('increase native/public sources')
    if metrics.get('counterexamples',0)>=1500: score+=20
    else: notes.append('increase minimized replay evidence')
    return {'score':score,'grade':'A' if score>=90 else 'B' if score>=75 else 'C','notes':notes,'status':'PASS' if score>=90 else 'REVIEW'}
