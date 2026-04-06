#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: cfbVamp.py
from SLiCAP import *
fileName = 'cfbVamp'
prj = initProject(fileName) # Creates the SLiCAP libraries and the
 # project HTML index page
i1 = instruction() # Creates an instance of an instruction object
i1.setCircuit(fileName+'.cir') # Checks and defines the local circuit object,
 # and sets the index page to the project index
i1.setSource('V1')
i1.setDetector('V_4')
i1.setSimType('symbolic')
i1.setGainType('gain')
i1.setDataType('laplace')
result = i1.execute()
gain = result.laplace
V_ell, V_s, A_f = sp.symbols('V_ell, V_s, A_f')
L_G1, rho_G1, S_G1, A_infty_G1 = sp.symbols('L_G1, rho_G1, S_G1, A_oo_G1')
L_H1, rho_H1, S_H1, A_infty_H1 = sp.symbols('L_H1, rho_H1, S_H1, A_oo_H1')
# Calculations with H1 as loop gain reference
i1.setLGref('G1')
i1.setGainType('asymptotic')
result = i1.execute()
AG1 = result.laplace
i1.setGainType('loopgain')
result = i1.execute()
LG1 = result.laplace
i1.setGainType('servo')
result = i1.execute()
SG1 = result.laplace
i1.setGainType('direct')
result = i1.execute()
DG1 = result.laplace
htmlPage('Asymptotic-gain model G1 ref')
text2html('The gain of the circuit is obtained as:')
eqn2html(V_ell/V_s, gain)
text2html('The asymptotic-gain $A_{\\infty_G1}$ is found as:')
eqn2html(A_infty_G1, AG1)
text2html('The loop gain $L_{G1}$ is found as:')
eqn2html(L_G1, LG1)
text2html('The servo function $S_{G1}$ is found as:')
eqn2html(S_G1, SG1)
text2html('The direct transfer $\\rho_{G1}$ is found as:')
eqn2html(rho_G1, DG1)
text2html('The gain $A_f$ calculated from $A_{\\infty_{G1}}$, $S_{G1}$ ' + 'and $\\rho_{G1}$ is obtained as:')
eqn2html(A_f, sp.simplify(AG1*SG1 + DG1/(1-LG1)))

# Calculations with H1 as loop gain reference
i1.setLGref('H1')
i1.setGainType('asymptotic')
result = i1.execute()
AH1 = result.laplace
i1.setGainType('loopgain')
result = i1.execute()
LH1 = result.laplace
i1.setGainType('servo')
result = i1.execute()
SH1 = result.laplace
i1.setGainType('direct')
result = i1.execute()
DH1 = result.laplace
htmlPage('Asymptotic - gain model H1 ref')
text2html('The gain of the circuit is obtained as:')
eqn2html(V_ell / V_s, gain)
text2html('The asymptotic-gain $A_{\\infty_{H1}}$ is found as:')
eqn2html(A_infty_H1, AH1)
text2html('The loop gain $L_{H1}$ is found as:')
eqn2html(L_H1, LH1)
text2html('The servo function $S_{H1}$ is found as:')
eqn2html(S_H1, SH1)
text2html('The direct transfer $\\rho_{H1}$ is found as:')
eqn2html(rho_H1, DH1)
text2html('The gain $A_f$ calculated from $A_{\\infty_G1}$, $S_{G1}$ and ' +
 '$\\rho_{G1}$ is obtained as:')
eqn2html(A_f, sp.simplify(AH1*SH1 + DH1/(1-LH1)))
