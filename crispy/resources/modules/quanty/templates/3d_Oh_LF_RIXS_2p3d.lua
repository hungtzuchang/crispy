--------------------------------------------------------------------------------
-- Quanty input file generated using Crispy.
--
-- elements: 3d transition metals
-- symmetry: Oh
-- experiment: RIXS
-- edge: L2,3-M4,5 (2p3d)
-- Hamiltonian: Coulomb, spin-orbit coupling, ligand field
-- transition operators: dipole-in, dipole-out
-- template modification date: 28/10/2016
--------------------------------------------------------------------------------
Verbosity(0x00FF)

--------------------------------------------------------------------------------
-- Define the number of electrons, shells, etc.
--------------------------------------------------------------------------------
NBosons = 0
NFermions = 26

NElectrons_2p = $NElectrons_2p
NElectrons_3d = $NElectrons_3d
NElectrons_Ld = 10

IndexDn_2p = {0, 2, 4}
IndexUp_2p = {1, 3, 5}
IndexDn_3d = {6, 8, 10, 12, 14}
IndexUp_3d = {7, 9, 11, 13, 15}
IndexDn_Ld = {16, 18, 20, 22, 24}
IndexUp_Ld = {17, 19, 21, 23, 25}

--------------------------------------------------------------------------------
-- Define the Coulomb term.
--------------------------------------------------------------------------------
OppF0_3d_3d = NewOperator('U', NFermions, IndexUp_3d, IndexDn_3d, {1, 0, 0})
OppF2_3d_3d = NewOperator('U', NFermions, IndexUp_3d, IndexDn_3d, {0, 1, 0})
OppF4_3d_3d = NewOperator('U', NFermions, IndexUp_3d, IndexDn_3d, {0, 0, 1})

OppF0_2p_3d = NewOperator('U', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {1, 0}, {0, 0})
OppF2_2p_3d = NewOperator('U', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {0, 1}, {0, 0})
OppG1_2p_3d = NewOperator('U', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {0, 0}, {1, 0})
OppG3_2p_3d = NewOperator('U', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {0, 0}, {0, 1})

OppNUp_2p = NewOperator('Number', NFermions, IndexUp_2p, IndexUp_2p, {1, 1, 1})
OppNDn_2p = NewOperator('Number', NFermions, IndexDn_2p, IndexDn_2p, {1, 1, 1})
OppN_2p   = OppNUp_2p + OppNDn_2p

OppNUp_3d = NewOperator('Number', NFermions, IndexUp_3d, IndexUp_3d, {1, 1, 1, 1, 1})
OppNDn_3d = NewOperator('Number', NFermions, IndexDn_3d, IndexDn_3d, {1, 1, 1, 1, 1})
OppN_3d   = OppNUp_3d + OppNDn_3d

OppNUp_Ld = NewOperator('Number', NFermions, IndexUp_Ld, IndexUp_Ld, {1, 1, 1, 1, 1})
OppNDn_Ld = NewOperator('Number', NFermions, IndexDn_Ld, IndexDn_Ld, {1, 1, 1, 1, 1})
OppN_Ld   = OppNUp_Ld + OppNDn_Ld

Delta_sc    = $Delta_sc
U_3d_3d_sc  = $U(3d,3d)_sc
F2_3d_3d_sc = $F2(3d,3d)_sc
F4_3d_3d_sc = $F4(3d,3d)_sc
F0_3d_3d_sc = U_3d_3d_sc + 2 / 63 * F2_3d_3d_sc + 2 / 63 * F4_3d_3d_sc
e_3d_sc     = (10 * Delta_sc - NElectrons_3d * (19 + NElectrons_3d) * U_3d_3d_sc / 2) / (10 + NElectrons_3d)
e_Ld_sc     = NElectrons_3d * ((1 + NElectrons_3d) * U_3d_3d_sc / 2 - Delta_sc) / (10 + NElectrons_3d)

Delta_ic    = $Delta_ic
U_3d_3d_ic  = $U(3d,3d)_ic
F2_3d_3d_ic = $F2(3d,3d)_ic
F4_3d_3d_ic = $F4(3d,3d)_ic
F0_3d_3d_ic = U_3d_3d_ic + 2 / 63 * F2_3d_3d_ic + 2 / 63 * F4_3d_3d_ic
U_2p_3d_ic  = $U(2p,3d)_ic
F2_2p_3d_ic = $F2(2p,3d)_ic
G1_2p_3d_ic = $G1(2p,3d)_ic
G3_2p_3d_ic = $G3(2p,3d)_ic
F0_2p_3d_ic = U_2p_3d_ic + 1 / 15 * G1_2p_3d_ic + 3 / 70 * G3_2p_3d_ic
e_2p_ic    = (10 * Delta_ic + (1 + NElectrons_3d) * (NElectrons_3d * U_3d_3d_ic / 2 - (10 + NElectrons_3d) * U_2p_3d_ic)) / (16 + NElectrons_3d)
e_3d_ic    = (10 * Delta_ic - NElectrons_3d * (31 + NElectrons_3d) * U_3d_3d_ic / 2 - 90 * U_2p_3d_ic) / (16 + NElectrons_3d)
e_Ld_ic    = ((1 + NElectrons_3d) * (NElectrons_3d * U_3d_3d_ic / 2 + 6 * U_2p_3d_ic) - (6 + NElectrons_3d) * Delta_ic) / (16 + NElectrons_3d)

Delta_fc    = $Delta_fc
U_3d_3d_fc  = $U(3d,3d)_fc
F2_3d_3d_fc = $F2(3d,3d)_fc
F4_3d_3d_fc = $F4(3d,3d)_fc
F0_3d_3d_fc = U_3d_3d_fc + 2 / 63 * F2_3d_3d_fc + 2 / 63 * F4_3d_3d_fc
e_3d_fc     = (10 * Delta_fc - NElectrons_3d * (19 + NElectrons_3d) * U_3d_3d_fc / 2) / (10 + NElectrons_3d)
e_Ld_fc     = NElectrons_3d * ((1 + NElectrons_3d) * U_3d_3d_fc / 2 - Delta_fc) / (10 + NElectrons_3d)

H_coulomb_sc = F0_3d_3d_sc * OppF0_3d_3d
             + F2_3d_3d_sc * OppF2_3d_3d
             + F4_3d_3d_sc * OppF4_3d_3d
             + e_3d_sc     * OppN_3d
             + e_Ld_sc     * OppN_Ld

H_coulomb_ic = F0_3d_3d_ic * OppF0_3d_3d
             + F2_3d_3d_ic * OppF2_3d_3d
             + F4_3d_3d_ic * OppF4_3d_3d
             + F0_2p_3d_ic * OppF0_2p_3d
             + F2_2p_3d_ic * OppF2_2p_3d
             + G1_2p_3d_ic * OppG1_2p_3d
             + G3_2p_3d_ic * OppG3_2p_3d
             + e_2p_ic     * OppN_2p
             + e_3d_ic     * OppN_3d
             + e_Ld_ic     * OppN_Ld

H_coulomb_fc = F0_3d_3d_fc * OppF0_3d_3d
             + F2_3d_3d_fc * OppF2_3d_3d
             + F4_3d_3d_fc * OppF4_3d_3d
             + e_3d_fc     * OppN_3d
             + e_Ld_fc     * OppN_Ld

--------------------------------------------------------------------------------
-- Define the spin-orbit coupling term.
--------------------------------------------------------------------------------
Oppldots_3d = NewOperator('ldots', NFermions, IndexUp_3d, IndexDn_3d)

Oppldots_2p = NewOperator('ldots', NFermions, IndexUp_2p, IndexDn_2p)

zeta_3d_sc = $zeta(3d)_sc

zeta_3d_ic = $zeta(3d)_ic
zeta_2p_ic = $zeta(2p)_ic

zeta_3d_fc = $zeta(3d)_fc

H_soc_sc = zeta_3d_sc * Oppldots_3d

H_soc_ic = zeta_3d_ic * Oppldots_3d
         + zeta_2p_ic * Oppldots_2p

H_soc_fc = zeta_3d_fc * Oppldots_3d

--------------------------------------------------------------------------------
-- Define the ligand field term.
--------------------------------------------------------------------------------
OpptenDq_3d = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, PotentialExpandedOnClm('Oh', 2, {0.6, -0.4}))
OpptenDq_Ld = NewOperator('CF', NFermions, IndexUp_Ld, IndexDn_Ld, PotentialExpandedOnClm('Oh', 2, {0.6, -0.4}))

OppVeg_3d = NewOperator('CF', NFermions, IndexUp_Ld, IndexDn_Ld, IndexUp_3d, IndexDn_3d, PotentialExpandedOnClm('Oh', 2, {1, 0}))
OppVeg_Ld = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, IndexUp_Ld, IndexDn_Ld, PotentialExpandedOnClm('Oh', 2, {1, 0}))
OppVeg = OppVeg_3d + OppVeg_Ld

OppVt2g_3d = NewOperator('CF', NFermions, IndexUp_Ld, IndexDn_Ld, IndexUp_3d, IndexDn_3d, PotentialExpandedOnClm('Oh', 2, {0, 1}))
OppVt2g_Ld = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, IndexUp_Ld, IndexDn_Ld, PotentialExpandedOnClm('Oh', 2, {0, 1}))
OppVt2g = OppVt2g_3d + OppVt2g_Ld

tenDq_3d_sc = $10Dq(3d)_sc
tenDq_Ld_sc = $10Dq(Ld)_sc
Veg_sc      = $V(eg)_sc
Vt2g_sc     = $V(t2g)_sc

tenDq_3d_ic = $10Dq(3d)_ic
tenDq_Ld_ic = $10Dq(Ld)_ic
Veg_ic      = $V(eg)_ic
Vt2g_ic     = $V(t2g)_ic

tenDq_3d_fc = $10Dq(3d)_fc
tenDq_Ld_fc = $10Dq(Ld)_fc
Veg_fc      = $V(eg)_fc
Vt2g_fc     = $V(t2g)_fc

H_lf_sc = tenDq_3d_sc * OpptenDq_3d
        + tenDq_Ld_sc * OpptenDq_Ld
        + Veg_sc      * OppVeg
        + Vt2g_sc     * OppVt2g

H_lf_ic = tenDq_3d_ic * OpptenDq_3d
        + tenDq_Ld_ic * OpptenDq_Ld
        + Veg_ic      * OppVeg
        + Vt2g_ic     * OppVt2g

H_lf_fc = tenDq_3d_fc * OpptenDq_3d
        + tenDq_Ld_fc * OpptenDq_Ld
        + Veg_fc      * OppVeg
        + Vt2g_fc     * OppVt2g

--------------------------------------------------------------------------------
-- Define the magnetic field term.
--------------------------------------------------------------------------------
OppSx_3d    = NewOperator('Sx'   , NFermions, IndexUp_3d, IndexDn_3d)
OppSy_3d    = NewOperator('Sy'   , NFermions, IndexUp_3d, IndexDn_3d)
OppSz_3d    = NewOperator('Sz'   , NFermions, IndexUp_3d, IndexDn_3d)
OppSsqr_3d  = NewOperator('Ssqr' , NFermions, IndexUp_3d, IndexDn_3d)
OppSplus_3d = NewOperator('Splus', NFermions, IndexUp_3d, IndexDn_3d)
OppSmin_3d  = NewOperator('Smin' , NFermions, IndexUp_3d, IndexDn_3d)

OppLx_3d    = NewOperator('Lx'   , NFermions, IndexUp_3d, IndexDn_3d)
OppLy_3d    = NewOperator('Ly'   , NFermions, IndexUp_3d, IndexDn_3d)
OppLz_3d    = NewOperator('Lz'   , NFermions, IndexUp_3d, IndexDn_3d)
OppLsqr_3d  = NewOperator('Lsqr' , NFermions, IndexUp_3d, IndexDn_3d)
OppLplus_3d = NewOperator('Lplus', NFermions, IndexUp_3d, IndexDn_3d)
OppLmin_3d  = NewOperator('Lmin' , NFermions, IndexUp_3d, IndexDn_3d)

OppJx_3d    = NewOperator('Jx'   , NFermions, IndexUp_3d, IndexDn_3d)
OppJy_3d    = NewOperator('Jy'   , NFermions, IndexUp_3d, IndexDn_3d)
OppJz_3d    = NewOperator('Jz'   , NFermions, IndexUp_3d, IndexDn_3d)
OppJsqr_3d  = NewOperator('Jsqr' , NFermions, IndexUp_3d, IndexDn_3d)
OppJplus_3d = NewOperator('Jplus', NFermions, IndexUp_3d, IndexDn_3d)
OppJmin_3d  = NewOperator('Jmin' , NFermions, IndexUp_3d, IndexDn_3d)

OppSx_Ld    = NewOperator('Sx'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppSy_Ld    = NewOperator('Sy'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppSz_Ld    = NewOperator('Sz'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppSsqr_Ld  = NewOperator('Ssqr' , NFermions, IndexUp_Ld, IndexDn_Ld)
OppSplus_Ld = NewOperator('Splus', NFermions, IndexUp_Ld, IndexDn_Ld)
OppSmin_Ld  = NewOperator('Smin' , NFermions, IndexUp_Ld, IndexDn_Ld)

OppLx_Ld    = NewOperator('Lx'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppLy_Ld    = NewOperator('Ly'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppLz_Ld    = NewOperator('Lz'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppLsqr_Ld  = NewOperator('Lsqr' , NFermions, IndexUp_Ld, IndexDn_Ld)
OppLplus_Ld = NewOperator('Lplus', NFermions, IndexUp_Ld, IndexDn_Ld)
OppLmin_Ld  = NewOperator('Lmin' , NFermions, IndexUp_Ld, IndexDn_Ld)

OppJx_Ld    = NewOperator('Jx'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppJy_Ld    = NewOperator('Jy'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppJz_Ld    = NewOperator('Jz'   , NFermions, IndexUp_Ld, IndexDn_Ld)
OppJsqr_Ld  = NewOperator('Jsqr' , NFermions, IndexUp_Ld, IndexDn_Ld)
OppJplus_Ld = NewOperator('Jplus', NFermions, IndexUp_Ld, IndexDn_Ld)
OppJmin_Ld  = NewOperator('Jmin' , NFermions, IndexUp_Ld, IndexDn_Ld)

OppSx   = OppSx_3d + OppSx_Ld
OppSy   = OppSy_3d + OppSy_Ld
OppSz   = OppSz_3d + OppSz_Ld
OppSsqr = OppSx * OppSx + OppSy * OppSy + OppSz * OppSz

OppLx   = OppLx_3d + OppLx_Ld
OppLy   = OppLy_3d + OppLy_Ld
OppLz   = OppLz_3d + OppLz_Ld
OppLsqr = OppLx * OppLx + OppLy * OppLy + OppLz * OppLz

OppJx   = OppJx_3d + OppJx_Ld
OppJy   = OppJy_3d + OppJy_Ld
OppJz   = OppJz_3d + OppJz_Ld
OppJsqr = OppJx * OppJx + OppJy * OppJy + OppJz * OppJz

Bx = $Bx * EnergyUnits.Tesla.value
By = $By * EnergyUnits.Tesla.value
Bz = $Bz * EnergyUnits.Tesla.value

B = Bx * (2 * OppSx + OppLx)
  + By * (2 * OppSy + OppLy)
  + Bz * (2 * OppSz + OppLz)

--------------------------------------------------------------------------------
-- Compose the total Hamiltonian.
--------------------------------------------------------------------------------
H_sc = $H_coulomb_flag * H_coulomb_sc + $H_soc_flag * H_soc_sc + $H_lf_flag * H_lf_sc + B
H_ic = $H_coulomb_flag * H_coulomb_ic + $H_soc_flag * H_soc_ic + $H_lf_flag * H_lf_ic + B
H_fc = $H_coulomb_flag * H_coulomb_fc + $H_soc_flag * H_soc_fc + $H_lf_flag * H_lf_fc + B

--------------------------------------------------------------------------------
-- Define the starting restrictions and set the number of initial states.
--------------------------------------------------------------------------------
StartingRestrictions = {NFermions, NBosons, {'111111 0000000000 0000000000', NElectrons_2p, NElectrons_2p},
                                            {'000000 1111111111 1111111111', NElectrons_3d + NElectrons_Ld, NElectrons_3d + NElectrons_Ld}}

NPsis = $NPsis

Psis = Eigensystem(H_sc, StartingRestrictions, NPsis)
if not (type(Psis) == 'table') then
    Psis = {Psis}
end

-- Print some useful information about the calculated states.
OppList = {H_sc, OppSsqr, OppLsqr, OppJsqr, OppSz, OppLz, OppN_2p, OppN_3d, OppN_Ld}

print('     <E>    <S^2>    <L^2>    <J^2>    <Sz>     <Lz>     <Np>      <Nd>     <NL>');
for key, Psi in pairs(Psis) do
	expectationValues = Psi * OppList * Psi
	for key, expectationValue in pairs(expectationValues) do
		io.write(string.format('%9.4f', Complex.Re(expectationValue)))
	end
	io.write('\n')
end

--------------------------------------------------------------------------------
-- Define the transition operators.
--------------------------------------------------------------------------------
t = math.sqrt(1/2);

OppTx_2p_3d = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, IndexUp_2p, IndexDn_2p, {{1, -1, t    }, {1, 1, -t    }})
OppTy_2p_3d = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, IndexUp_2p, IndexDn_2p, {{1, -1, t * I}, {1, 1,  t * I}})
OppTz_2p_3d = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, IndexUp_2p, IndexDn_2p, {{1,  0, 1    }                })
OppTr_2p_3d = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, IndexUp_2p, IndexDn_2p, {{1, -1, 1    }                })
OppTl_2p_3d = NewOperator('CF', NFermions, IndexUp_3d, IndexDn_3d, IndexUp_2p, IndexDn_2p, {{1,  1, 1    }                })

OppTx_3d_2p = NewOperator('CF', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {{1, -1, t    }, {1, 1, -t    }})
OppTy_3d_2p = NewOperator('CF', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {{1, -1, t * I}, {1, 1,  t * I}})
OppTz_3d_2p = NewOperator('CF', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {{1,  0, 1    }                })
OppTr_3d_2p = NewOperator('CF', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {{1, -1, 1    }                })
OppTl_3d_2p = NewOperator('CF', NFermions, IndexUp_2p, IndexDn_2p, IndexUp_3d, IndexDn_3d, {{1,  1, 1    }                })

--------------------------------------------------------------------------------
-- Calculate and save the spectra.
--------------------------------------------------------------------------------
-- Define the temperature.
T = $T * EnergyUnits.Kelvin.value

-- Initialize the partition function and the spectrum.
Z = 0
G = 0

Emin1 = $Emin1
Emax1 = $Emax1
Gamma1 = $Gamma1
NE1 = $NE1

Emin2 = $Emin2
Emax2 = $Emax2
Gamma2 = $Gamma2
NE2 = $NE2

-- Calculate the ground state energy.
E_gs = Psis[1] * H_sc * Psis[1]

for j = 1, NPsis do
    E_j = Psis[j] * H_sc * Psis[j]

    if math.abs(E_j - E_gs) < 1e-12 then
        dZ = 1
    else
        dZ = math.exp(-(E_j - E_gs) / T)
    end

    if (dZ < 1e-8) then
        break
    end

    Z = Z + dZ

    G = G + CreateResonantSpectra(H_ic, H_fc, OppTx_2p_3d, OppTx_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})
    G = G + CreateResonantSpectra(H_ic, H_fc, OppTx_2p_3d, OppTy_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})
    G = G + CreateResonantSpectra(H_ic, H_fc, OppTx_2p_3d, OppTz_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})

    G = G + CreateResonantSpectra(H_ic, H_fc, OppTy_2p_3d, OppTx_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})
    G = G + CreateResonantSpectra(H_ic, H_fc, OppTy_2p_3d, OppTy_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})
    G = G + CreateResonantSpectra(H_ic, H_fc, OppTy_2p_3d, OppTz_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})

    G = G + CreateResonantSpectra(H_ic, H_fc, OppTz_2p_3d, OppTx_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})
    G = G + CreateResonantSpectra(H_ic, H_fc, OppTz_2p_3d, OppTy_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})
    G = G + CreateResonantSpectra(H_ic, H_fc, OppTz_2p_3d, OppTz_3d_2p, Psis[j], {{"Emin1", Emin1}, {"Emax1", Emax1}, {"NE1", NE1}, {"Gamma1", Gamma1}, {"Emin2", Emin2}, {"Emax2", Emax2}, {"NE2", NE2}, {"Gamma2", Gamma2}})
end

G = G / Z
G.Print({{'file', '$baseName' .. '.spec'}})
