import numpy as np
import pytest
import pyccl as ccl
from pyccl.halos.halo_model import halomod_bias_1pt


COSMO = ccl.Cosmology(
    Omega_c=0.27, Omega_b=0.045, h=0.67, sigma8=0.8, n_s=0.96,
    transfer_function='bbks', matter_power_spectrum='linear')
COSMO.compute_nonlin_power()
M200 = ccl.halos.MassDef200m()
HMF = ccl.halos.MassFuncTinker10(COSMO, mass_def=M200)
HBF = ccl.halos.HaloBiasTinker10(COSMO, mass_def=M200)
P1 = ccl.halos.HaloProfileNFW(ccl.halos.ConcentrationDuffy08(M200),
                              fourier_analytic=True)
# P2 will have is_number_counts = True
P2 = ccl.halos.HaloProfileHOD(ccl.halos.ConcentrationDuffy08(M200))
P3 = ccl.halos.HaloProfilePressureGNFW()
P4 = P1
Pneg = ccl.halos.HaloProfilePressureGNFW(P0=-1)
PKC = ccl.halos.Profile2pt()
PKCH = ccl.halos.Profile2ptHOD()
KK = np.geomspace(1E-3, 10, 32)
MM = np.geomspace(1E11, 1E15, 16)
AA = 1.0


def get_ssc_counterterm_gc(k, a, hmc, prof1, prof2, prof12_2pt,
                           normalize=False):

    P_12 = b1 = b2 = np.zeros_like(k)
    if prof1.is_number_counts or prof2.is_number_counts:
        norm1 = hmc.profile_norm(COSMO, a, prof1)
        norm2 = hmc.profile_norm(COSMO, a, prof2)
        norm12 = 1
        if normalize:
            norm12 = norm1 * norm2

        i11_1 = hmc.I_1_1(COSMO, k, a, prof1)
        i11_2 = hmc.I_1_1(COSMO, k, a, prof2)
        i02_12 = hmc.I_0_2(COSMO, k, a, prof1, prof12_2pt, prof2)

        pk = ccl.linear_matter_power(COSMO, k, a)
        P_12 = norm12 * (pk * i11_1 * i11_2 + i02_12)

        if prof1.is_number_counts:
            b1 = halomod_bias_1pt(COSMO, hmc, k, a, prof1) * norm1
        if prof2.is_number_counts:
            b2 = halomod_bias_1pt(COSMO, hmc, k, a, prof2) * norm2

    return (b1 + b2) * P_12


@pytest.mark.parametrize('pars',
                         [{'p1': P1, 'p2': None, 'cv12': None,
                           'p3': None, 'p4': None, 'cv34': None,
                           'norm': False, 'pk': None},
                          {'p1': P1, 'p2': None, 'cv12': None,
                           'p3': None, 'p4': None, 'cv34': None,
                           'norm': True, 'pk': None},
                          {'p1': P1, 'p2': P2, 'cv12': None,
                           'p3': None, 'p4': None, 'cv34': None,
                           'norm': False, 'pk': None},
                          {'p1': P1, 'p2': None, 'cv12': None,
                           'p3': P3, 'p4': None, 'cv34': None,
                           'norm': False, 'pk': None},
                          {'p1': P1, 'p2': None, 'cv12': None,
                           'p3': None, 'p4': P4, 'cv34': None,
                           'norm': False, 'pk': None},
                          {'p1': P1, 'p2': P2, 'cv12': None,
                           'p3': P3, 'p4': P4, 'cv34': None,
                           'norm': False, 'pk': None},
                          {'p1': P2, 'p2': P2, 'cv12': PKCH,
                           'p3': P2, 'p4': P2, 'cv34': None,
                           'norm': False, 'pk': None},
                          {'p1': P1, 'p2': P2, 'cv12': PKC,
                           'p3': P3, 'p4': P4, 'cv34': PKC,
                           'norm': True, 'pk': None},
                          {'p1': P1, 'p2': None, 'cv12': None,
                           'p3': None, 'p4': None, 'cv34': None,
                           'norm': False, 'pk': 'linear'},
                          {'p1': P1, 'p2': None, 'cv12': None,
                           'p3': None, 'p4': None, 'cv34': None,
                           'norm': False, 'pk': 'nonlinear'},
                          {'p1': P1, 'p2': None, 'cv12': None,
                           'p3': None, 'p4': None, 'cv34': None,
                           'norm': False, 'pk': COSMO.get_nonlin_power()},
                          ],)
def test_tkkssc_smoke(pars):
    hmc = ccl.halos.HMCalculator(COSMO, HMF, HBF, mass_def=M200,
                                 nlog10M=2)
    k_arr = KK
    a_arr = np.array([0.3, 0.5, 0.7, 1.0])

    tkk = ccl.halos.halomod_Tk3D_SSC(COSMO, hmc,
                                     prof1=pars['p1'],
                                     prof2=pars['p2'],
                                     prof12_2pt=pars['cv12'],
                                     prof3=pars['p3'],
                                     prof4=pars['p4'],
                                     prof34_2pt=pars['cv34'],
                                     normprof1=pars['norm'],
                                     normprof2=pars['norm'],
                                     normprof3=pars['norm'],
                                     normprof4=pars['norm'],
                                     p_of_k_a=pars['pk'],
                                     lk_arr=np.log(k_arr), a_arr=a_arr,
                                     )
    tk = tkk.eval(0.1, 0.5)
    assert np.all(np.isfinite(tk))


def test_tkkssc_errors():
    from pyccl.pyutils import assert_warns

    hmc = ccl.halos.HMCalculator(COSMO, HMF, HBF, mass_def=M200)
    k_arr = KK
    a_arr = np.array([0.3, 0.5, 0.7, 1.0])

    # Wrong first profile
    with pytest.raises(TypeError):
        ccl.halos.halomod_Tk3D_SSC(COSMO, hmc, None)
    # Wrong other profiles
    for i in range(2, 4):
        kw = {'prof%d' % i: PKC}
        with pytest.raises(TypeError):
            ccl.halos.halomod_Tk3D_SSC(COSMO, hmc, P1, **kw)
    # Wrong 2pts
    with pytest.raises(TypeError):
        ccl.halos.halomod_Tk3D_SSC(COSMO, hmc, P1,
                                   prof12_2pt=P2)
    with pytest.raises(TypeError):
        ccl.halos.halomod_Tk3D_SSC(COSMO, hmc, P1,
                                   prof34_2pt=P2)

    # Negative profile in logspace
    assert_warns(ccl.CCLWarning, ccl.halos.halomod_Tk3D_1h,
                 COSMO, hmc, P3, prof2=Pneg,
                 lk_arr=np.log(k_arr), a_arr=a_arr,
                 use_log=True)


@pytest.mark.parametrize('kwargs', [
                         # All is_number_counts = False
                         {'prof1': P1, 'prof2': P1,
                          'prof3': P1, 'prof4': P1},
                         #
                         {'prof1': P2, 'prof2': P1,
                          'prof3': P1, 'prof4': P1},
                         #
                         {'prof1': P2, 'prof2': P2,
                          'prof3': P1, 'prof4': P1},
                         #
                         {'prof1': P2, 'prof2': P2,
                          'prof3': P2, 'prof4': P1},
                         #
                         {'prof1': P1, 'prof2': P1,
                          'prof3': P2, 'prof4': P2},
                         #
                         {'prof1': P2, 'prof2': P1,
                          'prof3': P2, 'prof4': P2},
                         #
                         {'prof1': P2, 'prof2': P2,
                          'prof3': P1, 'prof4': P2},
                         #
                         {'prof1': P2, 'prof2': None,
                          'prof3': P1, 'prof4': None},
                         #
                         {'prof1': P2, 'prof2': None,
                          'prof3': None, 'prof4': None},
                         #
                         {'prof1': P2, 'prof2': P2,
                          'prof3': None, 'prof4': None},
                         # All is_number_counts = True
                         {'prof1': P2, 'prof2': P2,
                          'prof3': P2, 'prof4': P2},

                         ]
                         )
def test_tkkssc_counterterms_gc(kwargs):
    hmc = ccl.halos.HMCalculator(COSMO, HMF, HBF, mass_def=M200,
                                 nlog10M=2)
    k_arr = KK
    a_arr = np.array([0.3, 0.5, 0.7, 1.0])

    if kwargs['prof2'] is None:
        kwargs['prof2'] = kwargs['prof1']
    if kwargs['prof3'] is None:
        kwargs['prof3'] = kwargs['prof1']
    if kwargs['prof4'] is None:
        kwargs['prof4'] = kwargs['prof3']

    # Tk's without clustering terms. Set is_number_counts=False for HOD
    # profiles
    kwargs_nogc = kwargs.copy()
    for k, v in kwargs_nogc.items():
        if v is None:
            continue
        v.is_number_counts = False
        kwargs_nogc[k] = v
    tkk_nogc = ccl.halos.halomod_Tk3D_SSC(COSMO, hmc, prof12_2pt=PKC,
                                          prof34_2pt=PKC,
                                          lk_arr=np.log(k_arr), a_arr=a_arr,
                                          **kwargs_nogc)
    _, _, _, tkk_nogc_arrs = tkk_nogc.get_spline_arrays()
    tk_nogc_12, tk_nogc_34 = tkk_nogc_arrs

    # Tk's with clustering terms
    tkk_gc = ccl.halos.halomod_Tk3D_SSC(COSMO, hmc, prof12_2pt=PKC,
                                        prof34_2pt=PKC,
                                        lk_arr=np.log(k_arr), a_arr=a_arr,
                                        **kwargs)
    _, _, _, tkk_gc_arrs = tkk_gc.get_spline_arrays()
    tk_gc_12, tk_gc_34 = tkk_gc_arrs

    # Tk's of the clustering terms
    tkc12 = []
    tkc34 = []
    for aa in a_arr:
        tkc12.append(get_ssc_counterterm_gc(k_arr, aa, hmc, kwargs['prof1'],
                                            kwargs['prof2'], PKC))
        tkc34.append(get_ssc_counterterm_gc(k_arr, aa, hmc, kwargs['prof3'],
                                            kwargs['prof4'], PKC))
    tkc12 = np.array(tkc12)
    tkc34 = np.array(tkc34)

    assert np.abs((tk_nogc_12 - tkc12) / tk_gc_12 - 1).max() < 1e-5
    assert np.abs((tk_nogc_34 - tkc34) / tk_gc_34 - 1).max() < 1e-5
