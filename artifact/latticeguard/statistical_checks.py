from __future__ import annotations
from math import sqrt

def wilson_interval(successes:int, total:int, z:float=1.96) -> tuple[float,float]:
    if total==0: return (0.0,0.0)
    phat=successes/total
    denom=1+z*z/total
    center=(phat+z*z/(2*total))/denom
    margin=z*sqrt((phat*(1-phat)+z*z/(4*total))/total)/denom
    return (max(0.0,center-margin), min(1.0,center+margin))

def pass_rate_summary(successes:int,total:int) -> dict[str,float]:
    lo,hi=wilson_interval(successes,total)
    return {'successes':successes,'total':total,'rate':successes/total if total else 0.0,'wilson_low':lo,'wilson_high':hi}
