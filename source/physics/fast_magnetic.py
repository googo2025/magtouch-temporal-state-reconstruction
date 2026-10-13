"""Finite cylindrical magnets via azimuthal current sheets.

Independent implementation: angular current-loop integration uses complete
elliptic integrals; axial integration uses Gauss-Legendre quadrature. The model
is the SAME uniformly axial-magnetized cylinder as the charge-sheet reference.
No field map, real-data calibration or dipole approximation is introduced.
Lengths mm, polarization mu0*M in T, output uT. Exterior only.
"""
from functools import lru_cache
import numpy as np
from scipy.special import ellipk,ellipe
from scipy.spatial.transform import Rotation

@lru_cache(None)
def gauss(n):return np.polynomial.legendre.leggauss(n)

def cylinder_local_uT(local_mm,radius_mm=2.5,height_mm=1.,order=12):
    X=np.asarray(local_mm,float); shape=X.shape
    if shape[-1]!=3 or not np.isfinite(X).all() or radius_mm<=0 or height_mm<=0:raise ValueError('bad magnetic geometry')
    x=X.reshape(-1,3);rho=np.linalg.norm(x[:,:2],axis=1);a=radius_mm;h=height_mm/2
    if np.any((rho<=a)&(abs(x[:,2])<=h)):raise ValueError('exterior cylinder field only')
    nodes,w=gauss(order);zz=x[:,2,None]-h*nodes[None,:];rr=rho[:,None]
    den=np.sqrt((a+rr)**2+zz**2);Q=(a-rr)**2+zz**2
    m=np.clip(4*a*rr/den**2,0,1-1e-16);K=ellipk(m);E=ellipe(m)
    Bz=((K+(a*a-rr**2-zz**2)/Q*E)/den)@(w*h)/(2*np.pi)
    safe=np.maximum(rr,1e-30)
    Br=((zz/safe*(-K+(a*a+rr**2+zz**2)/Q*E))/den)@(w*h)/(2*np.pi)
    axis=rho<a*1e-5
    # Near-axis analytic limits avoid cancellation in the off-axis loop formula.
    if axis.any():
        z=x[axis,2];zp=z+h;zm=z-h
        bz=.5*(zp/np.sqrt(zp*zp+a*a)-zm/np.sqrt(zm*zm+a*a))
        db=.5*a*a*((zp*zp+a*a)**-1.5-(zm*zm+a*a)**-1.5)
        Bz[axis]=bz;Br[axis]=-.5*rho[axis]*db
    out=np.c_[Br[:,None]*x[:,:2]/np.maximum(rho[:,None],1e-30),Bz]*1e6
    return out.reshape(shape)

def fields_external_fast(centers_mm,rotvec_rad,sensors_mm,signed_J,radius_mm=2.5,height_mm=1.,order=12,batch=256):
    C=np.asarray(centers_mm,float);V=np.asarray(rotvec_rad,float);S=np.asarray(sensors_mm,float);J=np.asarray(signed_J,float)
    if C.ndim==2:C=C[None];V=V[None]
    if C.shape!=V.shape or C.ndim!=3 or C.shape[-1]!=3 or J.shape!=(C.shape[1],):raise ValueError('bad shapes')
    if not all(np.isfinite(z).all() for z in (C,V,S,J)):raise ValueError('nonfinite input')
    R=Rotation.from_rotvec(V.reshape(-1,3)).as_matrix().reshape(*V.shape[:-1],3,3)
    result=[]
    for start in range(0,len(C),batch):
        cc=C[start:start+batch];rr=R[start:start+batch]
        local=np.einsum('tmsi,tmij->tmsj',S[None,None]-cc[:,:,None],rr)
        b=cylinder_local_uT(local,radius_mm,height_mm,order)
        world=np.einsum('tmsj,tmij->tmsi',b,rr)
        result.append(np.sum(world*J[None,:,None,None],axis=1))
    return np.concatenate(result)

def field_from_poses_fast(geometry,readout,poses,order=12):
    readout.validate();P=np.asarray(poses,float).reshape(-1,geometry.grid_side**2,6)
    B=fields_external_fast(geometry.centers()[None]+P[:,:,:3],P[:,:,3:],readout.sensor_positions_mm,geometry.polarities()*readout.polarization_T,
       geometry.magnet_diameter_mm/2,geometry.magnet_thickness_mm,order=order)
    B+=readout.ambient_world_uT
    return np.einsum('tsi,sij->tsj',B,readout.world_from_sensor).reshape(len(P),-1)
