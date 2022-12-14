# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.3.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---
%matplotlib widget
import os, sys

from common import *

# %% [markdown]
# # Load Experiments

# %% [markdown]
An experiment consists of several replicas of STGEM runs on a given benchmark.
The replicas of an experiment correspond to files on a certain path with file
names having a common prefix. Currently the file organization is as follows.
The subdirectories of the base directory (by default `output`) correspond to
the benchmarks. Whenever a replica prefix is specified, all files (including
subdirectories) under `output/benchmark` that have the matching prefix
are collected into one experiment.

# %%
# Default path containing subdirectory for each benchmark.
output_path_base = os.path.join("..", "output")

# Which benchmarks are to be included.
#benchmarks = ["AT"]
benchmarks = ["AFC", "AT"]

# Replica prefixes for collecting the experiments.
replica_prefixes = {"AFC": ["AFC27"],
                    "AT": ["AT1", "ATX13", "ATX14", "ATX2", "ATX61", "ATX62"],
                    "F16": ["F16"]}

experiments = loadExperiments(output_path_base, benchmarks, replica_prefixes)

# %% [markdown]
# # Falsification Rate and First Falsifications

# %%
print("Experiment: Falsification rates:")
for benchmark in benchmarks:
    for experiment in experiments[benchmark]:
        FR = falsification_rate(experiments[benchmark][experiment])
        print("{}/{}, {}".format(benchmark, experiment, FR))


# %%
print("Experiment: Mean: SD:")
data = []
labels = []
for benchmark in benchmarks:
    labels += replica_prefixes[benchmark]
    for experiment in experiments[benchmark]:
        FF = np.array([first_falsification(replica) for replica in experiments[benchmark][experiment]])
        data.append(FF[FF != None])
        print("{}/{}, {}, {}".format(benchmark, experiment, np.mean(data[-1]), np.std(data[-1])))

own_boxplot(data, labels, title="First Falsifications", ylabel="First falsification", line=75)

# %% [markdown]
# # Times

# %%
print("Experiment: Mean time:")
for benchmark in benchmarks:
    for experiment in experiments[benchmark]:
        T = np.array([times(replica) for replica in experiments[benchmark][experiment]])
        print("{}/{}, {}".format(benchmark, experiment, np.mean(T)))

# %% [markdown]
# # Visualize Test Inputs and Outputs

# %% [markdown]
Visualize tests (indices given in `idx`) from a replica. For signal inputs or
outputs, we draw the plots representing the signals. For vector inputs or
outputs, we simply print the vector components. The inputs are always
denormalized, that is, they are given in the format actually given to the SUT.
Outputs are always the outputs of the SUT unmodified.

# %% [markdown]
# TODO
#
# * Include robustness values in the plots.

# %%
benchmark = "F16"
experiment = "F16"
replica_idx = [0]
test_idx = [0]

for i in replica_idx:
    for j in test_idx:
        plotTest(experiments[benchmark][experiment][i], j)

# %% [markdown]
# # Visualization of 1-3D Vector Input Test Suites.

# %% [markdown]
This visualizes the test suites for SUTs which have vector input of dimension
$d$ with $d \leq 3$. The input space is represented as $[-1, 1]^d$ meaning that
inputs are not presented as denormalized to their actual ranges.

# %%
benchmark = "F16"
experiment = "F16"
idx = [0]

for i in idx:
    visualize3DTestSuite(experiments[benchmark][experiment], i)

# %% [markdown]
# # Animate Signal Input/Output Test Suite

# %%
benchmark = "AT"
experiment = "ATX1_ATX1_10000"
replica_idx = 0

anim = animateResult(experiments[benchmark][experiment][replica_idx])
HTML(anim.to_jshtml())

