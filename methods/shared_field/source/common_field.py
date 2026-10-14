"""Exact implemented conditional-field class; private gate/controller excluded."""
import torch
from torch import nn
from .shape_to_field import SharedShapeToField

class CommonField(nn.Module):
    def __init__(self,packet):
        super().__init__();self.history=nn.GRU(21,32,batch_first=True)
        self.spatial=nn.Sequential(nn.Linear(35,64),nn.Tanh(),nn.Linear(64,64),nn.Tanh(),nn.Linear(64,3))
        self.H=SharedShapeToField(packet)
        for p in self.H.parameters():p.requires_grad_(False)
        nodes=torch.as_tensor(packet['nodes_mm'],dtype=torch.float32)
        self.register_buffer('mid',(nodes.min(0).values+nodes.max(0).values)/2)
        self.register_buffer('query_half_extent',(nodes.max(0).values-nodes.min(0).values)/2)
        # Small initialization, not a hard u range or output clamp.
        with torch.no_grad():self.spatial[-1].weight.mul_(.01);self.spatial[-1].bias.mul_(.01)
    def encode(self,features,reset):
        assert features.shape[1]==21 and reset.shape==(len(features),)
        ids=torch.nonzero(reset,as_tuple=False).flatten().tolist();assert ids[0]==0
        bounds=ids+[len(features)];out=[]
        for i,j in zip(bounds,bounds[1:]):out.append(self.history(features[i:j][None])[0][0])
        return torch.cat(out)
    def query(self,h,points):
        q=(points.to(h)-self.mid)/self.query_half_extent
        return self.spatial(torch.cat((h[:,None].expand(-1,len(q),-1),q[None].expand(len(h),-1,-1)),-1))
