import stl.robustness as STL


from stgem.algorithm.ogan.algorithm import OGAN
from stgem.algorithm.ogan.model import OGAN_Model
from stgem.algorithm.random.algorithm import Random
from stgem.algorithm.random.model import Uniform, LHS
from stgem.algorithm.wogan.algorithm import WOGAN
from stgem.algorithm.wogan.model import WOGAN_Model
from stgem.generator import Search
from stgem.objective_selector import ObjectiveSelectorAll
from stgem.objective import FalsifySTL
from stgem.sut.matlab.sut import Matlab_Simulink

mode = "stop_at_first_objective"

ogan_parameters = {"fitness_coef": 0.95,
                   "train_delay": 1,
                   "N_candidate_tests": 1,
                   "reset_each_training": True
                   }

ogan_model_parameters = {
    "convolution": {
        "optimizer": "Adam",
        "discriminator_lr": 0.005,
        "discriminator_betas": [0.9, 0.999],
        "generator_lr": 0.0005,
        "generator_betas": [0.9, 0.999],
        "noise_batch_size": 2048,
        "generator_loss": "MSE,Logit",
        "discriminator_loss": "MSE,Logit",
        "generator_mlm": "GeneratorNetwork",
        "generator_mlm_parameters": {
            "noise_dim": 20,
            "neurons": 64
        },
        "discriminator_mlm": "DiscriminatorNetwork1dConv",
        "discriminator_mlm_parameters": {
            "feature_maps": [16],
            "kernel_sizes": [[2,2]],
            "convolution_activation": "relu",
            "dense_neurons": 32
        },
        "train_settings_init": {"epochs": 2, "discriminator_epochs": 20, "generator_batch_size": 32},
        "train_settings": {"epochs": 1, "discriminator_epochs": 30, "generator_batch_size": 32}
    }
}

def build_specification(selected_specification, mode=None):
    """Builds a specification object and a SUT for the selected specification.
    In addition, returns if scaling and strict horizon check should be used for
    the specification. A previously created SUT can be passed as an argument,
    and then it will be reused."""

    sut_parameters = {"model_file": "cc/cars",
                      "input_type": "piecewise constant signal",
                      "output_type": "signal",
                      "inputs": ["THROTTLE", "BRAKE"],
                      "outputs": ["Y1", "Y2", "Y3", "Y4", "Y5"],
                      "input_range": [[0, 1], [0, 1]],
                      "output_range": [[-5000, 0], [-5000, 0], [-5000, 0], [-5000, 0], [-5000, 0]],
                      "simulation_time": 100,
                      "time_slices": [5, 5],
                      "sampling_step": 0.5
                     }

    # Some ARCH-COMP specifications have requirements whose horizon is longer than
    # the output signal for some reason. Thus strict horizon check needs to be
    # disabled in some cases.
    if selected_specification == "CC1":
        specification = "always[0,100]( Y5 - Y4 <= 40 )"

        specifications = [specification]
        strict_horizon_check = True
    elif selected_specification == "CC2":
        specification = "always[0,70]( eventually[0,30]( Y5 - Y4 >= 15 ) )"

        specifications = [specification]
        strict_horizon_check = True
    elif selected_specification == "CC3":
        specification = "always[0,80]( (always[0,20]( Y2 - Y1 <= 20 )) or (eventually[0,20]( Y5 - Y4 >= 40 )) )"

        specifications = [specification]
        strict_horizon_check = True
    elif selected_specification == "CC4":
        specification = "always[0,65]( eventually[0,30]( always[0,20]( Y5 - Y4 >= 8 ) ) )"

        specifications = [specification]
        strict_horizon_check = False
    elif selected_specification == "CC5":
        specification = "always[0,72]( eventually[0,8]( always[0,5]( Y2 - Y1 >= 9 ) implies always[5,20]( Y5 - Y4 >= 9 ) ) )"

        specifications = [specification]
        strict_horizon_check = True
    elif selected_specification == "CCX":
        def getSpecification(N):
            return "always[0, 50](Y{} - Y{} > 7.5)".format(N+1, N)

        F1 = getSpecification(1)
        F2 = getSpecification(2)
        F3 = getSpecification(3)
        F4 = getSpecification(4)
        specification = "({}) and ({}) and ({}) and ({})".format(F1, F2, F3, F4)

        #specifications = [specification]
        specifications = [F1, F2, F3, F4]
        strict_horizon_check = True
    else:
        raise Exception("Unknown specification '{}'.".format(selected_specification))

    return sut_parameters, specifications, strict_horizon_check

def objective_selector_factory():
    objective_selector = ObjectiveSelectorAll()

def get_objective_selector_factory():
    return objective_selector_factory

def step_factory():
    mode = "stop_at_first_objective"

    step_1 = Search(mode=mode,
                    budget_threshold={"executions": 75},
                    #algorithm=Random(model_factory=(lambda: LHS(parameters={"samples": 75})))
                    algorithm=Random(model_factory=(lambda: Uniform()))
                   )      
    step_2 = Search(mode=mode,
                    budget_threshold={"executions": 300},
                    #algorithm=WOGAN(model_factory=(lambda: WOGAN_Model()))
                    #algorithm=OGAN(model_factory=(lambda: OGANK_Model()))
                    algorithm=OGAN(model_factory=(lambda: OGAN_Model(ogan_model_parameters["convolution"])), parameters=ogan_parameters)
                   )
    #steps = [step_1]
    steps = [step_1, step_2]
    return steps

def get_step_factory():
    return step_factory

