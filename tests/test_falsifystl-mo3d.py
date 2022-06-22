import math
import unittest

import tltk_mtl as STL

from stgem.generator import STGEM, Search
from stgem.sut.python import PythonFunction
from stgem.objective import FalsifySTL

from stgem.algorithm.ogan.algorithm import OGAN
from stgem.algorithm.ogan.model_keras import OGANK_Model
from stgem.algorithm.random.algorithm import Random
from stgem.algorithm.random.model import Uniform

def myfunction(input: [[-15, 15], [-15, 15], [-15, 15]]) -> [[0, 350], [0, 350], [0, 350]]:
    x1, x2, x3 = input[0], input[1], input[2]
    h1 = 305 - 100 * (math.sin(x1 / 3) + math.sin(x2 / 3) + math.sin(x3 / 3))
    h2 = 230 - 75 * (math.cos(x1 / 2.5 + 15) + math.cos(x2 / 2.5 + 15) + math.cos(x3 / 2.5 + 15))
    h3 = (x1 - 7) ** 2 + (x2 - 7) ** 2 + (x3 - 7) ** 2 - (
            math.cos((x1 - 7) / 2.75) + math.cos((x2 - 7) / 2.75) + math.cos((x3 - 7) / 2.75))

    return [h1, h2, h3]

class TestFalsifySTL(unittest.TestCase):
    def test_python(self):
        F1 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o0", var_range=[0, 350]))
        F2 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o1", var_range=[0, 350]))
        F3 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o2", var_range=[0, 350]))
        specification = STL.And(F1, STL.And(F2, F3))

        generator = STGEM(
            description="mo3d-OGAN",
            sut=PythonFunction(function=myfunction),
            objectives=[FalsifySTL(specification=specification, scale=True) ],
            steps=[
                Search(budget_threshold={"executions": 20},
                       algorithm=Random(model_factory=(lambda: Uniform()))),
                Search(budget_threshold={"executions": 25},
                       mode="stop_at_first_objective",
                       algorithm=OGAN(model_factory=(lambda: OGANK_Model()))
                )
            ]
        )

        r = generator.run()

    def test_python_multiple(self):
        from stgem.objective_selector.objective_selector import ObjectiveSelectorMAB

        F1 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o0", var_range=[0, 350]))
        F2 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o1", var_range=[0, 350]))
        F3 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o2", var_range=[0, 350]))

        generator = STGEM(
            description="mo3d-OGAN",
            sut=PythonFunction(function=myfunction),
            objectives=[FalsifySTL(specification=F1, scale=True),
                       FalsifySTL(specification=F2, scale=True),
                       FalsifySTL(specification=F3, scale=True)],
            objective_selector=ObjectiveSelectorMAB(),
            steps=[
                Search(budget_threshold={"executions": 20},
                       algorithm=Random(model_factory=(lambda: Uniform()))),
                Search(budget_threshold={"executions": 25},
                       mode="stop_at_first_objective",
                       algorithm=OGAN(model_factory=(lambda: OGANK_Model()))
                       )
            ]
        )

        r = generator.run()

    def test_MOD3D(self):
        from stgem.sut.mo3d.sut import MO3D

        F1 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o0", var_range=[0, 350]))
        F2 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o1", var_range=[0, 350]))
        F3 = FalsifySTL.StrictlyGreaterThan(1, 0, 0, 0, STL.Signal("o2", var_range=[0, 350]))
        specification = STL.And(F1, STL.And(F2, F3))

        generator = STGEM(
            description="mo3d-OGAN",
            sut=MO3D(),
            objectives=[FalsifySTL(specification=specification, scale=True)],
            steps=[
                Search(budget_threshold={"executions": 20},
                       algorithm=Random(model_factory=(lambda: Uniform()))),
                Search(budget_threshold={"executions": 25},
                       mode="stop_at_first_objective",
                       algorithm=OGAN(model_factory=(lambda: OGANK_Model()))
                       )
            ]
        )

        r = generator.run()

if __name__ == "__main__":
    unittest.main()

