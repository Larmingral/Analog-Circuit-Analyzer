#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 2 14:59:59 2020
@author: anton
"""
from SLiCAP import *
fileName = 'cfbVampExtended'
prj = initProject(fileName) # Creates the SLiCAP libraries and the
 # project HTML index page
i1 = instruction() # Creates an instance of an instruction object
i1.setCircuit(fileName+'.cir') # Checks and defines the local circuit object
 # and sets the index page to the project index
htmlPage('Circuit data')
elementData2html(i1.circuit)

i1.setSource('V1')
i1.setDetector('V_3')
i1.setLGref('H_O1')
i1.setSimType('numeric')
i1.setDataType('laplace')
i1.setGainType('gain')
G = i1.execute()
i1.setGainType('asymptotic')
A = i1.execute()
i1.setGainType('loopgain')
L = i1.execute()
i1.setGainType('servo')
S = i1.execute()
i1.setGainType('direct')
D = i1.execute()
figdBmag = plotSweep('cfbVampdBmag.svg', 'dB magnitude plots asymptotic-' +
 'gain model', [G,A,L,S,D], 1e4, 1e9, 200,
 funcType = 'dBmag', show=True)
figPhase = plotSweep('cfbVampPhase.svg', 'Phase plots asymptotic-gain model',[G,A,L,S,D], 1e4, 1e9, 200, funcType = 'phase', show=True)
htmlPage('Bode plots')
fig2html(figdBmag, 800)
fig2html(figPhase, 800)

htmlPage('Symbolic asymptotic-gain')
i1.setSimType('symbolic')
i1.setGainType('asymptotic')
result = i1.execute()
A = result.laplace
text2html('The asymptotic-gain is found as:')
eqn2html('A_f_oo', A)