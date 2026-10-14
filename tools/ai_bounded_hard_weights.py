"""TRAIN-only bounded example weights; no resampling or case duplication."""
import math


def class_normalized_weights(rows, hard_positive, hard_negative, factor=2.):
    if not math.isfinite(factor) or not 1 <= factor <= 2:
        raise ValueError('A registered bounded factor in[1,2] is required')
    ids=[r['image_id'] for r in rows]
    if len(ids)!=len(set(ids)) or any(r['split']!='train' for r in rows):
        raise ValueError('Exactly one weight per unique TRAIN source image')
    positive={r['image_id'] for r in rows if int(r['fractured'])}
    negative=set(ids)-positive
    hp,hn=set(hard_positive),set(hard_negative)
    if not hp<=positive or not hn<=negative or hp&hn:
        raise ValueError('Hard catalogs must respect explicit TRAIN labels')
    if not positive or not negative: raise ValueError('Both TRAIN classes required')
    weights={}
    for members,hard in ((positive,hp),(negative,hn)):
        mean=(len(members)+(factor-1)*len(hard))/len(members)
        for image_id in members:
            weights[image_id]=(factor if image_id in hard else 1.)/mean
        if not math.isclose(sum(weights[i] for i in members),len(members),rel_tol=1e-12):
            raise AssertionError('Within-class total example mass changed')
    if min(weights.values())<.5 or max(weights.values())>2:
        raise AssertionError('Example weight cap violated')
    return weights


def fixtures():
    rows=[dict(image_id=str(i),split='train',fractured=i<8) for i in range(20)]
    hp={'0','1'};hn={str(i) for i in range(8,14)}
    w=class_normalized_weights(rows,hp,hn)
    assert w['0']==1.6 and w['2']==.8
    assert w['8']==4/3 and w['14']==2/3
    assert all(x==1 for x in class_normalized_weights(rows,hp,hn,1).values())
    for bad in ({'8'}, {'missing'}):
        try: class_normalized_weights(rows,bad,hn)
        except ValueError: pass
        else: raise AssertionError('Invalid hard-positive label/membership accepted')
    try: class_normalized_weights([dict(rows[0],split='val'),*rows[1:]],hp,hn)
    except ValueError: pass
    else: raise AssertionError('VAL accepted')
    return dict(status='hand_calculated_weight_and_membership_fixtures_passed',
        positive_hard_weight=1.6,positive_other_weight=.8,
        normal_hard_weight=4/3,normal_other_weight=2/3,
        both_class_weight_means=1,no_duplicate_samples=True)


if __name__=='__main__':
    import json
    print(json.dumps(fixtures(),indent=2))
