"""Target H: shared silicone displacement samples ->25 local bodies ->15 B.

No command, tip, measured B, recurrent encoder or trainable hardware parameter.
Samples must come from ONE continuous body field at the declared175 query points;
they are not independently predicted magnet poses. Mesh interpolation is not
invented here. This freezes the already validated local readout resolution.
"""
import torch
from torch import nn
from .finite_cylinder_field import Had239FieldGeometry,FiniteCylinderHallField

class SharedShapeToField(nn.Module):
    def __init__(self,packet):
        super().__init__()
        self.operator=FiniteCylinderHallField(Had239FieldGeometry(**packet['field_geometry']),order=24)
        for parameter in self.operator.parameters():parameter.requires_grad_(False)
        self.register_buffer('query_points_mm',torch.as_tensor(packet['probe_points_mm'],dtype=torch.float64))
        self.register_buffer('centers_mm',torch.as_tensor(packet['centers_mm'],dtype=torch.float64))
        self.probe_mm=float(packet['probe_mm']);self.datum_mm=float(packet['field_geometry']['mechanical_to_array_z_mm'])

    def local_poses(self,shared_u_samples_mm):
        if shared_u_samples_mm.shape[-2:]!=(175,3):raise ValueError('One shared field at175 declared probes, mm')
        u=shared_u_samples_mm.reshape(*shared_u_samples_mm.shape[:-2],25,7,3).to(self.centers_mm)
        if not torch.isfinite(u).all():raise ValueError('Nonfinite common deformation')
        identity=torch.eye(3,dtype=u.dtype,device=u.device)
        gradient=(identity+(u[...,1:4,:]-u[...,4:7,:])/(2*self.probe_mm)).transpose(-1,-2)
        if (torch.linalg.det(gradient)<=0).any():raise ValueError('Common field inverted at magnet; no clipping')
        x=gradient[...,0];nx=x.norm(dim=-1,keepdim=True)
        if (nx<1e-9).any():raise ValueError('Singular local field frame')
        e1=x/nx;y=gradient[...,1]-(gradient[...,1]*e1).sum(-1,keepdim=True)*e1;ny=y.norm(dim=-1,keepdim=True)
        if (ny<1e-9).any():raise ValueError('Singular local field frame')
        e2=y/ny;e3=torch.linalg.cross(e1,e2,dim=-1)
        return self.centers_mm+u[...,0,:],torch.stack((e1,e2,e3),-1)

    def absolute(self,shared_u_samples_mm):
        centers,rotations=self.local_poses(shared_u_samples_mm)
        return self.operator.field_from_absolute(centers+centers.new_tensor([0.,0.,self.datum_mm]),rotations)

    def forward(self,shared_u_samples_mm,reference_u_samples_mm):
        if reference_u_samples_mm is None:raise ValueError('Explicit physical B0 reference shape required')
        return self.absolute(shared_u_samples_mm)-self.absolute(reference_u_samples_mm)
