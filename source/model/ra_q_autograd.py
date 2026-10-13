"""Source-exact RA RigidMap and exterior RA24 differentiable CPU consumer.

This is not a mechanics solver, material law, fitted field or forward surrogate.
Lengths mm, Euler xyz radians, polarization T, fields uT. Original exterior
guard and quadrature retained. SciPy elliptic values use analytic first VJPs.
"""
import numpy as np
import torch
from torch import nn
from scipy.special import ellipk, ellipe


class EllipticPair(torch.autograd.Function):
    @staticmethod
    def forward(ctx, m):
        if m.device.type != 'cpu' or m.dtype != torch.float64:
            raise ValueError('Qualified implementation is CPU FP64 only')
        a = m.detach().numpy()
        k = torch.from_numpy(np.asarray(ellipk(a))).to(m)
        e = torch.from_numpy(np.asarray(ellipe(a))).to(m)
        ctx.save_for_backward(m, k, e)
        return k, e

    @staticmethod
    def backward(ctx, gk, ge):
        m, k, e = ctx.saved_tensors
        safe = torch.where(m.abs() < 1e-7, torch.ones_like(m), m)
        dk = (e / (1 - m) - k) / (2 * safe)
        de = (e - k) / (2 * safe)
        dk0 = (np.pi / 2) * (1/4 + 18*m/64 + 75*m*m/256)
        de0 = (np.pi / 2) * (-1/4 - 6*m/64 - 15*m*m/256)
        dk = torch.where(m.abs() < 1e-7, dk0, dk)
        de = torch.where(m.abs() < 1e-7, de0, de)
        return (0 if gk is None else gk * dk) + (0 if ge is None else ge * de)


def euler_matrix(v):
    x, y, z = v.unbind(-1)
    cx, cy, cz = x.cos(), y.cos(), z.cos()
    sx, sy, sz = x.sin(), y.sin(), z.sin()
    return torch.stack((cz*cy, cz*sy*sx-sz*cx, cz*sy*cx+sz*sx,
                        sz*cy, sz*sy*sx+cz*cx, sz*sy*cx-cz*sx,
                        -sy, cy*sx, cy*cx), -1).reshape(*v.shape[:-1], 3, 3)


class RAQDecoder(nn.Module):
    def __init__(self, mapping, sensors, signed_j, baseline, datum):
        super().__init__()
        self.nregular = mapping.nregular
        self.ndof = mapping.ndof
        self.datum = float(datum)
        self.groups = [torch.as_tensor(x, dtype=torch.long) for x in mapping.groups]
        for key, value in dict(nodes=mapping.mesh.nodes, centers=mapping.mesh.centers,
                               regular_rows=mapping.regular_rows, rid=mapping.rid,
                               sensors=sensors, signed_j=signed_j, B0=baseline).items():
            dtype = torch.long if key in ('regular_rows', 'rid') else torch.float64
            self.register_buffer(key, torch.as_tensor(value, dtype=dtype))
        z, w = np.polynomial.legendre.leggauss(24)
        self.register_buffer('zquad', torch.as_tensor(z * .5))
        self.register_buffer('wquad', torch.as_tensor(w * .5))

    def poses(self, q):
        v = q[..., self.rid]
        return self.centers + v[..., :3], euler_matrix(v[..., 3:])

    def geometry(self, q):
        flat = q.new_zeros((*q.shape[:-1], self.nodes.numel()))
        flat = flat.index_copy(-1, self.regular_rows, q[..., :self.nregular])
        u = flat.reshape(*q.shape[:-1], len(self.nodes), 3)
        v = q[..., self.rid]
        rotations = euler_matrix(v[..., 3:])
        for j, ids in enumerate(self.groups):
            r = self.nodes[ids] - self.centers[j]
            moved = torch.einsum('...ij,nj->...ni', rotations[..., j, :, :], r)
            value = moved - r + v[..., j, None, :3]
            u = u.index_copy(-2, ids, value)
        return u

    def local_field(self, x):
        rho = torch.linalg.vector_norm(x[..., :2], dim=-1)
        if ((rho <= 2.5) & (x[..., 2].abs() <= .5)).any():
            raise ValueError('exterior cylinder field only')
        rr = rho[..., None]
        zz = x[..., 2, None] - self.zquad
        den = ((2.5 + rr).square() + zz.square()).sqrt()
        q = (2.5 - rr).square() + zz.square()
        m = (10 * rr / den.square()).clamp(0, 1 - 1e-16)
        k, e = EllipticPair.apply(m)
        bz = ((k + (6.25 - rr.square() - zz.square()) / q * e) / den * self.wquad).sum(-1) / (2*np.pi)
        safe = rr.clamp_min(1e-30)
        br = ((zz / safe * (-k + (6.25 + rr.square() + zz.square()) / q * e)) / den * self.wquad).sum(-1) / (2*np.pi)
        axis = rho < 2.5e-5
        z = x[..., 2]
        zp, zm = z + .5, z - .5
        bz_axis = .5 * (zp / (zp.square() + 6.25).sqrt() - zm / (zm.square() + 6.25).sqrt())
        db = .5 * 6.25 * ((zp.square() + 6.25).pow(-1.5) - (zm.square() + 6.25).pow(-1.5))
        bxy = br[..., None] * x[..., :2] / rho[..., None].clamp_min(1e-30)
        bxy = torch.where(axis[..., None], -.5 * db[..., None] * x[..., :2], bxy)
        bz = torch.where(axis, bz_axis, bz)
        return torch.cat((bxy, bz[..., None]), -1) * 1e6

    def field(self, q):
        c, r = self.poses(q)
        c = c + c.new_tensor([0., 0., self.datum])
        local = torch.einsum('...msi,...mij->...msj', self.sensors - c[..., :, None, :], r)
        b = self.local_field(local)
        world = torch.einsum('...msj,...mij->...msi', b, r)
        return (world * self.signed_j[..., None, None]).sum(-3).flatten(-2) - self.B0


class HistoryQ(nn.Module):
    """Only B15 + valid15 + elapsed native seconds enter the trainable network."""
    def __init__(self, ndof, nregular, bscale):
        super().__init__()
        self.history = nn.GRU(31, 64, batch_first=True).double()
        self.head = nn.Linear(64, ndof).double()
        nn.init.normal_(self.head.weight, std=1e-5)
        nn.init.zeros_(self.head.bias)
        scale = torch.ones(ndof, dtype=torch.float64)
        scale[nregular:] = torch.tensor([1., 1., 1., .1, .1, .1], dtype=torch.float64).repeat(25)
        self.register_buffer('q_unit_scale', scale)
        self.register_buffer('B_scale_uT', torch.tensor(float(bscale), dtype=torch.float64))

    def encode(self, features, reset):
        cuts = [0] + [int(i) for i in np.flatnonzero(reset) if i > 0] + [len(features)]
        out = []
        for a, b in zip(cuts[:-1], cuts[1:]):
            h, _ = self.history(features[a:b][None])
            out.append(h[0])
        return torch.cat(out)

    def decode(self, h):
        return self.head(h) * self.q_unit_scale
