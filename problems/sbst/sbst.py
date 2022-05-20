from stgem.generator import STGEM, Search
from stgem.budget import Budget
from stgem.algorithm.random.algorithm import Random
from stgem.algorithm.random.model import Uniform, LHS
from stgem.algorithm.wogan.algorithm import WOGAN
from stgem.algorithm.wogan.model import WOGAN_Model
from stgem.objective import Objective
from stgem.objective_selector import ObjectiveSelectorAll

from sut import SBSTSUT

class MaxOOB(Objective):
    """
    Objective which picks the maximum M from an output signal and returns 1-M
    for minimization.
    """

    def __init__(self):
        super().__init__()

        self.dim = 1

    def __call__(self, r):
        return 1 - max(r.outputs[0])

mode = "stop_at_first_objective"

sut_parameters = {
    "beamng_home":  "C:/BeamNG/BeamNG.tech.v0.24.0.1",
    "curvature_points": 5,
    "map_size": 200,
    "max_speed": 75.0
}

wogan_parameters = {
    "bins": 10,
    "wgan_batch_size": 32,
    "fitness_coef": 0.95,
    "train_delay": 3,
    "N_candidate_tests": 1,
    "shift_function": "linear",
    "shift_function_parameters": {"initial": 0, "final": 3},
}

wogan_model_parameters = {
    "critic_optimizer": "Adam",
    "critic_lr": 0.001,
    "critic_betas": [0, 0.9],
    "generator_optimizer": "Adam",
    "generator_lr": 0.001,
    "generator_betas": [0, 0.9],
    "noise_batch_size": 32,
    "gp_coefficient": 10,
    "eps": 1e-6,
    "report_wd": True,
    "analyzer": "Analyzer_NN",
    "analyzer_parameters": {
        "optimizer": "Adam",
        "lr": 0.005,
        "betas": [0, 0.9],
        "loss": "MSE,logit",
        "l2_regularization_coef": 0.001,
        "analyzer_mlm": "AnalyzerNetwork",
        "analyzer_mlm_parameters": {
            "hidden_neurons": [64, 64],
            "layer_normalization": False
        },
    },
    "generator_mlm": "GeneratorNetwork",
    "generator_mlm_parameters": {
        "noise_dim": 20,
        "hidden_neurons": [128, 128],
        "batch_normalization": False,
        "layer_normalization": False
    },
    "critic_mlm": "CriticNetwork",
    "critic_mlm_parameters": {
        "hidden_neurons": [128, 128]
    },
    "train_settings_init": {
        "epochs": 3,
        "analyzer_epochs": 20,
        "critic_steps": 5,
        "generator_steps": 1
    },
    "train_settings": {
        "epochs": 10,
        "analyzer_epochs": 1,
        "critic_steps": 5,
        "generator_steps": 1
    },
}

generator = STGEM(
                  description="SBST 2022 BeamNG.tech simulator",
                  sut=SBSTSUT(sut_parameters),
                  budget=Budget(),
                  objectives=[MaxOOB()],
                  objective_selector=ObjectiveSelectorAll(),
                  steps=[
                         Search(mode=mode,
                                budget_threshold={"executions": 3},
                                algorithm=Random(model_factory=(lambda: Uniform()))),
                         Search(mode=mode,
                                budget_threshold={"executions": 200},
                                algorithm=WOGAN(model_factory=(lambda: WOGAN_Model(wogan_model_parameters)), parameters=wogan_parameters))
                        ]
                  )

if __name__ == "__main__":
    r = generator.run()
