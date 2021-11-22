import pytest
import numpy as np
import pyccl as ccl
import warnings


COSMO = ccl.CosmologyVanillaLCDM(
    transfer_function='bbks',
    matter_power_spectrum='halofit')
COSMO.compute_nonlin_power()


@pytest.mark.parametrize('k', [
    1,
    1.0,
    [0.3, 0.5, 10],
    np.array([0.3, 0.5, 10])])
def test_bcm_smoke(k):
    a = 0.8
    fka = ccl.bcm_model_fka(COSMO, k, a)
    assert np.all(np.isfinite(fka))
    assert np.shape(fka) == np.shape(k)


def test_bcm_correct_smoke():
    k_arr = np.geomspace(1E-2, 1, 10)
    fka = ccl.bcm_model_fka(COSMO, k_arr, 0.5)
    pk_nobar = ccl.nonlin_matter_power(COSMO, k_arr, 0.5)
    ccl.bcm_correct_pk2d(COSMO,
                         COSMO._pk_nl['delta_matter:delta_matter'])
    pk_wbar = ccl.nonlin_matter_power(COSMO, k_arr, 0.5)
    assert np.all(np.fabs(pk_wbar/(pk_nobar*fka)-1) < 1E-5)


@pytest.mark.parametrize('model', ['bcm', 'arico21', ])
def test_baryon_correct_smoke(model):
    # we compare each model with BCM
    extras = {"arico21": {'M_c': 14, 'eta': -0.3, 'beta': -0.22,
                          'M1_z0_cen': 10.5, 'theta_out': 0.25,
                          'theta_inn': -0.86, 'M_inn': 13.4},
              }  # other models go in here

    cosmo = ccl.CosmologyVanillaLCDM(
        matter_power_spectrum="halofit",
        extra_parameters=extras)
    cosmo.compute_nonlin_power()
    pknl = cosmo.get_nonlin_power()

    k_arr = np.geomspace(1e-1, 1, 16)
    for z in [0., 0.5, 2.]:
        a = 1./(1+z)
        with warnings.catch_warnings():
            # filter all warnings related to the emulator packages
            warnings.simplefilter("ignore")
            pkb = cosmo.baryon_correct(model, pknl)

        pk0 = pknl.eval(k_arr, a, cosmo)
        pk1 = pkb.eval(k_arr, a, cosmo)
        assert not np.array_equal(pk1, pk0)


def test_bcm_correct_raises():
    with pytest.raises(ValueError):
        ccl.bcm_correct_pk2d(COSMO, None)