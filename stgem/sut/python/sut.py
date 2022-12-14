import math
import numpy as np
import inspect
from stgem.sut import SUT, SUTOutput

class PythonFunction(SUT):
    """
    A SUT which encapsulates a Python function which we assume to take vectors
    as inputs and output vectors.
    """

    def __init__(self, function, parameters=None):
        super().__init__(parameters)
        self.function = function

        # Use input parameters primarily and function annotation secondarily.
        if "input_range" in self.parameters and len(self.parameters["input_range"]) > 0:
            self.input_range = self.parameters["input_range"]
        else:
            for k, v in self.function.__annotations__.items():
                if k != "return":
                    self.input_range = v

        if "output_range" in self.parameters and len(self.parameters["output_range"]) > 0:
            self.output_range = self.parameters["output_range"]
        else:
            for k, v in self.function.__annotations__.items():
                if k == "return":
                    self.output_range = v

        self.idim = len(self.input_range)
        self.odim = len(self.output_range)

    def _execute_test(self, test):
        denormalized = self.descale(test.inputs.reshape(1, -1), self.input_range).reshape(-1)
        output = []
        error = None
        # Add a exception handler
        try:
            output = self.function(denormalized)
        except Exception as err:
            error = err

        test.input_denormalized = denormalized

        return SUTOutput(np.asarray(output), None, None, error)

