"""Archived C_posts geometry and exact finite-rotation rigid magnet map."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.spatial.transform import Rotation

FACES = np.array([[0,3,2,1],[4,5,6,7],[0,1,5,4],
                  [1,2,6,5],[2,3,7,6],[3,0,4,7]])


def euler_rotation(theta):
    """Rz Ry Rx, first and second derivatives w.r.t. x/y/z Euler angles."""
    mats=[]; first=[]; second=[]
    for axis, a in enumerate(theta):
        c=np.cos(a); s=np.sin(a)
        K=np.zeros((3,3))
        i,j=((1,2),(2,0),(0,1))[axis]
        K[j,i]=1; K[i,j]=-1
        outer=np.zeros((3,3)); outer[axis,axis]=1
        m=c*np.eye(3)+(1-c)*outer+s*K
        dm=-s*np.eye(3)+s*outer+c*K
        d2m=-c*np.eye(3)+c*outer-s*K
        mats.append(m); first.append(dm); second.append(d2m)
    def product(orders):
        selected=[(mats,first,second)[orders[k]][k] for k in range(3)]
        return selected[2]@selected[1]@selected[0]
    R=product([0,0,0]); dR=np.empty((3,3,3)); d2R=np.empty((3,3,3,3))
    for a in range(3):
        order=[0,0,0]; order[a]=1; dR[a]=product(order)
        for b in range(3):
            order=[0,0,0]; order[a]+=1; order[b]+=1
            d2R[a,b]=product(order)
    return R,dR,d2R


@dataclass
class Mesh:
    nodes: np.ndarray
    cells: np.ndarray
    dimensions: np.ndarray
    fixed_nodes: np.ndarray
    top_quads: np.ndarray
    centers: np.ndarray
    metadata: dict

    @classmethod
    def from_operator(cls, path):
        with np.load(Path(path), allow_pickle=False) as a:
            p=a['source_nodes'].copy(); cells=a['source_cells'].astype(np.int32)
            centers=a['magnet_centers'].copy(); meta=json.loads(str(a['metadata_json'].item()))
        xe=p[cells]
        dims=xe.max(axis=1)-xe.min(axis=1)
        expected=xe[:,0,None,:]+((FINE_SIGNS+1)/2)[None,:,:]*dims[:,None,:]
        if not np.allclose(expected,xe,rtol=0,atol=1e-10):
            raise ValueError('Archived mesh has non-axis-aligned Hex8 cells')
        faces=cells[:,FACES].reshape(-1,4)
        _,ix,count=np.unique(np.sort(faces,axis=1),axis=0,return_index=True,return_counts=True)
        boundary=faces[ix[count==1]]
        top=np.all(np.isclose(p[boundary,2],p[:,2].max()),axis=1)
        fixed=np.unique(boundary[~top])
        return cls(p,cells,dims,fixed,boundary[top],centers,meta)


FINE_SIGNS=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
                    [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])


class RigidMap:
    """Regular node displacements + 25 exact six-DOF magnet motions.

    Input angle convention is Euler xyz; output poses use axis-angle rotvec to
    match the archived finite-cylinder magnetic interface.
    """
    def __init__(self, mesh):
        self.mesh=mesh; p=mesh.nodes; n=len(p)
        self.owner=np.full(n,-1,dtype=int)
        for j,c in enumerate(mesh.centers):
            inside=(np.sum((p[:,:2]-c[:2])**2,axis=1)<2.5**2-1e-10)
            inside &= (p[:,2]>=c[2]-.5-1e-9)&(p[:,2]<=c[2]+.5+1e-9)
            if np.any(self.owner[inside]>=0): raise ValueError('Overlapping rigid-node regions')
            self.owner[inside]=j
        fixed=np.zeros(n,bool); fixed[mesh.fixed_nodes]=True
        if np.any(fixed&(self.owner>=0)): raise ValueError('Rigid node meets fixed boundary')
        regular=np.flatnonzero((~fixed)&(self.owner<0))
        self.regular_rows=(regular[:,None]*3+np.arange(3)).ravel()
        self.nregular=len(self.regular_rows)
        self.rid=np.arange(self.nregular,self.nregular+6*len(mesh.centers)).reshape(-1,6)
        self.ndof=self.nregular+6*len(mesh.centers)
        self.groups=[np.flatnonzero(self.owner==j) for j in range(len(mesh.centers))]
        if min(map(len,self.groups))<8: raise ValueError('Unresolved rigid magnet')

    def state(self, q, want_jacobian=True):
        q=np.asarray(q,dtype=float)
        if q.shape!=(self.ndof,) or not np.isfinite(q).all(): raise ValueError('Bad reduced state')
        u=np.zeros((len(self.mesh.nodes),3))
        u.ravel()[self.regular_rows]=q[:self.nregular]
        rows=[self.regular_rows]; cols=[np.arange(self.nregular)]; values=[np.ones(self.nregular)]
        rotations=[]
        for j,nodes in enumerate(self.groups):
            v=q[self.rid[j]]; r=self.mesh.nodes[nodes]-self.mesh.centers[j]
            R,dR,d2R=euler_rotation(v[3:]); rotations.append((R,dR,d2R))
            u[nodes]=v[:3]+r@R.T-r
            if want_jacobian:
                jac=np.empty((len(nodes),3,6)); jac[:,:,:3]=np.eye(3)
                jac[:,:,3:]=np.einsum('aik,nk->nia',dR,r)
                rows.append(np.broadcast_to(nodes[:,None,None]*3+np.arange(3)[None,:,None],jac.shape).ravel())
                cols.append(np.broadcast_to(self.rid[j][None,None,:],jac.shape).ravel())
                values.append(jac.ravel())
        T=None
        if want_jacobian:
            T=sparse.coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(cols))),
                               shape=(u.size,self.ndof)).tocsr(); T.eliminate_zeros()
        return u,T,rotations

    def geometric_hessian(self, force, rotations):
        """The exact chain-rule term sum_i g_i d²u_i/dq² for rotations."""
        g=np.asarray(force).reshape(-1,3); blocks=[]
        for j,nodes in enumerate(self.groups):
            r=self.mesh.nodes[nodes]-self.mesh.centers[j]
            blocks.append(np.einsum('ni,abik,nk->ab',g[nodes],rotations[j][2],r))
        return np.array(blocks)

    def magnetic_poses(self,q):
        v=np.asarray(q)[self.rid]; out=v.copy()
        out[:,3:]=Rotation.from_euler('xyz',v[:,3:]).as_rotvec()
        return out

