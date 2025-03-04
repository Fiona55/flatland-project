# Imports
from cma.sigma_adaptation import CMAAdaptSigmaTPA
from evaluate import get_env, get_state_action_size, evaluate
from policy import NeuroevoPolicy
from argparse import ArgumentParser
import numpy as np
import logging
import cma
from pymoo.algorithms.soo.nonconvex.cmaes import CMAES
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.core.problem import ElementwiseProblem
from pymoo.factory import get_termination
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pyswarm import pso


# Definition d'un probleme pour l'algorithme CMAES et l'algorithme PSO de Pymoo
class fitness_pymoo(ElementwiseProblem):

    def __init__(self, n_var):
        xl = np.ones(n_var)*(-10)
        xu = np.ones(n_var)*10
        super().__init__(n_var=n_var, n_obj=1, n_constr=0, xl=xl, xu=xu)

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = fit_inv(x)


# Recuperation des arguments passes en entree
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-e', '--env', help='environment', default='small', type=str)
    parser.add_argument('-g', '--gens', help='number of generations', default=100, type=int)
    parser.add_argument('-p', '--pop', help='population size (lambda for the 1+lambda ES)', default=10, type=int)
    parser.add_argument('-s', '--seed', help='seed for evolution', default=0, type=int)
    parser.add_argument('--log', help='log file', default='evolution.log', type=str)
    parser.add_argument('--weights', help='filename to save policy weights', default='weights', type=str)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, encoding='utf-8', level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    # starting point
    env, params = get_env(args.env)
    s, a = get_state_action_size(env)
    policy = NeuroevoPolicy(s, a)

    # evolution
    rng = np.random.default_rng(args.seed)
    start = rng.normal(size=(len(policy.get_params(),)))
    print(start.shape)

    
    # Definition des differents algorithmes testes pour obtenir un resultat optimal
    # Strategies : 1+lambda, CMA-ES (en utilisant les bibliotheques cma et Pymoo), PSO (en utilisant Pyswarm et Pymoo)
    # Strategie choisie : Genetic Algorithm (Pymoo)

    # def oneplus_lambda(x, fitness, gens, lam, std=0.05, rng=np.random.default_rng()):
    #     x_best = x
    #     f_best = -np.Inf
    #     n_evals = 0
    #     for g in range(gens):
    #         N = rng.normal(size=(lam, len(x))) * std
    #         for i in range(lam):
    #             ind = x + N[i, :]
    #             f = fitness(ind)
    #             if f > f_best:
    #                 f_best = f
    #                 x_best = ind
    #         x = x_best
    #         n_evals += lam
    #         logging.info('\t%d\t%d', n_evals, f_best)
    #     return x_best


    # def cma_strat(x_start,fitness):
    #     es = cma.CMAEvolutionStrategy(x_start, 0.5, {'popsize': 10, 'maxfevals': 100})
    #     es.optimize(fitness)
    #     return es.result.xbest
    
    # def pymoo_strat(x_start):
    #     algorithm = CMAES(x0=x_start,sigma=0.1,popsize = 20,maxfevals=1000,restart_from_best=True,CMA_stds=1.5, minstd = -0.15, maxstd = 0.15, bipop=True,restarts=3)
    #     pb = fitness_pymoo(len(x_start))
    #     termination = get_termination("n_gen",50)
    #     res = minimize(pb,
    #            algorithm,
    #            termination,
    #            verbose=True)
    #     return res.X

    # def pymoo_pso(x_start):
    #     algorithm = PSO(pop_size = 20, verbose=True)
    #     pb = fitness_pymoo(len(x_start))
    #     termination = get_termination("n_gen",50)
    #     res = minimize(pb,
    #            algorithm,
    #            termination,
    #            verbose=True)
    #     return res.X

    # def pso_start(x_start,fitness):
    #     n_var = len(x_start)
    #     lb = np.ones(n_var)*(-10)
    #     ub = np.ones(n_var)*10
    #     xopt, _ = pso(fitness, lb, ub, swarmsize=60, omega=0.5, phip=1, phig=1, maxiter=10, debug=True)
    #     return xopt

    def genetic_algorithm(x, fitness):
    # define the problem
        class Trainproblem(ElementwiseProblem):

            def __init__(self,n_var):
                xl = np.ones(n_var)*(-1)
                xu = np.ones(n_var)

                super().__init__(n_var=n_var, n_obj=1, n_constr=0, xl=xl, xu=xu)

            def _evaluate(self, x, out, *args, **kwargs):
                out["F"] = fitness(x)

        problem = Trainproblem(len(x))
        algorithm = GA(pop_size=30, eliminate_duplicates=True, maxfevals=1000)
    
        res = minimize(problem,
               algorithm,
               seed=1,
               verbose=True)
        return res.X


    # Definition des fitness (selon l'algorithme, on utilisera +/- fitness)

    def fitness(x, s, a, env, params):
        policy = NeuroevoPolicy(s, a)
        policy.set_params(x)
        return evaluate(env, params, policy)

    def fit(x):
        return fitness(x, s, a, env, params)

    def fit_inv(x):
        return -fitness(x, s, a, env, params)


    # Calcul du resultat
    #x_best = oneplus_lambda(start, fit, args.gens, args.pop, rng=rng)
    
    #x_best = cma_strat(start,fit_inv)

    #x_best = pymoo_strat(start)

    #x_best = optunity_strat(start,fit)

    #x_best = pso_start(start,fit_inv)
    
    x_best = genetic_algorithm(start, fit_inv)

    #x_best = pymoo_pso(start)


    # Evaluation
    policy.set_params(x_best)
    policy.save(args.weights)
    best_eval = evaluate(env, params, policy)
    print('Best individual: ', x_best[:5])
    print('Fitness: ', best_eval)
