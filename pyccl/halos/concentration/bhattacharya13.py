from ... import ccllib as lib
from ...base import warn_api
from ..massdef import MassDef
from ..halo_model_base import Concentration


__all__ = ("ConcentrationBhattacharya13",)


class ConcentrationBhattacharya13(Concentration):
    r"""Concentration-mass relation by Bhattacharya et al. (2013)
    :arXiv:1112.5479. Valid only for S.O. masses with
    :math:`\Delta=200m` and :math:`\Delta=200c`.

    The concentration takes the form

    .. math::

        c(M, z) = A \times D(z)^B \nu^C,

    where :math:`D(z)` is the growth factor at redshift :math:`z`,
    :math:`\nu=\frac{\delta_c}{\sigma_\rm{M}}` is the peak height, and
    :math:`(A,B,C)` are given by the fitting formula.

    Parameters
    ----------
    mass_def : :class:`~pyccl.halos.massdef.MassDef`
        Mass definition for this :math:`c(M)` parametrization.
        The default is :math:`\Delta=200c`.
    """
    name = 'Bhattacharya13'

    @warn_api(pairs=[("mdef", "mass_def")])
    def __init__(self, *, mass_def=MassDef(200, 'critical')):
        super().__init__(mass_def=mass_def)

    def _check_mass_def_strict(self, mass_def):
        return mass_def.name not in ["vir", "200m", "200c"]

    def _setup(self):
        vals = {"vir": (7.7, 0.9, -0.29),
                "200m": (9.0, 1.15, -0.29),
                "200c": (5.9, 0.54, -0.35)}

        self.A, self.B, self.C = vals[self.mass_def.name]

    def _concentration(self, cosmo, M, a):
        gz = cosmo.growth_factor(a)
        status = 0
        delta_c, status = lib.dc_NakamuraSuto(cosmo.cosmo, a, status)
        sig = cosmo.sigmaM(M, a)
        nu = delta_c / sig
        return self.A * gz**self.B * nu**self.C
