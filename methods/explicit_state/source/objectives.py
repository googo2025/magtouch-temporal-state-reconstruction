"""Portable extraction of unchanged scientific helpers from the pinned parent.

No private paths, dataset loader, automatic worker, training controller or
checkpoint loader is included. Callers must provide authorized inputs.
"""
from pathlib import Path
import hashlib

DOSE = dict(native_history_frames=0, field_frames=0)

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def features(a, source, scale):
    import numpy as np
    import torch
    ids = np.flatnonzero(a['available']); reset = np.zeros(len(ids), bool); dt = np.zeros(len(ids))
    last = -1
    for k, i in enumerate(ids):
        changed = last < 0 or bool(a['reset'][last+1:i+1].any()) or a['b0_id'][i] != a['b0_id'][last]
        reset[k] = changed
        if not changed:
            dt[k] = (int(a['t_ns'][i])-int(a['t_ns'][last]))*1e-9
        last = int(i)
    x = np.concatenate((a['B_'+source][ids]/scale, np.ones((len(ids), 15)), dt[:, None]), 1)
    assert np.isfinite(x).all() and reset[0]
    return torch.as_tensor(x), reset, ids

def position_metrics(diff):
    import numpy as np
    flat = diff.reshape(-1, 3); t = flat.mean(0)
    def score(x):
        v = np.linalg.norm(x, axis=1)
        return dict(mean_mm=float(v.mean()), P95_mm=float(np.quantile(v, .95)), vector_RMSE_mm=float(np.sqrt(np.mean(v*v))))
    return dict(raw=score(flat), unique_Trial_XYZ=score(flat-t), translation_mm=t.tolist(), count=len(flat),
                scope='One constant XYZ across all paired snapshots and points of the complete Trial; diagnostic only')

def train_trial(model, decoder, a, source, scale, cores, backward=False, metrics=False):
    import numpy as np
    import torch
    x, reset, ids = features(a, source, scale)
    torch.set_num_threads(1); h = model.encode(x, reset); DOSE['native_history_frames'] += len(ids)
    torch.set_num_threads(cores)
    leaf = h.detach().requires_grad_(True) if backward else h
    bi = np.unique(np.linspace(0, len(ids)-1, min(64, len(ids))).round().astype(int))
    lookup = np.full(len(a['t_ns']), -1, np.int64); lookup[ids] = np.arange(len(ids))
    slots = np.flatnonzero(a['weak_valid']); wi = lookup[a['weak_native_indices'][slots]]
    assert (wi >= 0).all() and len(wi) > 0
    union = np.unique(np.r_[bi, wi]); index = {int(v): k for k, v in enumerate(union)}
    q = model.decode(leaf[union])
    bidx = torch.tensor([index[int(v)] for v in bi]); widx = torch.tensor([index[int(v)] for v in wi])
    DOSE['field_frames'] += len(bi)
    pred = decoder.field(q[bidx]); target = torch.as_tensor(a['B_'+source][ids[bi]])
    LB = ((pred-target)/scale).square().mean()
    u = decoder.geometry(q[widx]); tu = torch.as_tensor(a['weak_u_mm'][slots], dtype=torch.float64)
    tq = torch.as_tensor(a['weak_q'][slots], dtype=torch.float64)
    pc, pr = decoder.poses(q[widx]); tc, tr = decoder.poses(tq)
    LU = ((u-tu)/.5).square().mean(); LC = ((pc-tc)/.5).square().mean(); LR = (pr-tr).square().mean()
    loss = LB+LU+LC+.1*LR
    if not torch.isfinite(loss):
        raise ValueError('Nonfinite unchanged Trial objective')
    result = dict(total=float(loss.detach()), B=float(LB.detach()), u=float(LU.detach()), centers=float(LC.detach()),
                  rotation=float(LR.detach()), B_RMSE_uT=float((pred-target).square().mean().sqrt().detach()),
                  native_history_frames=len(ids), physics_loss_frames=len(bi), weak_shape_states=len(wi))
    if backward:
        loss.backward()
        if leaf.grad is None or not torch.isfinite(leaf.grad).all():
            raise ValueError('Missing/nonfinite history VJP')
        torch.set_num_threads(1); h.backward(leaf.grad); torch.set_num_threads(cores)
        if not all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()):
            raise ValueError('Missing/nonfinite trainable gradients')
    if metrics:
        result['full_u'] = position_metrics((u-tu).detach().numpy())
        result['magnet_centers'] = position_metrics((pc-tc).detach().numpy())
        result['B_rotation_spatial_translation'] = 'N/A'
    return result

def validation_trial(model, decoder, field, ra, a, scale, dest, display=None):
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    mapping, _, b0, sensors, j, datum = ra
    x, reset, ids = features(a, 'real', scale); torch.set_num_threads(1)
    pred = np.full((len(a['t_ns']), 15), np.nan)
    saved_q = np.full((80, mapping.ndof), np.nan) if display is not None else None
    slotmap = {int(v): k for k, v in enumerate(display)} if display is not None else {}
    with torch.inference_mode():
        h = model.encode(x, reset); DOSE['native_history_frames'] += len(ids)
        for begin in range(0, len(ids), 32):
            ii = ids[begin:begin+32]; q = model.decode(h[begin:begin+len(ii)])
            if not torch.isfinite(q).all():
                raise ValueError('Nonfinite validation q')
            c, r = decoder.poses(q); c = c.numpy(); r = r.numpy()
            rv = Rotation.from_matrix(r.reshape(-1, 3, 3)).as_rotvec().reshape(-1, 25, 3)
            DOSE['field_frames'] += len(ii)
            value = field.fields_external_fast(c+[0., 0., datum], rv, sensors, j, order=24).reshape(-1, 15)-b0
            if not np.isfinite(value).all():
                raise ValueError('Nonfinite validation field')
            pred[ii] = value
            for k, i in enumerate(ii):
                if int(i) in slotmap:
                    saved_q[slotmap[int(i)]] = q[k].numpy()
    d = pred[ids]-a['B_real'][ids]
    sse = np.square(d).sum(0); sae = abs(d).sum(0); n = len(ids)
    result = dict(uid=a['record']['uid'], tip=a['record']['tip'], native_frames=len(a['t_ns']), valid_frames=n,
                  scalar_count=n*15, SSE_channels_uT2=sse.tolist(), SAE_channels_uT=sae.tolist(),
                  RMSE_uT=float(np.sqrt(sse.sum()/(15*n))), MAE_uT=float(sae.sum()/(15*n)),
                  channel_RMSE_uT=np.sqrt(sse/n).tolist(), channel_MAE_uT=(sae/n).tolist(),
                  Hall_RMSE_uT=np.sqrt(sse.reshape(5, 3).sum(1)/(3*n)).tolist(), guard_failures=0)
    if dest is not None:
        path = dest/(hashlib.sha256(result['uid'].encode()).hexdigest()[:24]+'.npz')
        values = dict(t_ns=a['t_ns'], source_row=a['source_row'], b0_id=a['b0_id'], valid=a['available'],
                      reference_B_uT=a['B_real'], predicted_B_uT=pred)
        if saved_q is not None:
            values.update(display_native_indices=display, display_q=saved_q)
        np.savez_compressed(path, **values)
        result['saved_output'] = dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)
    return result

def aggregate(records):
    import numpy as np
    assert len(records) == 97 and len({r['uid'] for r in records}) == 97
    assert sum(r['native_frames'] for r in records) == 234195
    sse = np.sum([r['SSE_channels_uT2'] for r in records], 0); sae = np.sum([r['SAE_channels_uT'] for r in records], 0)
    n = sum(r['valid_frames'] for r in records)
    return dict(denominator_Trials=97, complete_Trials=97, native_frames=234195, valid_frames=n, scalar_count=n*15,
                RMSE_uT=float(np.sqrt(sse.sum()/(15*n))), MAE_uT=float(sae.sum()/(15*n)),
                channel_RMSE_uT=np.sqrt(sse/n).tolist(), channel_MAE_uT=(sae/n).tolist(),
                Hall_RMSE_uT=np.sqrt(sse.reshape(5, 3).sum(1)/(3*n)).tolist(),
                macro_Trial_RMSE_uT=float(np.mean([r['RMSE_uT'] for r in records])),
                selection='Pooled measured-B squared error, all97 original noncone validation Trials, unchanged native channels and baseline',
                calibration_fits=0, spatial_translation='N/A', weak_shape_used_for_selection=False,
                blind_TEST=False, guard_failures=0)
