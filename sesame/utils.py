# Copyright 2017 University of Maryland.
#
# This file is part of Sesame. It is subject to the license terms in the file
# LICENSE.rst found in the top-level directory of this distribution.

import numpy as np
import gzip
import pickle
from scipy.io import savemat

def safe_eval(expr, allowed_vars=None):
    """
    Safely evaluate a mathematical expression using a restricted environment.
    Only numpy and basic math functions are allowed.
    """
    allowed_names = {
        'np': np,
        'exp': np.exp,
        'sin': np.sin,
        'cos': np.cos,
        'abs': np.abs,
        'log': np.log,
        'sqrt': np.sqrt,
        'pi': np.pi,
    }
    if allowed_vars:
        allowed_names.update(allowed_vars)

    # Restrict __builtins__ to prevent access to dangerous functions
    return eval(expr, {"__builtins__": {}}, allowed_names)

def make_safe_callable(expr, var_names):
    """
    Returns a safe callable function from a string expression.
    To be compatible with Sesame's Builder.generation, it must have the correct
    number of positional arguments (1 for 1D, 2 for 2D).
    """
    if 'y' in var_names: # Assume 2D if 'y' is in var_names
        def safe_f(x, y, *args):
            allowed_vars = {'x': x, 'y': y}
            # map remaining args to remaining var_names
            other_names = [n for n in var_names if n not in ('x', 'y')]
            for name, val in zip(other_names, args):
                allowed_vars[name] = val
            return safe_eval(expr, allowed_vars)
    else:
        def safe_f(x, *args):
            allowed_vars = {'x': x}
            other_names = [n for n in var_names if n != 'x']
            for name, val in zip(other_names, args):
                allowed_vars[name] = val
            return safe_eval(expr, allowed_vars)
    return safe_f

def get_indices(sys, p, site=False):
    # Return the indices of continous coordinates on the discrete lattice
    # If site is True, return the site number instead
    # Warning: for x=Lx, the site index will be the one before the last one, and
    # the same goes for y=Ly and z=Lz.
    # p: list containing x,y,z coordinates, use zeros for unused dimensions

    x, y, z = p
    xpts, ypts = sys.xpts, sys.ypts
    nx = len(xpts)
    x = nx-len(xpts[xpts >= x])
    s = x

    if ypts is not None:
        ny = len(ypts)
        y = ny-len(ypts[ypts >= y])
        s += nx*y

    if site:
        return s
    else:
        return x, int(y)

def get_xyz_from_s(sys, site):
    nx, ny = sys.nx, sys.ny
    j = (site - nx*ny) // nx * (ny > 1)
    i = site - j*nx
    return i, j

def get_dl(sys, sites):
    sa, sb = sites
    xa, ya, za = get_xyz_from_s(sys, sa)
    xb, yb, zb = get_xyz_from_s(sys, sb)

    if xa != xb: dl = sys.dx[xa]
    if ya != yb: dl = sys.dy[ya]
    if za != zb: dl = sys.dz[za]

    return dl

    return s, np.asarray(X), np.asarray(xcoord), np.asarray(ycoord)


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def Bresenham(system, p1, p2):
    # Compute a digital line contained in the plane (x,y) and passing by the
    # points p1 and p2.
    i1, j1 = get_indices(system, p1)
    i2, j2 = get_indices(system, p2)

    Dx = abs(i2 - i1)    # distance to travel in X
    Dy = abs(j2 - j1)    # distance to travel in Y

    incx = 0
    if i1 < i2:
        incx = 1           # x will increase at each step
    elif i1 > i2:
        incx = -1          # x will decrease at each step

    incy = 0
    if j1 < j2:
        incy = 1           # y will increase at each step
    elif j1 > j2:
        incy = -1          # y will decrease at each step

    # take the numerator of the distance of a point to the line
    error = lambda x, y: abs((p2[1]-p1[1])*x - (p2[0]-p1[0])*y + p2[0]*p1[1] - p2[1]*p1[0])

    i, j = i1, j1
    sites = [i + j*system.nx]
    X = [0]
    icoord = [i]
    jcoord = [j]


    for _ in range(Dx + Dy):
        e1 = error(system.xpts[i], system.ypts[j+incy])
        e2 = error(system.xpts[i+incx], system.ypts[j])
        if incx == 0:
            condition = e1 <= e2 # for lines x = constant
        else:
            condition = e1 < e2
        if condition:
            # if j went over the edge, break
            if j == system.ny - 1:
                break
            X.append(X[-1] + system.dy[j])
            j += incy
        else:
            # if i went over the edge, break
            if i == system.nx - 1:
                break
            X.append(X[-1] + system.dx[i])
            i += incx
        sites.append(i + j*system.nx)
        icoord.append(i)
        jcoord.append(j)


    sites = np.asarray(sites)
    X = np.asarray(X)
    return sites, X, icoord, jcoord


def get_point_defects_sites(system, location):
    # find the site closest to a given point
    xa = location
    ia, _, _ = get_indices(system, (xa, 0, 0))
    sites = ia
    perp_dl = system.dx[ia]
    return sites, perp_dl



def get_line_defects_sites(system, location):
    # find the sites closest to the straight line defined by
    # (xa,ya,za) and (xb,yb,zb) 

    xa, ya = location[0]
    xb, yb = location[1]
    ia, ja = get_indices(system, (xa, ya, 0))
    ib, jb = get_indices(system, (xb, yb, 0))

    Dx = abs(ib - ia)    # distance to travel in X
    Dy = abs(jb - ja)    # distance to travel in Y
    if ia < ib:
        incx = 1           # x will increase at each step
    elif ia > ib:
        incx = -1          # x will decrease at each step
    else:
        incx = 0
    if ja < jb:
        incy = 1           # y will increase at each step
    elif ja > jb:
        incy = -1          # y will decrease at each step
    else:
        incy = 0

    # take the numerator of the distance of a point to the line
    error = lambda x, y: abs((yb-ya)*x - (xb-xa)*y + xb*ya - yb*xa)

    i, j = ia, ja
    perp_dl = []
    sites = [i + j*system.nx]
    for _ in range(Dx + Dy):
        e1 = error(system.xpts[i], system.ypts[j+incy])
        e2 = error(system.xpts[i+incx], system.ypts[j])
        if incx == 0:
            condition = e1 <= e2 # for lines x = constant
        else:
            condition = e1 < e2
        if condition:
            j += incy
            perp_dl.append((system.dx[i] + system.dx[i-1])/2.)  
        else:
            i += incx
            if (len(system.dy) < j):
                perp_dl.append((system.dy[j] + system.dy[j - 1]) / 2.)
            else:
                # we've assumed abrupt boundary conditions along y-direction!
                perp_dl.append(system.dy[j - 1])
        sites.append(i + j*system.nx)
    perp_dl.append(perp_dl[-1])
    perp_dl = np.asarray(perp_dl)
    return sites, perp_dl


def save_sim(sys, result, filename, fmt='npy'):
    """
    Utility function that saves a system together with simulation results.

    **Warning: For the default numpy format, this function uses pickle, which is
    insecure. Only load files from trusted sources.**

    Parameters
    ----------
    sys: Builder
        The discretized system.
    result: dictionary
        Dictionary of solution, containing 'v', 'efn', 'efp'
    filename: string
        Name of outputfile
    fmt: string
        Format of output file, set to 'mat' for matlab files. With the default
        numpy format, the Builder object is saved directly.
    """

    if fmt=='mat':
        system = {'xpts': sys.xpts, 'ypts': sys.ypts, 'Eg': sys.Eg, 'Nc': sys.Nc, 'Nv': sys.Nv, \
                  'affinity': sys.bl, 'epsilon': sys.epsilon, 'g': sys.g, 'mu_e': sys.mu_e, 'mu_h': sys.mu_h, \
                  'm_e': sys.mass_e, 'm_h': sys.mass_h, 'tau_e': sys.tau_e, 'tau_h': sys.tau_h, \
                  'B': sys.B, 'Cn': sys.Cn, 'Cp': sys.Cp, 'n1': sys.n1, 'p1': sys.p1, 'ni': sys.ni, 'rho': sys.rho}
        results = result.copy()
        results['v'] = np.reshape(result['v'], (sys.ny, sys.nx))
        results['efn'] = np.reshape(result['efn'], (sys.ny, sys.nx))
        results['efp'] = np.reshape(result['efp'], (sys.ny, sys.nx))
        for attr in dir(sys):
            tfield = getattr(sys, attr)
            # determine if element is an array of proper size
            if type(tfield) is np.ndarray:
                if(np.size(tfield) == sys.nx*sys.ny):
                    tdata = np.reshape(tfield, (sys.ny, sys.nx))
                    system.update({attr: tdata})

        savemat(filename, {'sys': system, 'results': results}, do_compression=True)
    else:
        file = gzip.GzipFile(filename, 'wb')
        file.write(pickle.dumps((sys, result)))
        file.close()

def load_sim(filename):
    """
    Utility function that loads a system together with simulation results.

    **Warning: This function uses pickle, which is insecure. Only load
    files from trusted sources.**

    Parameters
    ----------
    filename: string
        Name of inputfile

    Returns
    -------
    system: Builder object
        A discritized system.
    result: dictionary
        Dictionary containing 1D arrays of electron and hole quasi-Fermi levels
        and the electrostatic potential across the system. Keys are 'efn',
        'efp', and/or 'v'.
    """

    f = gzip.GzipFile(filename, 'rb')
    data = f.read()
    sys, result = pickle.loads(data)
    return sys, result


def export_to_csv(sys, result, filename):
    """
    Export simulation results to a CSV file.
    Includes x, y coordinates, potential, and quasi-Fermi levels.
    """
    import csv
    nx, ny = sys.nx, sys.ny
    xpts = sys.xpts
    ypts = sys.ypts

    v = result['v']
    efn = result['efn']
    efp = result['efp']

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['x [cm]', 'y [cm]', 'v [V_dimless]', 'efn [V_dimless]', 'efp [V_dimless]'])

        for j in range(ny):
            for i in range(nx):
                idx = i + j*nx
                y_val = ypts[j] if ny > 1 else 0
                writer.writerow([xpts[i], y_val, v[idx], efn[idx], efp[idx]])

def check_equal_sim_settings(system1, system2):

    # cycle over all elements of system2
    equivalent = True
    for attr in dir(system2):
        # don't compare G matrices
        if attr == 'g':
            continue
        tfield = getattr(system2,attr)
        # determine if element is an array
        if type(tfield) is np.ndarray:
            tfield1 = getattr(system1, attr)
            if np.array_equal(tfield, tfield1) == False:
                equivalent = False

    return equivalent

