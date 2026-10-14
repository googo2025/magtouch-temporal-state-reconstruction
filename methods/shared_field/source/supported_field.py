"""Portable supported shared-field construction from externally supplied geometry.
The support/query algorithms follow the frozen model; no geometry or checkpoint is bundled.
This relocation is source transparency, not a new scientific qualification run.
"""
import hashlib,time
import numpy as np
import torch
from .common_field import CommonField
from .finite_cylinder_field import _finite as finite

class SupportedCommonField(CommonField):
    def __init__(self,packet,fixed_faces_node_indices,fixed_node_ids,geometry_contract_sha):
        super().__init__(packet)
        nodes=np.asarray(packet['nodes_mm']);faces=np.asarray(fixed_faces_node_indices)
        self.fixed_node_ids=np.asarray(fixed_node_ids).copy()
        quads=nodes[faces];lo=quads.min(1);hi=quads.max(1)
        if not np.all(np.sum(hi==lo,axis=1)==1):raise ValueError('Registered fixed faces must be axis-aligned rectangles')
        self._face_low=torch.as_tensor(lo,dtype=torch.float64);self._face_high=torch.as_tensor(hi,dtype=torch.float64)
        self._distance_cache={};self.geometry_cache_records=[];self.support_scale_mm=1.25
        self.nominal_nodes64=torch.as_tensor(nodes,dtype=torch.float64)
        self.geometry_contract_sha=str(geometry_contract_sha)
    def _identity(self,points):
        return hashlib.sha256(points.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
    def query(self,h,points):
        raw=super().query(h,points)
        return raw*self.support_rho(points).to(raw)[None,:,None]
    def encode_framewise(self,features):
        return self.history(features[:,None,:])[0][:,0,:]
    def freeze_framewise_history_weights(self):
        self.history.weight_hh_l0.requires_grad_(False)

    def support_rho(self,points,point_block=128,face_block=256):
            if points.ndim!=2 or points.shape[1]!=3:raise ValueError('Material XYZ query points required')
            key=None if points.requires_grad else (self._identity(points),str(points.device),str(points.dtype),len(points),self.geometry_contract_sha)
            if key is not None and key in self._distance_cache:return self._distance_cache[key]
            start=time.monotonic();cpu=time.process_time();x=points.double();lo=self._face_low.to(x);hi=self._face_high.to(x);values=[]
            for i in range(0,len(x),point_block):
                q=x[i:i+point_block];best=q.new_full((len(q),),float('inf'))
                for j in range(0,len(lo),face_block):
                    delta=torch.relu(lo[None,j:j+face_block]-q[:,None])+torch.relu(q[:,None]-hi[None,j:j+face_block])
                    best=torch.minimum(best,delta.square().sum(-1).min(1).values)
                values.append(best/(best+self.support_scale_mm**2))
            rho=torch.cat(values);finite('declared support rho',rho)
            if key is not None:
                self._distance_cache[key]=rho
                self.geometry_cache_records.append(dict(points=len(x),coordinate_identity=key[0],device=str(x.device),rho_SHA256=hashlib.sha256(rho.detach().cpu().numpy().tobytes()).hexdigest(),bytes=rho.numel()*rho.element_size(),wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu))
            return rho
