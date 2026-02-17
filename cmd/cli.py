"""Comprehensive CLI for Sesame.

This CLI keeps the GUI intact and exposes core functionality via subcommands.
Supported subcommands: `build`, `save`, `load`, `solve`, `ivcurve`, `analyze`, `plot`.
"""

import argparse
import json
import numpy as np
import logging
import os

import sesame
from sesame.utils import save_sim, load_sim
from sesame.analyzer import Analyzer
from configparser import ConfigParser
from ast import literal_eval as ev
import traceback


def make_default_system(nx=150, length=3e-4):
    x = np.linspace(0, length, nx)
    sys = sesame.Builder(x)

    material = {'Nc':8e17, 'Nv':1.8e19, 'Eg':1.5, 'affinity':3.9, 'epsilon':9.4,
            'mu_e':100, 'mu_h':100, 'tau_e':10e-9, 'tau_h':10e-9, 'Et':0}
    sys.add_material(material)

    junction = 50e-7
    def n_region(pos):
        x = pos
        return x < junction
    def p_region(pos):
        x = pos
        return x >= junction
    sys.add_donor(1e17, n_region)
    sys.add_acceptor(1e15, p_region)
    sys.contact_type('Ohmic', 'Ohmic')
    Sn_left, Sp_left, Sn_right, Sp_right = 1e7, 0, 0, 1e7
    sys.contact_S(Sn_left, Sp_left, Sn_right, Sp_right)

    # generation as in the example
    phi = 1e17
    alpha = 2.3e4
    def gfcn(x, y=None):
        return phi * alpha * np.exp(-alpha * x)
    sys.generation(gfcn)

    return sys


def build_system_from_config(cfg):
    """Build a `sesame.Builder` from a config dict.

    Supported keys: mesh (nx,length) or xpts list, materials (list), donors, acceptors,
    defects, contacts, generation (not fully general).
    """
    # mesh
    if 'xpts' in cfg:
        xpts = np.array(cfg['xpts'], dtype=float)
        sys = sesame.Builder(xpts)
    else:
        nx = int(cfg.get('nx', 150))
        length = float(cfg.get('length', 3e-4))
        xpts = np.linspace(0, length, nx)
        sys = sesame.Builder(xpts)

    # materials
    for mat in cfg.get('materials', []):
        loc = mat.get('location', None)
        if loc is None:
            sys.add_material(mat)
        else:
            # location is expected to be a dict with type 'region' and params
            # For simplicity support left/right threshold
            if loc.get('type') == 'x_less':
                thresh = float(loc.get('value'))
                sys.add_material(mat, location=lambda pos: pos < thresh)
            else:
                sys.add_material(mat)

    # donors / acceptors
    for d in cfg.get('donors', []):
        density = float(d.get('density'))
        sys.add_donor(density)
    for a in cfg.get('acceptors', []):
        density = float(a.get('density'))
        sys.add_acceptor(density)

    # contacts
    if 'contacts' in cfg:
        left = cfg['contacts'].get('left', 'Ohmic')
        right = cfg['contacts'].get('right', 'Ohmic')
        sys.contact_type(left, right)

    # generation: simple exponential or provided function not supported
    if 'generation' in cfg:
        g = cfg['generation']
        if g.get('type') == 'exponential':
            phi = float(g.get('phi', 1e17))
            alpha = float(g.get('alpha', 2.3e4))
            sys.generation(lambda x, y=None: phi*alpha*np.exp(-alpha*x))

    return sys


def cmd_build(args):
    # build a system from JSON config or simple flags
    if args.config:
        with open(args.config, 'r') as f:
            cfg = json.load(f)
        sys = build_system_from_config(cfg)
    else:
        sys = make_default_system(nx=args.nx, length=args.length)

    if args.out:
        result = {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}
        save_sim(sys, result, args.out)
        print('Saved system to', args.out)
    else:
        print('Built system: nx={}, ny={}'.format(sys.nx, sys.ny))
    return 0


def cmd_ivcurve(args):
    # build or load system
    if args.mesh_file:
        try:
            sys, _ = load_sim(args.mesh_file)
        except Exception as e:
            logging.error("Could not load mesh file: %s", e)
            return 1
    else:
        sys = make_default_system(nx=args.nx, length=args.length)

    # voltages
    if args.voltages:
        V = np.fromstring(args.voltages, sep=',')
    else:
        V = np.linspace(args.vmin, args.vmax, args.npoints)

    # run IV
    logging.info("Running IVcurve with %d voltages", V.size)
    j = sesame.IVcurve(sys, V, args.out, fmt='npz')

    # Convert to physical units and save summary
    j_phys = j * sys.scaling.current
    np.savez(args.out + "_IV_summary.npz", v=V, j=j_phys)
    print("Saved IV summary to {}".format(args.out + "_IV_summary.npz"))
    return 0


def cmd_save(args):
    # Save a minimal default system to a file
    sys = make_default_system()
    result = {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}
    save_sim(sys, result, args.filename)
    print('Saved simulation to', args.filename)
    return 0


def cmd_load(args):
    try:
        sys, result = load_sim(args.filename)
    except Exception as e:
        logging.error('Could not load file: %s', e)
        return 1
    print('System summary:')
    print(' nx =', sys.nx, ' ny =', sys.ny)
    print(' Has defects:', len(sys.defects_list))
    return 0


def cmd_solve(args):
    try:
        sys, result = load_sim(args.filename)
    except Exception as e:
        logging.error('Could not load file: %s', e)
        return 1
    # Create a fresh Solver instance (not the singleton) to avoid state persistence
    from sesame.solvers import Solver
    solver = Solver()
    sol = solver.solve(sys, compute=args.compute, guess=None, tol=args.tol, 
                       periodic_bcs=not args.no_periodic, maxiter=args.maxiter, 
                       verbose=not args.quiet)
    if sol is None:
        logging.error('Solver failed')
        return 1
    out = args.out or (os.path.splitext(args.filename)[0] + '_sol.gzip')
    save_sim(sys, sol, out)
    print('Saved solution to', out)
    return 0


def cmd_analyze(args):
    try:
        sys, result = load_sim(args.filename)
    except Exception as e:
        logging.error('Could not load file: %s', e)
        return 1
    az = Analyzer(sys, result)
    if args.density:
        if args.density in ('electron', 'both'):
            n = az.electron_density()
            print('Electron density (sample):', n[:5])
        if args.density in ('hole', 'both'):
            p = az.hole_density()
            print('Hole density (sample):', p[:5])
    if args.current:
        J = az.full_current()
        print('Full current:', J * sys.scaling.current)
    if args.recomb:
        if args.recomb == 'srh':
            r = az.bulk_srh_rr()
        elif args.recomb == 'radiative':
            r = az.radiative_rr()
        elif args.recomb == 'auger':
            r = az.auger_rr()
        else:
            r = az.total_rr()
        print('Recombination (sample):', r[:5])
    return 0


def cmd_plot(args):
    # Use Agg backend for headless
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except Exception:
        logging.error('matplotlib not available, cannot plot')
        return 1

    try:
        sys, result = load_sim(args.filename)
    except Exception as e:
        logging.error('Could not load file: %s', e)
        return 1

    what = args.what
    if what == 'grid':
        from sesame.plotter import plot_grid
        fig = plt.figure()
        plot_grid(sys, fig=fig)
        fig.savefig(args.out)
    else:
        # try to find attribute in system or result
        if hasattr(sys, what):
            data = getattr(sys, what)
        elif what in result:
            data = result[what]
        else:
            logging.error('Unknown data to plot: %s', what)
            return 1
        from sesame.plotter import plot
        fig = plt.figure()
        plot(sys, data, fig=fig)
        fig.savefig(args.out)

    print('Saved plot to', args.out)
    return 0


def _load_sys_or_error(filename):
    try:
        sys, result = load_sim(filename)
        return sys, result
    except Exception as e:
        logging.error('Could not load file: %s', e)
        return None, None


def cmd_add_material(args):
    sys, result = _load_sys_or_error(args.filename)
    if sys is None:
        return 1
    # parse material
    if args.mat_file:
        with open(args.mat_file, 'r') as f:
            mat = json.load(f)
    elif args.mat:
        mat = json.loads(args.mat)
    else:
        logging.error('No material provided. Use --mat or --mat-file')
        return 1

    if args.x_less is not None:
        thresh = float(args.x_less)
        sys.add_material(mat, location=lambda pos: pos < thresh)
    else:
        sys.add_material(mat)

    out = args.out or args.filename
    save_sim(sys, result or {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}, out)
    print('Saved updated system to', out)
    return 0


def cmd_add_dopant(args, kind='donor'):
    sys, result = _load_sys_or_error(args.filename)
    if sys is None:
        return 1
    density = float(args.density)
    if kind == 'donor':
        sys.add_donor(density)
    else:
        sys.add_acceptor(density)
    out = args.out or args.filename
    save_sim(sys, result or {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}, out)
    print('Saved updated system to', out)
    return 0


def cmd_add_defect(args):
    sys, result = _load_sys_or_error(args.filename)
    if sys is None:
        return 1
    # parse location
    if args.location.startswith('point:'):
        _, xs = args.location.split(':', 1)
        x = float(xs)
        loc = x
    elif args.location.startswith('line:'):
        _, pts = args.location.split(':', 1)
        a, b = pts.split(';')
        xa, ya = [float(v) for v in a.split(',')]
        xb, yb = [float(v) for v in b.split(',')]
        loc = [(xa, ya), (xb, yb)]
    else:
        logging.error('Bad location format. Use point:x or line:x1,y1;x2,y2')
        return 1

    N = float(args.N)
    sigma_e = float(args.sigma_e)
    sigma_h = float(args.sigma_h) if args.sigma_h is not None else None
    E = float(args.E) if args.E is not None else None
    sys.add_defects(loc, N, sigma_e, sigma_h=sigma_h, E=E)
    out = args.out or args.filename
    save_sim(sys, result or {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}, out)
    print('Saved updated system with defect to', out)
    return 0


def cmd_set_contacts(args):
    sys, result = _load_sys_or_error(args.filename)
    if sys is None:
        return 1
    left = args.left
    right = args.right
    sys.contact_type(left, right, left_wf=args.left_wf, right_wf=args.right_wf)
    if args.contact_S:
        # expect 4 comma-separated numbers
        vals = [float(v) for v in args.contact_S.split(',')]
        sys.contact_S(*vals)
    out = args.out or args.filename
    save_sim(sys, result or {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}, out)
    print('Saved updated contacts to', out)
    return 0


def cmd_set_generation(args):
    sys, result = _load_sys_or_error(args.filename)
    if sys is None:
        return 1
    if args.type == 'exponential':
        phi = float(args.phi)
        alpha = float(args.alpha)
        sys.generation(lambda x, y=None: phi * alpha * np.exp(-alpha * x))
    else:
        logging.error('Generation type not supported')
        return 1
    out = args.out or args.filename
    save_sim(sys, result or {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}, out)
    print('Saved updated generation to', out)
    return 0


def cmd_run_config(args):
    # Read INI config saved by GUI and run simulation headless
    cfg = ConfigParser()
    cfg.optionxform = str
    try:
        cfg.read(args.config)
    except Exception as e:
        logging.error('Could not read config file: %s', e)
        return 1

    try:
        grid = cfg.get('System', 'Grid')
        materials = cfg.get('System', 'Materials')
        defects = cfg.get('System', 'Defects')
        gen = cfg.get('System', 'Generation rate')
        param = cfg.get('System', 'Generation parameter')
        ill_onesun = cfg.get('System', 'One sun illumination')
        man_gen = cfg.get('System', 'Use manual generation')
        ill_monochromatic = cfg.get('System', 'Monochromatic illumination')
        ill_wavelength = cfg.get('System', 'Illumination wavelength')
        ill_power = cfg.get('System', 'Illumination power')
        abs_usefile = cfg.get('System', 'Use absorption file')
        abs_file = cfg.get('System', 'Absorption file')
        abs_useralpha = cfg.get('System', 'Use user-defined alpha')
        abs_alpha = cfg.get('System', 'Alpha')

        # build settings dict for parseSettings
        settings = {}
        settings['grid'] = ev(grid)
        settings['materials'] = ev(materials)
        settings['defects'] = ev(defects)
        settings['gen'] = gen
        settings['use_manual_g'] = (man_gen == 'True')
        settings['ill_onesun'] = (ill_onesun == 'True')
        settings['ill_monochromatic'] = (ill_monochromatic == 'True')
        settings['ill_wavelength'] = ill_wavelength
        settings['ill_power'] = ill_power
        settings['abs_usefile'] = (abs_usefile == 'True')
        settings['abs_useralpha'] = (abs_useralpha == 'True')
        settings['abs_alpha'] = abs_alpha
        settings['abs_file'] = abs_file

    except Exception as e:
        logging.error('Error parsing System section: %s', e)
        logging.debug(traceback.format_exc())
        return 1

    # parse simulation section
    try:
        voltageLoop = cfg.getboolean('Simulation', 'Voltage loop')
        loopValues = cfg.get('Simulation', 'Loop values')
        workDir = cfg.get('Simulation', 'Working directory')
        fileName = cfg.get('Simulation', 'Simulation name')
        ext = cfg.get('Simulation', 'Extension')
        BCs = cfg.getboolean('Simulation', 'Transverse boundary conditions')
        L_contact = cfg.get('Simulation', 'Contact boundary condition in 0')
        R_contact = cfg.get('Simulation', 'Contact boundary condition in L')
        L_WF = cfg.get('Simulation', 'Contact work function in 0')
        R_WF = cfg.get('Simulation', 'Contact work function in L')
        ScnL = float(cfg.get('Simulation', 'Electron recombination velocity in 0'))
        ScpL = float(cfg.get('Simulation', 'Hole recombination velocity in 0'))
        ScnR = float(cfg.get('Simulation', 'Electron recombination velocity in L'))
        ScpR = float(cfg.get('Simulation', 'Hole recombination velocity in L'))
        precision = float(cfg.get('Simulation', 'Newton precision'))
        maxSteps = int(cfg.get('Simulation', 'Maximum steps'))
        useMumps = cfg.getboolean('Simulation', 'Use Mumps')
        iterative = cfg.getboolean('Simulation', 'Iterative solver')
        ramp = int(cfg.get('Simulation', 'Generation ramp'))
        iterPrec = float(cfg.get('Simulation', 'Iterative solver precision'))
        htpy = int(cfg.get('Simulation', 'Newton homotopy'))
    except Exception as e:
        logging.error('Error parsing Simulation section: %s', e)
        logging.debug(traceback.format_exc())
        return 1

    # build sesame system
    try:
        from sesame.ui.common import parseSettings
        system = parseSettings(settings)
    except Exception as e:
        logging.error('Could not construct system from settings: %s', e)
        logging.debug(traceback.format_exc())
        return 1

    # set contacts
    Sc = (ScnL, ScpL, ScnR, ScpR)
    system.contact_type(L_contact, R_contact, left_wf=L_WF or None, right_wf=R_WF or None)
    system.contact_S(*Sc)

    # prepare solver
    from sesame.solvers import Solver
    solver = Solver(use_mumps=useMumps)

    # equilibrium
    guess = solver.make_guess(system)
    solver.solve(system, 'Poisson', guess, precision, BCs, maxSteps, True, htpy)
    if solver.equilibrium is None:
        logging.error('Equilibrium could not be found')
        return 1
    solution = {'efn': np.zeros_like(solver.equilibrium), 'efp': np.zeros_like(solver.equilibrium), 'v': np.copy(solver.equilibrium)}

    # run loops
    if voltageLoop:
        # parse loop values
        try:
            loop_vals = ev(loopValues)
            if isinstance(loop_vals, str):
                loop_vals = [float(x) for x in loop_vals.split(',') if x.strip()]
        except Exception:
            loop_vals = [float(x) for x in loopValues.split(',') if x.strip()]

        # apply generation handling similar to GUI
        if settings.get('gen') and settings.get('use_manual_g'):
            gen_expr = settings.get('gen')
            # gen may be tuple (expr, param)
            if isinstance(gen_expr, tuple):
                generation = gen_expr[0]
            else:
                generation = gen_expr
            if system.dimension == 1:
                f = eval('lambda x:' + generation)
            else:
                f = eval('lambda x,y:' + generation)
            system.generation(f)

        # loop
        nx = system.nx
        s = [nx-1 + j*nx for j in range(system.ny)]
        q = 1 if system.rho[nx-1] < 0 else -1
        Vapp = [i / system.scaling.energy for i in loop_vals]
        for idx, vapp in enumerate(Vapp):
            logging.info('Applied voltage: %s V', loop_vals[idx])
            solution['v'][s] = solver.equilibrium[s] + q*vapp
            solution = solver.solve(system, 'all', solution, precision, BCs, maxSteps, True, htpy)
            if solution is None:
                logging.error('Solver failed at voltage %s', loop_vals[idx])
                return 1
            # save result
            name = os.path.join(args.out_dir, f"{fileName}_{idx}.gzip")
            save_sim(system, solution, name)
            print('Saved', name)

    else:
        logging.info('Generation loop not implemented in CLI run-config')

    return 0


def cmd_simulate(args):
    # Build and run simulation with robust error handling
    try:
        # construct or load mesh/system
        if args.config_json:
            try:
                with open(args.config_json, 'r') as f:
                    cfg = json.load(f)
            except Exception as e:
                logging.error('Could not read config JSON %s: %s', args.config_json, e)
                logging.debug(traceback.format_exc())
                return 2
            try:
                sys = build_system_from_config(cfg)
            except Exception as e:
                logging.error('Invalid config JSON content: %s', e)
                logging.debug(traceback.format_exc())
                return 3
        elif args.xpts_file:
            try:
                xpts = np.load(args.xpts_file, allow_pickle=False)
                sys = sesame.Builder(xpts)
            except Exception as e:
                logging.error('Could not load xpts file %s: %s', args.xpts_file, e)
                logging.debug(traceback.format_exc())
                return 4
        elif args.nx and args.length:
            try:
                nx = int(args.nx)
                length = float(args.length)
                x = np.linspace(0, length, nx)
                sys = sesame.Builder(x)
            except Exception as e:
                logging.error('Bad mesh parameters: %s', e)
                logging.debug(traceback.format_exc())
                return 5
        else:
            sys = make_default_system()

        # override materials if requested
        if args.materials_file:
            try:
                with open(args.materials_file, 'r') as f:
                    mats = json.load(f)
                if not isinstance(mats, list):
                    raise ValueError('materials file must contain a list')
                for mat in mats:
                    loc = mat.get('location', '')
                    if loc == '' or loc is None:
                        sys.add_material(mat)
                    else:
                        if isinstance(loc, dict) and loc.get('type') == 'x_less':
                            thresh = float(loc.get('value'))
                            sys.add_material(mat, location=lambda pos: pos < thresh)
                        else:
                            sys.add_material(mat)
            except Exception as e:
                logging.error('Could not load materials file %s: %s', args.materials_file, e)
                logging.debug(traceback.format_exc())
                return 6

        # defects
        if args.defects_file:
            try:
                with open(args.defects_file, 'r') as f:
                    defs = json.load(f)
                if not isinstance(defs, list):
                    raise ValueError('defects file must contain a list')
                for d in defs:
                    loc = d.get('location')
                    N = float(d.get('Density'))
                    se = float(d.get('sigma_e', d.get('sigma', 1e-14)))
                    sh = float(d.get('sigma_h', se))
                    E = float(d.get('Energy', 0))
                    if isinstance(loc, list) and len(loc) == 2:
                        sys.add_defects(loc, N, se, sigma_h=sh, E=E)
                    else:
                        sys.add_defects(float(loc), N, se, sigma_h=sh, E=E)
            except Exception as e:
                logging.error('Could not load defects file %s: %s', args.defects_file, e)
                logging.debug(traceback.format_exc())
                return 7

        # generation
        try:
            if args.use_manual_g and args.gen_expr:
                expr = args.gen_expr
                if sys.dimension == 1:
                    gen_f = eval('lambda x:' + expr, {'np': np})
                else:
                    gen_f = eval('lambda x,y:' + expr, {'np': np})
                sys.generation(gen_f)
            elif args.monochromatic and args.wavelength and args.power:
                phi = float(args.power)
                alpha = 2.3e4
                sys.generation(lambda x, y=None: phi * alpha * np.exp(-alpha * x))
        except Exception as e:
            logging.error('Could not set generation function: %s', e)
            logging.debug(traceback.format_exc())
            return 8

        # contacts and Sc
        try:
            left = args.left_contact
            right = args.right_contact
            sys.contact_type(left, right, left_wf=args.left_wf, right_wf=args.right_wf)
            if args.Sc:
                vals = [float(v) for v in args.Sc.split(',')]
                if len(vals) != 4:
                    raise ValueError('Sc must be four comma-separated numbers')
                sys.contact_S(*vals)
        except Exception as e:
            logging.error('Could not set contacts: %s', e)
            logging.debug(traceback.format_exc())
            return 9

        # prepare solver
        try:
            from sesame.solvers import Solver
            solver = Solver(use_mumps=bool(args.use_mumps))
        except Exception as e:
            logging.error('Could not initialize solver: %s', e)
            logging.debug(traceback.format_exc())
            return 10

        # initial equilibrium with retries (in case Newton diverges)
        try:
            guess = solver.make_guess(sys)
            solver.solve(sys, 'Poisson', guess, args.tol, args.periodic, args.maxiter, True, args.htpy)
            if solver.equilibrium is None:
                # try with larger homotopy steps and small perturbed guesses
                tried = False
                for htry in (max(2, args.htpy), 5, 10):
                    logging.info('Retry equilibrium with homotopy htp=%s', htry)
                    solver.solve(sys, 'Poisson', guess, args.tol, args.periodic, args.maxiter, True, htry)
                    if solver.equilibrium is not None:
                        tried = True
                        break
                    # try small perturbations to the guess
                    for perturb in (1e-4, 1e-3, 1e-2):
                        pg = guess + perturb * np.sin(np.linspace(0, np.pi, guess.size))
                        logging.info('Retry equilibrium with htp=%s and perturb=%s', htry, perturb)
                        solver.solve(sys, 'Poisson', pg, args.tol, args.periodic, args.maxiter, True, htry)
                        if solver.equilibrium is not None:
                            tried = True
                            break
                    if tried:
                        break
            if solver.equilibrium is None:
                logging.error('Equilibrium could not be found after retries')
                # save debug system for inspection
                try:
                    dbgname = os.path.join(args.out_dir, args.file_name + '_debug_system.gzip')
                    save_sim(sys, {'v': np.zeros(sys.nx*sys.ny), 'efn': np.zeros(sys.nx*sys.ny), 'efp': np.zeros(sys.nx*sys.ny)}, dbgname)
                    logging.info('Saved debug system to %s', dbgname)
                except Exception:
                    logging.debug('Could not save debug system')
                logging.error('Suggestions: try coarser/finer mesh (--nx), increase --htpy, run under GUI to inspect material/doping, or adjust solver parameters (--tol, --maxiter).')
                return 11
            solution = {'efn': np.zeros_like(solver.equilibrium), 'efp': np.zeros_like(solver.equilibrium), 'v': np.copy(solver.equilibrium)}
        except Exception as e:
            logging.error('Error during equilibrium solve: %s', e)
            logging.debug(traceback.format_exc())
            return 12

        # determine loop values
        try:
            if args.voltage_loop:
                if args.loop_values:
                    loop_vals = np.fromstring(args.loop_values, sep=',')
                else:
                    loop_vals = np.linspace(0, 0.95, 10)
                is_voltage = True
            elif args.generation_loop:
                loop_vals = np.fromstring(args.loop_values, sep=',') if args.loop_values else np.array([1.0])
                is_voltage = False
            else:
                loop_vals = np.array([0.0])
                is_voltage = True
        except Exception as e:
            logging.error('Could not parse loop values: %s', e)
            logging.debug(traceback.format_exc())
            return 13

        # ensure out_dir exists
        try:
            os.makedirs(args.out_dir, exist_ok=True)
        except Exception as e:
            logging.error('Could not create output directory %s: %s', args.out_dir, e)
            logging.debug(traceback.format_exc())
            return 14

        # run loop
        if is_voltage:
            try:
                nx = sys.nx
                s = [nx-1 + j*nx for j in range(sys.ny)]
                q = 1 if sys.rho[nx-1] < 0 else -1
                for idx, val in enumerate(loop_vals):
                    vapp = float(val) / sys.scaling.energy
                    solution['v'][s] = solver.equilibrium[s] + q*vapp
                    solution = solver.solve(sys, 'all', solution, args.tol, args.periodic, args.maxiter, True, args.htpy)
                    if solution is None:
                        logging.error('Solver failed at value %s', val)
                        return 15
                    name = os.path.join(args.out_dir, f"{args.file_name}_{idx}.gzip")
                    try:
                        save_sim(sys, solution, name)
                        print('Saved', name)
                    except Exception as e:
                        logging.error('Could not save result %s: %s', name, e)
                        logging.debug(traceback.format_exc())
                        return 16
            except Exception as e:
                logging.error('Error during voltage loop: %s', e)
                logging.debug(traceback.format_exc())
                return 17
        else:
            logging.info('Generation-loop simulation not fully implemented via simulate')

        return 0
    except Exception as e:
        logging.error('Unexpected error in simulate: %s', e)
        logging.debug(traceback.format_exc())
        return 99


def build_parser():
    p = argparse.ArgumentParser(prog='sesame-cli', description='Sesame comprehensive CLI')
    sub = p.add_subparsers(dest='cmd')

    iv = sub.add_parser('ivcurve', help='Compute IV curve (minimal defaults)')
    iv.add_argument('--mesh-file', help='Load system from a saved .gzip file')
    iv.add_argument('--nx', type=int, default=150, help='Number of x points for default mesh')
    iv.add_argument('--length', type=float, default=3e-4, help='Length of system in cm')
    iv.add_argument('--voltages', help='Comma-separated voltages, e.g. "0,0.1,0.2"')
    iv.add_argument('--vmin', type=float, default=0.0)
    iv.add_argument('--vmax', type=float, default=0.95)
    iv.add_argument('--npoints', type=int, default=10)
    iv.add_argument('--out', default='iv_out', help='Output prefix for saved files')
    iv.set_defaults(func=cmd_ivcurve)

    # build
    bld = sub.add_parser('build', help='Build system from JSON config or defaults')
    bld.add_argument('--config', help='JSON config file describing system')
    bld.add_argument('--nx', type=int, default=150)
    bld.add_argument('--length', type=float, default=3e-4)
    bld.add_argument('--out', help='Output filename to save system (.gzip)')
    bld.set_defaults(func=cmd_build)

    # save/load
    sv = sub.add_parser('save', help='Save current system+result to file')
    sv.add_argument('filename', help='Output filename (.gzip)')
    sv.set_defaults(func=cmd_save)

    ld = sub.add_parser('load', help='Load a saved system and print summary')
    ld.add_argument('filename', help='Input filename (.gzip)')
    ld.set_defaults(func=cmd_load)

    # solve
    svp = sub.add_parser('solve', help='Solve a saved system')
    svp.add_argument('filename', help='Saved system (.gzip)')
    svp.add_argument('--compute', choices=['all', 'Poisson'], default='all')
    svp.add_argument('--tol', type=float, default=1e-6)
    svp.add_argument('--maxiter', type=int, default=300)
    svp.add_argument('--no-periodic', action='store_true', help='Disable periodic BCs')
    svp.add_argument('--out', help='Output filename for solution (.gzip)')
    svp.add_argument('--quiet', action='store_true')
    svp.set_defaults(func=cmd_solve)

    # analyze
    an = sub.add_parser('analyze', help='Analyze a saved simulation')
    an.add_argument('filename', help='Saved simulation (.gzip)')
    an.add_argument('--density', choices=['electron', 'hole', 'both'], help='Compute densities')
    an.add_argument('--current', action='store_true', help='Compute full current')
    an.add_argument('--recomb', choices=['srh', 'radiative', 'auger', 'total'], help='Compute recombination')
    an.set_defaults(func=cmd_analyze)

    # plot
    pl = sub.add_parser('plot', help='Plot results from a saved simulation (headless)')
    pl.add_argument('filename', help='Saved simulation (.gzip)')
    pl.add_argument('--what', choices=['grid', 'Eg', 'mu_e', 'mu_h', 'v', 'efn', 'efp'], default='v')
    pl.add_argument('--out', default='plot.png', help='Output image filename')
    pl.set_defaults(func=cmd_plot)

    # add-material
    am = sub.add_parser('add-material', help='Add material to a saved system')
    am.add_argument('filename', help='Saved system (.gzip)')
    am.add_argument('--mat', help='Material JSON string, e.g. "{\"Nc\":8e17,...}"')
    am.add_argument('--mat-file', help='Path to JSON file with material dict')
    am.add_argument('--x-less', help='Only apply material where x < value (in cm)')
    am.add_argument('--out', help='Output filename to save updated system')
    am.set_defaults(func=cmd_add_material)

    # add-donor / add-acceptor
    dd = sub.add_parser('add-donor', help='Add donor doping to a saved system')
    dd.add_argument('filename', help='Saved system (.gzip)')
    dd.add_argument('density', help='Doping density [cm^-3]')
    dd.add_argument('--out', help='Output filename')
    dd.set_defaults(func=lambda a: cmd_add_dopant(a, kind='donor'))

    aa = sub.add_parser('add-acceptor', help='Add acceptor doping to a saved system')
    aa.add_argument('filename', help='Saved system (.gzip)')
    aa.add_argument('density', help='Doping density [cm^-3]')
    aa.add_argument('--out', help='Output filename')
    aa.set_defaults(func=lambda a: cmd_add_dopant(a, kind='acceptor'))

    # add-defect
    df = sub.add_parser('add-defect', help='Add a defect (point or line) to a saved system')
    df.add_argument('filename', help='Saved system (.gzip)')
    df.add_argument('location', help='Location format: point:x or line:x1,y1;x2,y2')
    df.add_argument('N', help='Defect DOS (float)')
    df.add_argument('sigma_e', help='Electron capture cross-section')
    df.add_argument('--sigma_h', help='Hole capture cross-section')
    df.add_argument('--E', help='Energy level (eV)')
    df.add_argument('--out', help='Output filename')
    df.set_defaults(func=cmd_add_defect)

    # set-contacts
    ct = sub.add_parser('set-contacts', help='Set contact types and surface recombination')
    ct.add_argument('filename', help='Saved system (.gzip)')
    ct.add_argument('--left', default='Ohmic')
    ct.add_argument('--right', default='Ohmic')
    ct.add_argument('--left-wf', type=float, help='Left work function (eV)')
    ct.add_argument('--right-wf', type=float, help='Right work function (eV)')
    ct.add_argument('--contact-S', help='Comma-separated Sn_left,Sp_left,Sn_right,Sp_right')
    ct.add_argument('--out', help='Output filename')
    ct.set_defaults(func=cmd_set_contacts)

    # set-generation
    sg = sub.add_parser('set-generation', help='Set generation profile')
    sg.add_argument('filename', help='Saved system (.gzip)')
    sg.add_argument('--type', choices=['exponential'], default='exponential')
    sg.add_argument('--phi', type=float, default=1e17)
    sg.add_argument('--alpha', type=float, default=2.3e4)
    sg.add_argument('--out', help='Output filename')
    sg.set_defaults(func=cmd_set_generation)

    # run-config (execute a GUI .ini configuration headless)
    rc = sub.add_parser('run-config', help='Run a saved GUI .ini configuration headless')
    rc.add_argument('config', help='Configuration .ini file saved by the GUI')
    rc.add_argument('--out-dir', help='Output directory for results', default='.')
    rc.set_defaults(func=cmd_run_config)

    # simulate: full-featured CLI exposure of GUI options
    sim = sub.add_parser('simulate', help='Build and run a simulation exposing GUI options')
    sim.add_argument('--config-json', help='JSON file with full config (materials, defects, grid, simulation)')
    sim.add_argument('--xpts-file', help='Numpy .npy file with xpts array')
    sim.add_argument('--nx', type=int, help='Number of x points (used with --length)')
    sim.add_argument('--length', type=float, help='Length in cm (used with --nx)')
    sim.add_argument('--materials-file', help='JSON file with list of material dicts')
    sim.add_argument('--defects-file', help='JSON file with list of defects')
    sim.add_argument('--use-manual-g', action='store_true', help='Provide manual generation expression')
    sim.add_argument('--gen-expr', help='Generation expression, e.g. "phi*alpha*np.exp(-alpha*x)"')
    sim.add_argument('--onesun', action='store_true')
    sim.add_argument('--monochromatic', action='store_true')
    sim.add_argument('--wavelength', type=float)
    sim.add_argument('--power', type=float)
    sim.add_argument('--abs-file', help='Absorption file path (lambda,alpha)')
    sim.add_argument('--user-alpha', nargs='+', type=float, help='User-defined alpha array (space separated)')

    sim.add_argument('--voltage-loop', action='store_true', help='Run voltage loop')
    sim.add_argument('--generation-loop', action='store_true', help='Run generation loop')
    sim.add_argument('--loop-values', help='Comma-separated loop values (voltages or generation)')
    sim.add_argument('--file-name', default='sim', help='Base filename for outputs')
    sim.add_argument('--ext', choices=['.npz', '.mat'], default='.npz')
    sim.add_argument('--periodic', action='store_true', help='Periodic transverse BCs')
    sim.add_argument('--left-contact', default='Ohmic')
    sim.add_argument('--right-contact', default='Ohmic')
    sim.add_argument('--left-wf', type=float)
    sim.add_argument('--right-wf', type=float)
    sim.add_argument('--Sc', help='Comma-separated recombination velocities: ScnL,ScpL,ScnR,ScpR')

    sim.add_argument('--ramp', type=int, default=0)
    sim.add_argument('--tol', type=float, default=1e-6)
    sim.add_argument('--maxiter', type=int, default=300)
    sim.add_argument('--use-mumps', action='store_true')
    sim.add_argument('--iterative', action='store_true')
    sim.add_argument('--iter-prec', type=float, default=1e-6)
    sim.add_argument('--htpy', type=int, default=1)
    sim.add_argument('--out-dir', default='.', help='Directory to write outputs')
    sim.set_defaults(func=cmd_simulate)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
