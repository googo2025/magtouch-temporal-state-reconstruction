"""Differentiable finite-cylinder Hall readout, lengths mm and output microtesla.

This implements the same uniformly axial-magnetized exterior cylinder as RA's
``fast_magnetic.cylinder_local_uT``: complete elliptic integrals for each current
loop, followed by Gauss--Legendre integration along the cylinder axis.  No
point-dipole approximation, fitted channel gains, or learned field residual is
used.  Polarization is J = mu0*M in tesla, not M in A/m or an inferred real Br.

RA reference, read-only:
  A09_4R/../MagTouch_A07_joint_physics/reference/MagTouch_A06_physics_loop/
  upstream/MagTouch_A04_tip_matched/vendor/MagTouch_A03_platform/src/fast_magnetic.py

The operator is a magnetic decoder only.  Its availability does not certify a
mechanical basis, an initial specimen state, or true silicone deformation.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np
import torch
from torch import Tensor, nn


@lru_cache(maxsize=16)
def _gauss_numpy(order: int) -> tuple[np.ndarray, np.ndarray]:
    if isinstance(order, bool) or not isinstance(order, int) or order < 2:
        raise ValueError("Axial quadrature order must be an integer >= 2")
    nodes, weights = np.polynomial.legendre.leggauss(order)
    return nodes, weights


def _finite(name: str, value: Tensor) -> None:
    if not bool(torch.isfinite(value).all().detach().cpu()):
        raise ValueError(f"Nonfinite {name}")


def complete_elliptic_ke(parameter: Tensor, iterations: int = 16) -> tuple[Tensor, Tensor]:
    """Complete K(m), E(m) by fixed-iteration differentiable arithmetic-geometric mean.

    The argument is the elliptic parameter m (not modulus sqrt(m)).  No sqrt(m)
    is taken, so the m=0 derivative remains finite.  Float64 is recommended near
    the cylinder surface; the public Hall module uses float64 by default.
    """
    if not parameter.is_floating_point():
        raise ValueError("Elliptic parameter must be floating point")
    _finite("elliptic parameter", parameter)
    if bool(((parameter < 0) | (parameter >= 1)).any().detach().cpu()):
        raise ValueError("Complete elliptic integrals require 0 <= m < 1")
    if iterations < 8:
        raise ValueError("Use at least eight fixed AGM iterations")
    a = torch.ones_like(parameter)
    b = torch.sqrt(1 - parameter)
    correction = parameter / 2
    weight = 1.0
    for _ in range(iterations):
        c = (a - b) / 2
        correction = correction + weight * c.square()
        next_a = (a + b) / 2
        b = torch.sqrt(a * b)
        a = next_a
        weight *= 2
    k = math.pi / (2 * a)
    e = k * (1 - correction)
    return k, e


def rotvec_to_matrix(rotvec_rad: Tensor) -> Tensor:
    """Rodrigues map for (...,3) rotation vectors, with finite derivatives at zero.

    Angles are axis-angle rotation vectors in radians, not Euler angles.  Small
    angles use polynomial coefficients in squared angle; the unselected exact
    branch is also finite to avoid NaNs in backward at exactly zero.
    """
    if rotvec_rad.shape[-1:] != (3,) or not rotvec_rad.is_floating_point():
        raise ValueError("Expected floating rotation vectors (...,3), radians")
    _finite("rotation vectors", rotvec_rad)
    x, y, z = rotvec_rad.unbind(-1)
    zero = torch.zeros_like(x)
    skew = torch.stack((zero, -z, y, z, zero, -x, -y, x, zero), dim=-1)
    skew = skew.reshape(*rotvec_rad.shape[:-1], 3, 3)
    squared_angle = rotvec_rad.square().sum(-1)
    safe_squared_angle = squared_angle.clamp_min(1e-12)
    safe_angle = torch.sqrt(safe_squared_angle)
    a_exact = torch.sin(safe_angle) / safe_angle
    b_exact = (1 - torch.cos(safe_angle)) / safe_squared_angle
    a_series = 1 - squared_angle / 6 + squared_angle.square() / 120 - squared_angle.pow(3) / 5040
    b_series = 0.5 - squared_angle / 24 + squared_angle.square() / 720 - squared_angle.pow(3) / 40320
    small = squared_angle < 1e-8
    a = torch.where(small, a_series, a_exact)
    b = torch.where(small, b_series, b_exact)
    identity = torch.eye(3, dtype=rotvec_rad.dtype, device=rotvec_rad.device)
    return identity + a[..., None, None] * skew + b[..., None, None] * (skew @ skew)


def cylinder_local_uT(
    local_mm: Tensor,
    radius_mm: float = 2.5,
    height_mm: float = 1.0,
    order: int = 24,
    *,
    check_exterior: bool = True,
) -> Tensor:
    """Local exterior cylinder field for signed +1 tesla polarization, (...,3).

    Input origin is the cylinder center, magnetization along local +z.  Output is
    microtesla per tesla polarization.  Sensor positions inside/on the magnet
    are rejected; near-axis analytic limits match the RA reference.
    """
    if local_mm.shape[-1:] != (3,) or not local_mm.is_floating_point():
        raise ValueError("Expected floating cylinder-local coordinates (...,3)")
    if not math.isfinite(radius_mm) or not math.isfinite(height_mm) or radius_mm <= 0 or height_mm <= 0:
        raise ValueError("Finite positive radius and height in millimeters required")
    _finite("cylinder-local coordinates", local_mm)
    original_shape = local_mm.shape
    points = local_mm.reshape(-1, 3)
    rho = torch.linalg.vector_norm(points[:, :2], dim=-1)
    a, half_height = float(radius_mm), float(height_mm) / 2
    if check_exterior and bool(((rho <= a) & (points[:, 2].abs() <= half_height)).any().detach().cpu()):
        raise ValueError("Exterior cylinder field only; sensor inside/on magnetic source")
    gn, gw = _gauss_numpy(order)
    nodes = torch.as_tensor(gn, dtype=points.dtype, device=points.device)
    weights = torch.as_tensor(gw, dtype=points.dtype, device=points.device) * half_height
    axial = points[:, 2, None] - half_height * nodes[None, :]
    radial = rho[:, None]
    denominator = torch.sqrt((a + radial).square() + axial.square())
    distance_squared = (a - radial).square() + axial.square()
    # A parameter of exactly one is singular.  Match the RA FP64 clamp, and
    # retain a representable upper bound for a deliberately lower dtype.
    upper = 1 - max(1e-16, torch.finfo(points.dtype).eps / 2)
    parameter = (4 * a * radial / denominator.square()).clamp(0, upper)
    k, e = complete_elliptic_ke(parameter)
    bz = ((k + (a * a - radial.square() - axial.square()) / distance_squared * e) / denominator) @ weights / (2 * math.pi)
    safe_radial = radial.clamp_min(1e-30)
    br = ((axial / safe_radial * (-k + (a * a + radial.square() + axial.square()) / distance_squared * e)) / denominator) @ weights / (2 * math.pi)
    bx_by = br[:, None] * points[:, :2] / rho[:, None].clamp_min(1e-30)
    zp = points[:, 2] + half_height
    zm = points[:, 2] - half_height
    axial_bz = 0.5 * (zp / torch.sqrt(zp.square() + a * a) - zm / torch.sqrt(zm.square() + a * a))
    axial_derivative = 0.5 * a * a * ((zp.square() + a * a).pow(-1.5) - (zm.square() + a * a).pow(-1.5))
    # Write the radial limit directly in x/y, preserving transverse derivatives
    # at rho=0 rather than normalizing a zero direction vector.
    axial_bx_by = -0.5 * points[:, :2] * axial_derivative[:, None]
    axis = rho < a * 1e-5
    bx_by = torch.where(axis[:, None], axial_bx_by, bx_by)
    bz = torch.where(axis, axial_bz, bz)
    return torch.cat((bx_by, bz[:, None]), dim=-1).reshape(original_shape) * 1e6


def fields_external_torch(
    centers_mm: Tensor,
    rotvec_rad: Tensor,
    sensors_mm: Tensor,
    signed_J_T: Tensor,
    radius_mm: float = 2.5,
    height_mm: float = 1.0,
    order: int = 24,
    *,
    check_exterior: bool = True,
) -> Tensor:
    """Sum finite-cylinder contributions in one shared configuration.

    centers/rotvec: (...,M,3); sensors: (S,3); signed_J_T: (M,).
    Returns (...,S,3), in world axes and microtesla.  Contributions of magnetic
    sources may be summed here; independent single-contact mechanical responses
    must not be summed to manufacture a multiple-contact configuration.
    """
    if centers_mm.ndim < 2 or centers_mm.shape[-1] != 3 or centers_mm.shape != rotvec_rad.shape:
        raise ValueError("Centers and rotation vectors must share shape (...,M,3)")
    if not centers_mm.is_floating_point() or centers_mm.dtype != rotvec_rad.dtype or centers_mm.device != rotvec_rad.device:
        raise ValueError("Centers and rotations must share floating dtype and device")
    return fields_external_matrices(
        centers_mm, rotvec_to_matrix(rotvec_rad), sensors_mm, signed_J_T,
        radius_mm, height_mm, order, check_exterior=check_exterior,
    )


def fields_external_matrices(
    centers_mm: Tensor,
    rotation_matrices: Tensor,
    sensors_mm: Tensor,
    signed_J_T: Tensor,
    radius_mm: float = 2.5,
    height_mm: float = 1.0,
    order: int = 24,
    *,
    check_exterior: bool = True,
) -> Tensor:
    """Absolute world configuration -> (...,S,3) magnetic vectors in microtesla.

    Centers have shape (...,M,3), in the *same* world/array frame as sensors.
    Rotations have shape (...,M,3,3), mapping magnet-local column vectors to
    world column vectors.  This interface adds no nominal centers or Z datum,
    and does not take a matrix logarithm.  Thus a shared mechanical decoder can
    retain stable gradients for left-composed finite rotations at zero angle.
    Only actual rigid rotations are accepted, not scale/shear matrices.
    """
    if centers_mm.ndim < 2 or centers_mm.shape[-1:] != (3,):
        raise ValueError("Expected absolute centers(...,M,3) in sensor/array frame")
    if rotation_matrices.shape != (*centers_mm.shape[:-1], 3, 3):
        raise ValueError("Rotations must have shape (...,M,3,3), matching centers")
    if not centers_mm.is_floating_point() or centers_mm.dtype != rotation_matrices.dtype or centers_mm.device != rotation_matrices.device:
        raise ValueError("Centers and rotation matrices must share floating dtype and device")
    sensors = torch.as_tensor(sensors_mm, dtype=centers_mm.dtype, device=centers_mm.device)
    polarization = torch.as_tensor(signed_J_T, dtype=centers_mm.dtype, device=centers_mm.device)
    if sensors.ndim != 2 or sensors.shape[-1] != 3 or polarization.shape != (centers_mm.shape[-2],):
        raise ValueError("Expected sensors(S,3) and signed polarization(M,)")
    for name, value in (("centers", centers_mm), ("rotation matrices", rotation_matrices), ("sensor positions", sensors), ("signed polarization J=mu0*M in T", polarization)):
        _finite(name, value)
    # Validation must not detach the matrices used in the actual field graph.
    # Float32 mechanics may precede the float64 readout, so allow its rounding
    # error but never silently project scale/shear back into a rigid pose.
    rotation_tolerance = 2e-5
    detached_rotations = rotation_matrices.detach()
    identity = torch.eye(3, dtype=centers_mm.dtype, device=centers_mm.device)
    orthogonal_error = (detached_rotations.transpose(-1, -2) @ detached_rotations - identity).abs().amax()
    determinant_error = (torch.linalg.det(detached_rotations) - 1).abs().amax()
    if bool(((orthogonal_error > rotation_tolerance) | (determinant_error > rotation_tolerance)).cpu()):
        raise ValueError("Magnet orientation must be a proper rigid rotation (R^T R=I, det R=+1)")
    offsets = sensors - centers_mm[..., :, None, :]
    local = torch.einsum("...msi,...mij->...msj", offsets, rotation_matrices)
    local_field = cylinder_local_uT(local, radius_mm, height_mm, order, check_exterior=check_exterior)
    world = torch.einsum("...msj,...mij->...msi", local_field, rotation_matrices)
    return (world * polarization[:, None, None]).sum(dim=-3)


@dataclass(frozen=True)
class Had239FieldGeometry:
    """Frozen readout geometry and polarization provenance, not material metrology."""

    mechanical_centers_mm: tuple[tuple[float, float, float], ...]
    mechanical_to_array_z_mm: float
    sensors_array_mm: tuple[tuple[float, float, float], ...]
    sensor_yaw_deg: tuple[float, ...]
    signed_J_T: tuple[float, ...]
    radius_mm: float
    height_mm: float
    contract_sha256: str
    polarization_source: str
    polarity_source: str
    polarization_identity: str


def load_had239_geometry(
    contract_path: str | Path,
    *,
    checkerboard_global_sign: int,
    polarity_source: str,
    expected_sha256: str | None = None,
) -> Had239FieldGeometry:
    """Load the explicit RA had-239 contract without inferring real magnet strength.

    ``primary_static_magnetization_T`` is the contract's reference polarization.
    It is reported as such, never as a newly measured remanent flux density.
    The global polarity must be explicitly supplied with a source because the
    archived contract does not resolve its sign by measurement.  No mean-field
    fitting, optimizer parameter, gain, or per-Trial offset is introduced.
    """
    content = Path(contract_path).read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if expected_sha256 is not None and digest.lower() != expected_sha256.lower():
        raise ValueError("Physics contract SHA-256 differs from pinned input")
    contract: Mapping = json.loads(content.decode("utf-8-sig"))
    if contract["scope"]["target_specimen"] != "fixed_5x5_had_239":
        raise ValueError("This geometry loader is restricted to the explicit had-239 domain")
    if isinstance(checkerboard_global_sign, bool) or checkerboard_global_sign not in (-1, 1) or not polarity_source.strip():
        raise ValueError("Supply explicit +/-1 global polarity and its provenance")
    magnetic = contract["magnet_array"]
    sensor = contract["sensor_array"]
    initial = contract["manufacturing_initial_state"]
    housing = contract["housing_and_support_geometry"]
    if magnetic["count"] != 25 or sensor["sensor_count"] != 5 or sensor["channel_count"] != 15:
        raise ValueError("Expected explicit 25-magnet/5-Hall/15-channel geometry")
    if magnetic["layout"] != "5x5_square_grid" or magnetic["polarity_pattern"] != "alternating_checkerboard":
        raise ValueError("Unsupported magnetic layout or polarity pattern")
    coordinates = tuple(float(v) for v in magnetic["axis_coordinates_mm"])
    if coordinates != (-10.0, -5.0, 0.0, 5.0, 10.0):
        raise ValueError("Current loader requires the recorded five-pitch grid")
    diameter, height = float(magnetic["disc_diameter_mm"]), float(magnetic["disc_thickness_mm"])
    if diameter != 5.0 or height != 1.0 or magnetic["rigid_body_dof_per_magnet"] != 6:
        raise ValueError("Current had-239 contract requires D5/H1 rigid magnets")
    datum = float(housing["z_levels_mm"]["bottom_plate_top_or_reference"])
    if datum != 1.5:
        raise ValueError("Mechanical-to-array Z datum must remain +1.5 mm")
    bottom, top = float(initial["magnet_bottom_z_mm"]), float(initial["magnet_top_z_mm"])
    if bottom != 5.0 or top != 6.0 or not math.isclose(top - bottom, height, abs_tol=1e-12):
        raise ValueError("Magnet Z faces inconsistent with the locked datum and height")
    center_z_mechanical = (bottom + top) / 2 - datum
    # Archived mesh order: x outer loop, y inner loop; do not transpose poses.
    centers = tuple((x, y, center_z_mechanical) for x in coordinates for y in coordinates)
    sensors = tuple(tuple(float(x) for x in sensor["sensors"][f"S{i}"]["position_mm"]) for i in range(1, 6))
    expected_sensors = ((-7.594, 7.594, 0.0), (-7.594, -7.594, 0.0), (7.594, 7.594, 0.0), (7.594, -7.594, 0.0), (0.0, 1.406, 0.0))
    if not np.allclose(sensors, expected_sensors, rtol=0, atol=1e-12):
        raise ValueError("Recorded Hall order/coordinates differ; S5 must retain +1.406 mm Y")
    yaws = tuple(float(sensor["sensors"][f"S{i}"]["rotation_deg_z"]) for i in range(1, 6))
    if any(yaw != 0.0 for yaw in yaws):
        raise ValueError("This contract pins zero Hall yaw; do not refit sensor axes")
    j = float(magnetic["primary_static_magnetization_T"])
    if not math.isfinite(j) or j <= 0:
        raise ValueError("Contract must supply finite positive polarization J=mu0*M in T")
    matching = [v for v in magnetic["magnetization_candidates_T"] if float(v["value"]) == j]
    if len(matching) != 1 or matching[0]["identity"] != "J1_PRIMARY" or matching[0]["status"] != "FROZEN":
        raise ValueError("Require the explicit frozen J1_PRIMARY identity; no guessed Br fallback")
    signed_j = tuple(j * checkerboard_global_sign * (-1) ** (i // 5 + i % 5) for i in range(25))
    return Had239FieldGeometry(
        centers, datum, sensors, yaws, signed_j, diameter / 2, height, digest,
        "contract:magnet_array.primary_static_magnetization_T; reference J=mu0*M, not new measured Br",
        polarity_source, matching[0]["identity"],
    )


class FiniteCylinderHallField(nn.Module):
    """Frozen had-239 physical magnetic decoder: (...,25,6) rotvec poses -> 15D.

    Poses are displacements from recorded nominal mechanical magnet centers,
    followed by world-frame axis-angle rotation vectors.  ``field`` returns
    absolute modeled magnetic field; ``forward`` subtracts the explicitly given
    reference pose field.  No implicit zero-pose B0 or per-Trial learned offset.

    ``field_from_absolute`` / ``delta_field_from_absolute`` accept centers
    already in the array frame and local-to-array rotation matrices.  Unlike
    the pose interface, these do not add nominal centers or the +1.5 mm datum.
    """

    def __init__(self, geometry: Had239FieldGeometry, order: int = 24, *, dtype: torch.dtype = torch.float64):
        super().__init__()
        _gauss_numpy(order)
        if dtype not in (torch.float32, torch.float64):
            raise ValueError("Use float64 for validated reference readout, or explicit float32")
        self.geometry = geometry
        self.order = order
        self.radius_mm = geometry.radius_mm
        self.height_mm = geometry.height_mm
        centers = torch.as_tensor(geometry.mechanical_centers_mm, dtype=dtype).clone()
        centers[:, 2] += geometry.mechanical_to_array_z_mm
        self.register_buffer("nominal_centers_array_mm", centers)
        self.register_buffer("sensors_array_mm", torch.as_tensor(geometry.sensors_array_mm, dtype=dtype))
        self.register_buffer("signed_J_T", torch.as_tensor(geometry.signed_J_T, dtype=dtype))

    def field(self, poses_mm_rotvec: Tensor) -> Tensor:
        if poses_mm_rotvec.shape[-2:] != (25, 6):
            raise ValueError("Expected poses(...,25,6): mm translation then rotvec radians")
        pose = poses_mm_rotvec.to(dtype=self.signed_J_T.dtype, device=self.signed_J_T.device)
        centers = self.nominal_centers_array_mm + pose[..., :3]
        b = fields_external_torch(centers, pose[..., 3:], self.sensors_array_mm, self.signed_J_T, self.radius_mm, self.height_mm, self.order)
        return b.reshape(*b.shape[:-2], 15)

    def forward(self, poses_mm_rotvec: Tensor, reference_poses_mm_rotvec: Tensor) -> Tensor:
        if reference_poses_mm_rotvec is None:
            raise ValueError("Supply explicit B0 reference poses; no implicit zero-state substitution")
        field = self.field(poses_mm_rotvec)
        reference = self.field(reference_poses_mm_rotvec)
        return field - reference

    def field_from_absolute(self, centers_array_mm: Tensor, rotation_matrices: Tensor) -> Tensor:
        """Read already transformed absolute centers/rotations, returning (...,15)."""
        if centers_array_mm.shape[-2:] != (25, 3):
            raise ValueError("Expected absolute centers(...,25,3), array-frame millimeters")
        if rotation_matrices.shape != (*centers_array_mm.shape[:-1], 3, 3):
            raise ValueError("Expected matching local-to-array rotation matrices(...,25,3,3)")
        centers = centers_array_mm.to(dtype=self.signed_J_T.dtype, device=self.signed_J_T.device)
        rotations = rotation_matrices.to(dtype=self.signed_J_T.dtype, device=self.signed_J_T.device)
        b = fields_external_matrices(
            centers, rotations, self.sensors_array_mm, self.signed_J_T,
            self.radius_mm, self.height_mm, self.order,
        )
        return b.reshape(*b.shape[:-2], 15)

    def delta_field_from_absolute(
        self,
        centers_array_mm: Tensor,
        rotation_matrices: Tensor,
        reference_centers_array_mm: Tensor,
        reference_rotation_matrices: Tensor,
    ) -> Tensor:
        """Shared absolute configuration minus explicitly supplied B0 configuration.

        The reference may be unbatched while the current state is batched.
        No nominal position, datum conversion, identity-rotation substitution,
        or reference fitting is applied by this interface.
        """
        if reference_centers_array_mm is None or reference_rotation_matrices is None:
            raise ValueError("Supply explicit array-frame B0 centers and rotation matrices")
        return self.field_from_absolute(centers_array_mm, rotation_matrices) - self.field_from_absolute(
            reference_centers_array_mm, reference_rotation_matrices,
        )

    def provenance(self) -> dict:
        return {
            "schema": "MagTouch-FiniteCylinderTorch-R393-1",
            "domain": "original_round_had239",
            "contract_sha256": self.geometry.contract_sha256,
            "mechanical_to_array_z_mm": self.geometry.mechanical_to_array_z_mm,
            "magnet_order": "x_outer_y_inner; five by five",
            "pose_rotation": "axis-angle rotvec in radians; not Euler",
            "absolute_matrix_interface": "centers already in array mm; R maps local to array; no nominal/datum addition",
            "channel_order": [f"S{i}{axis}" for i in range(1, 6) for axis in "xyz"],
            "field_unit": "uT",
            "length_unit": "mm",
            "polarization_unit": "J=mu0*M in T",
            "polarization_identity": self.geometry.polarization_identity,
            "polarization_source": self.geometry.polarization_source,
            "polarity_source": self.geometry.polarity_source,
            "signed_J_T": list(self.geometry.signed_J_T),
            "quadrature": "azimuth analytic elliptic K/E AGM; axial Gauss-Legendre",
            "axial_order": self.order,
            "mechanical_teacher_validated": False,
            "physical_deformation_validation": "NOT_ESTABLISHED_BY_MAGNETIC_OPERATOR",
            "trainable_parameters": 0,
            "uses_measured_field_to_fit_gains": False,
        }
