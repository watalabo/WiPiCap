from cmath import sin, cos, exp, phase, pi, sqrt
import numpy as np

def recon_v_matrix(sub_arr):
    phi11, phi21, psi21, psi31, phi22, psi32 = sub_arr

    phi11 = (phi11/32+1/64)*pi
    phi21 = (phi21/32+1/64)*pi
    psi21 = (psi21/32+1/64)*pi
    psi31 = (psi31/32+1/64)*pi
    phi22 = (phi22/32+1/64)*pi
    psi32 = (psi32/32+1/64)*pi

    v11 = cos(psi31) * exp(1j*phi11) * cos(psi21)
    v12 = -cos(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    v13 = sin(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    v21 = cos(psi31) * exp(1j*phi21) * sin(psi21)
    v22 = cos(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    v23 = -sin(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    v31 = sin(psi31)
    v32 = cos(psi31) * sin(psi32)
    v33 = cos(psi31) * cos(psi32)

    return [v11, v12, v13, v21, v22, v23, v31, v32, v33]
    
def str2arr(x):
    x_alt = x.replace('"','').replace('[','').replace(']','').split(',')
    return list(map(int, x_alt))

def recon_two(sub_arr):
    phi11, psi21 = sub_arr
    a = np.array([[exp(1j*phi11), 0],[0, 1]])
    b = np.array([[cos(psi21), -sin(psi21)],[sin(psi21), cos(psi21)]])

    v = np.dot(a,b)

    return [v[0][0], v[0][1], v[1][0], v[1][1]]