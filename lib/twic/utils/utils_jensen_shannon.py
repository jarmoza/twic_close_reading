import math
from datetime import datetime
import json
import os
#from decimal import Decimal

# See here for description of Jensen-Shannon Divergence http://enterotype.embl.de/enterotypes.html
# Jensen-Shannon "Distance" may be further calculated as SQRT(Jensen-Shannon Divergence)
# NOTE: Functions assume len(prob_dist1) == len(prob_dist2), conditional removed for speed

# def entropy(prob_dist, base=math.e):
#     return -sum([p * math.log(p,base) for p in prob_dist if p != 0])

# def jsd(prob_dists, base=math.e):
#     weight = 1/float(len(prob_dists)) #all same weight
#     js_left = [0,0,0]
#     js_right = 0
#     for pd in prob_dists:
#         js_left[0] += pd[0]*weight
#         js_left[1] += pd[1]*weight
#         js_left[2] += pd[2]*weight
#         js_right += weight*entropy(pd,base)
#     return entropy(js_left)-js_right

# "Newton" division c/o http://fredrik-j.blogspot.ca/2008/07/making-division-in-python-faster.html

def load_src(name, fpath):
    import os, imp
    return imp.load_source(name, os.path.join(os.path.dirname(__file__), fpath))

# from lib.mpmath.libmp.libintmath import giant_steps, lshift, rshift
# from lib.mpmath.libmp.backend import gmpy, MPZ

# load_src("libintmath", "../lib/mpmath/libmp/libintmath.py")
load_src("libintmath", os.path.join("..", "..", "..", "lib", "mpmath", "libmp", "libintmath.py"))
from libintmath import giant_steps, lshift, rshift

# load_src("backend", "../lib/mpmath/libmp/backend.py")
load_src("backend", os.path.join("..", "..", "..", "lib", "mpmath", "libmp", "backend.py"))
from backend import gmpy, MPZ

# load_src("twic_malletscript", "../general/twic_malletscript.py")
load_src("twic_malletscript", os.path.join("..", "general", "twic_malletscript.py"))
from twic_malletscript import TWiC_MalletScript

Mallet_FileTopicProportions = TWiC_MalletScript.Mallet_FileTopicProportions


START_PREC = 15

def size(x):
    if isinstance(x, (int, long)):
        return int(math.log(x,2))
    # GMPY support
    #return gmpy.numdigits(x,2)
    return len("{0:f}".format(x))

def newdiv(p, q):
    szp = size(p)
    szq = size(q)
    print szp
    print szq
    szr = szp - szq
    if min(szp, szq, szr) < 2*START_PREC:
        print 'Floor div'
        return p//q
    r = (1 << (2*START_PREC)) // (q >> (szq - START_PREC))
    last_prec = START_PREC
    for prec in giant_steps(START_PREC, szr):
        a = lshift(r, prec-last_prec+1)
        b = rshift(r**2 * rshift(q, szq-prec), 2*last_prec)
        r = a - b
        last_prec = prec
    return ((p >> szq) * r) >> szr

def kullback_leibler_divergence(prob_dist1, prob_dist2, base=math.e):

    # Calculate the Kullback-Leibler divergence

    kl_divergence = 0

    # To avoid zero in the numerator or denominator
    pseudo_count = 0.000001

    for index in range(len(prob_dist1)):
        #print 'KL Divergence PD1[{0}]: {1} PD2[{0}]: {2}'.format(index, prob_dist1[index], prob_dist2[index])
        #print "newdiv == {0}".format(newdiv(float(prob_dist1[index]) + pseudo_count, float(prob_dist2[index]) + pseudo_count))
        #kl_divergence += prob_dist1[index] * math.log(newdiv(float(prob_dist1[index]) + pseudo_count, float(prob_dist2[index]) + pseudo_count), base)
        kl_divergence += prob_dist1[index] * math.log((float(prob_dist1[index]) + pseudo_count) / (float(prob_dist2[index]) + pseudo_count), base)

    return kl_divergence


def jensen_shannon_divergence(prob_dist1, prob_dist2, base=math.e):

    # Calculate "M" == (prob_dist1 + prob_dist2) / 2
    # m = []
    len_pd1 = len(prob_dist1)
    m = [0.5 * (prob_dist1[index] + prob_dist2[index]) for index in range(len_pd1)]
    # for index in range(0, len(prob_dist1)):
    #     m.append(0.5 * (prob_dist1[index] + prob_dist2[index]))
    #print 'M: {0}'.format(m)

    # Return Jensen-Shannon Divergence
    jsd = 0.5 * (kullback_leibler_divergence(prob_dist1, m, base) + kullback_leibler_divergence(prob_dist2, m, base))

    #print 'Jensen-Shannon Divergence: {0}'.format(jsd)

    return jsd


def jensen_shannon_distance(prob_dist1, prob_dist2, base=math.e):
    return math.sqrt(jensen_shannon_divergence(prob_dist1, prob_dist2, base))
