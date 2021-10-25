#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import torch
import torch.nn as nn

# For visualizing the computational graphs.
#from torchviz import make_dot

from neural_networks.ogan.generator import GeneratorNetwork
from neural_networks.ogan.discriminator import DiscriminatorNetwork

from neural_networks.wgan.analyzer import AnalyzerNetwork
from neural_networks.wgan.generator import GeneratorNetwork
from neural_networks.wgan.critic import CriticNetwork

class Model:
  """
  Base class for all models.
  """

  def __init__(self, sut, validator, device):
    self.sut = sut
    self.device = device
    self.validator = validator

  def train_with_batch(self, dataX, dataY, epochs=1, validator_epochs=1, discriminator_epochs=1, use_final=-1):
    raise NotImplementedError()

  def generate_test(self, N=1):
    raise NotImplementedError()

  def validity(self, tests):
    """
    Validate the given test using the true validator.

    Args:
      tests (np.ndarray): Array of shape (N, self.sut.ndimensions).

    Returns:
      output (np.ndarray): Array of shape (N, 1).
    """

    if len(tests.shape) != 2 or tests.shape[1] != self.sut.ndimensions:
      raise ValueError("Input array expected to have shape (N, {}).".format(self.sut.ndimensions))

    if self.validator is None:
      result = np.ones(shape=(tests.shape[0], 1))
    else:
      result = self.validator.validity(tests)

    return result

  def predict_validity(self, tests):
    """
    Validate the given test using the learned proxy validator.

    Args:
      tests (np.ndarray): Array of N tests with shape (N, self.sut.ndimensions).

    Returns:
      result (np.ndarray): Array of shape (N, 1).
    """

    if len(tests.shape) != 2 or tests.shape[1] != self.sut.ndimensions:
      raise ValueError("Input array expected to have shape (N, {}).".format(self.sut.ndimensions))

    if self.validator is None:
      result = np.ones(shape=(tests.shape[0], 1))
    else:
      result = self.validator.predict_validity(tests)

    return result

class OGAN(Model):
  """
  Implements the OGAN model.
  """

  def __init__(self, sut, validator, device):
    # TODO: describe the arguments
    super().__init__(sut, validator, device)

    self.modelG = None
    self.modelD = None
    # Input dimension for the noise inputted to the generator.
    self.noise_dim = 100
    # Number of neurons per layer in the neural networks.
    self.neurons = 128

    # Initialize neural network models.
    self.modelG = GeneratorNetwork(input_shape=self.noise_dim, output_shape=self.sut.ndimensions, neurons=self.neurons).to(self.device)
    self.modelD = DiscriminatorNetwork(input_shape=self.sut.ndimensions, neurons=self.neurons).to(self.device)

    # Loss functions.
    # TODO: figure out a reasonable default and make configurable.
    self.lossG = nn.MSELoss()
    #self.lossG = nn.BCELoss() # binary cross entropy
    #self.lossD = nn.L1Loss()
    self.lossD = nn.MSELoss() # mean square error

    # Optimizers.
    # TODO: figure out reasonable defaults and make configurable.
    lr = 0.001
    #self.optimizerD = torch.optim.RMSprop(self.modelD.parameters(), lr=lr)
    #self.optimizerG = torch.optim.RMSprop(self.modelG.parameters(), lr=lr)
    self.optimizerD = torch.optim.Adam(self.modelD.parameters(), lr=lr)
    self.optimizerG = torch.optim.Adam(self.modelG.parameters(), lr=lr)

  def train_with_batch(self, dataX, dataY, epoch_settings):
    """
    Train the OGAN with a new batch of learning data.

    Args:
      dataX (np.ndarray):             Array of tests of shape
                                      (N, self.sut.ndimensions).
      dataY (np.ndarray):             Array of test outputs of shape (N, 1).
      epoch_settings (dict): A dictionary setting up the number of training
                             epochs for various parts of the model. The keys
                             are as follows:

                               epochs: How many total runs are made with the
                               given training data.

                               discriminator_epochs: How many times the
                               discriminator is trained per epoch.

                               generator_epochs: How many times the generator
                               is trained per epoch.

                             The default for each missing key is 1. Keys not
                             found above are ignored.
    """

    if len(dataX.shape) != 2 or dataX.shape[1] != self.sut.ndimensions:
      raise ValueError("Test array expected to have shape (N, {}).".format(self.ndimensions))
    if len(dataY.shape) != 2 or dataY.shape[0] < dataX.shape[0]:
      raise ValueError("Output array should have at least as many elements as there are tests.")

    dataX = torch.from_numpy(dataX).float().to(self.device)
    dataY = torch.from_numpy(dataY).float().to(self.device)

    # Unpack values from the epochs dictionary.
    epochs = epoch_settings["epochs"] if "epochs" in epoch_settings else 1
    discriminator_epochs = epoch_settings["discriminator_epochs"] if "discriminator_epochs" in epoch_settings else 1
    generator_epochs = epoch_settings["generator_epochs"] if "generator_epochs" in epoch_settings else 1

    # Save the training modes for later restoring.
    training_D = self.modelD.training
    training_G = self.modelG.training
 
    quiet = True

    for n in range(epochs):
      # Train the discriminator.
      # -----------------------------------------------------------------------
      # We want the discriminator to learn the mapping from tests to test
      # outputs.
      self.modelD.train(True)
      for m in range(discriminator_epochs):
        # We the values from [0, 1] to \R using a logit transformation so that
        # MSE loss works better. Since logit is undefined in 0 and 1, we
        # actually first transform the values to the interval [0.01, 0.99].
        D_loss = self.lossD(torch.logit(0.98*self.modelD(dataX) + 0.01), torch.logit(0.98*dataY + 0.01))
        self.optimizerD.zero_grad()
        D_loss.backward()
        self.optimizerD.step()

        if not quiet:
          print("Epoch {}/{}, Discriminator epoch {}/{}, Loss: {}".format(n + 1, epochs, m + 1, discriminator_epochs, D_loss))

      self.modelD.train(False)

      # Visualize the computational graph.
      #print(make_dot(D_loss, params=dict(self.modelD.named_parameters())))

      # Train the generator on the discriminator.
      # -----------------------------------------------------------------------
      # We generate noise and label it to have output 1 (high fitness).
      # Training the generator in this way should shift it to generate tests
      # with high output values (high fitness).
      if self.validator is not None:
        # We need to generate valid tests in order not to confuse the generator
        # by garbage inputs (invalid tests with high fitness do not exist).
        # TODO: Is the following line really needed when not using batch
        #       normalization?
        self.modelG.train(False)
        # TODO: put size into parameter
        inputs = np.zeros(shape=(10, self.sut.ndimensions))
        k = 0
        while k < discriminator_data_size:
          new_test = self.modelG(((torch.rand(size=(1, self.modelG.input_shape)) - 0.5)/0.5).to(self.device)).detach().numpy()
          if self.validator.validity(new_test)[0,0] == 0.0: continue
          inputs[k,:] = new_test[0,:]
          k += 1

        self.modelG.train(True)
        inputs = torch.from_numpy(inputs).float.to(self.device)
      else:
        inputs = ((torch.rand(size=(10, self.modelG.input_shape)) - 0.5)/0.5).to(self.device)

      fake_label = torch.ones(size=(10, 1)).to(self.device)

      # Notice the following subtlety. Above the tensor 'outputs' contains
      # information on how it is computed (the computation graph is being kept
      # track off) up to the original input 'noise' which does not anymore
      # depend on previous operations. Since 'self.modelD' is used as part of
      # the computation, its parameters are present in the computation graph.
      # These parameters are however not updated because the optimizer is
      # initialized only for the parameters of 'self.modelG' (see the
      # initialization of 'self.modelG'.

      for k in range(generator_epochs):
        outputs = self.modelD(self.modelG(inputs))
        # Same comment as above on D_loss.
        G_loss = self.lossG(torch.logit(0.98*outputs + 0.01), torch.logit(0.98*fake_label + 0.01))
        self.optimizerG.zero_grad()
        G_loss.backward()
        self.optimizerG.step()
        if not quiet:
          print("Epoch {}/{}, Generator epoch: {}/{}, Loss: {}".format(n + 1, epochs, k + 1, generator_epochs, G_loss))

      self.modelG.train(False)

      # Visualize the computational graph.
      #print(make_dot(G_loss, params=dict(self.modelG.named_parameters())))

    # Restore the training modes.
    self.modelD.train(training_D)
    self.modelG.train(training_G)

  def generate_test(self, N=1):
    """
    Generate N random tests.

    Args:
      N (int): Number of tests to be generated.

    Returns:
      output (np.ndarray): Array of shape (N, self.sut.ndimensions).
    """

    if N <= 0:
      raise ValueError("The number of tests should be positive.")

    # Generate uniform noise in [-1, 1].
    noise = ((torch.rand(size=(N, self.noise_dim)) - 0.5)/0.5).to(self.device)
    return self.modelG(noise).cpu().detach().numpy()

  def predict_fitness(self, test):
    """
    Predicts the fitness of the given test.

    Args:
      test (np.ndarray): Array of shape (N, self.sut.ndimensions).

    Returns:
      output (np.ndarray): Array of shape (N, 1).
    """

    if len(test.shape) != 2 or test.shape[1] != self.sut.ndimensions:
      raise ValueError("Input array expected to have shape (N, {}).".format(self.sut.ndimensions))

    test_tensor = torch.from_numpy(test).float().to(self.device)
    return self.modelD(test_tensor).cpu().detach().numpy()

class WGAN(Model):
  """
  Implements the WGAN model.
  """

  def __init__(self, sut, validator, device):
    # TODO: describe the arguments
    super().__init__(sut, validator, device)

    self.modelG = None
    self.modelC = None
    self.modelA = None
    # Input dimension for the noise inputted to the generator.
    self.noise_dim = 100
    # Number of neurons per layer in the neural networks.
    self.neurons = 128

    # Initialize neural network models.
    self.modelG = GeneratorNetwork(input_shape=self.noise_dim, output_shape=self.sut.ndimensions, neurons=self.neurons).to(self.device)
    self.modelC = CriticNetwork(input_shape=self.sut.ndimensions, neurons=self.neurons).to(self.device)
    self.modelA = AnalyzerNetwork(input_shape=self.sut.ndimensions, neurons=self.neurons).to(self.device)

    # Loss functions.
    self.lossA = nn.MSELoss()

    # Optimizers.
    # TODO: figure out reasonable defaults and make configurable.
    lr = 0.001
    self.optimizerG = torch.optim.RMSprop(self.modelG.parameters(), lr=lr) # RMSprop with clipping
    self.optimizerC = torch.optim.RMSprop(self.modelC.parameters(), lr=lr) # RMSprop with clipping
    self.optimizerA = torch.optim.Adam(self.modelA.parameters(), lr=lr)

  def train_with_batch(self, data_A_X, data_A_Y, data_C_X, data_C_Y, epoch_settings):
    """
    Train the WGAN with a new batch of learning data.

    Args:
      data_A_X (np.ndarray): Array of tests of shape (N, self.sut.ndimensions).
      data_A_Y (np.ndarray): Array of test outputs of shape (N, 1).
      data_C_X (np.ndarray): Array of tests of shape (M, self.sut.ndimensions).
      data_C_Y (np.ndarray): Array of test outputs of shape (M, 1).
      epoch_settings (dict): A dictionary setting up the number of training
                             epochs for various parts of the model. The keys
                             are as follows:

                               epochs: How many total runs are made with the
                               given training data.

                               analyzer_epochs: How many times the analyzer is
                               trained per epoch.

                               critic_epochs: How many times the critic is
                               trained per epoch.

                               generator_epochs: How many times the generator
                               is trained per epoch.

                             The default for each missing key is 1. Keys not
                             found above are ignored.
    """

    if len(data_A_X.shape) != 2 or data_A_X.shape[1] != self.sut.ndimensions:
      raise ValueError("Array data_A_X expected to have shape (N, {}).".format(self.ndimensions))
    if len(data_A_Y.shape) != 2 or data_A_Y.shape[0] < data_A_X.shape[0]:
      raise ValueError("Array data_A_Y array should have at least as many elements as there are tests.")

    if len(data_C_X.shape) != 2 or data_C_X.shape[1] != self.sut.ndimensions:
      raise ValueError("Array data_C_X expected to have shape (N, {}).".format(self.ndimensions))
    if len(data_C_Y.shape) != 2 or data_C_Y.shape[0] < data_C_X.shape[0]:
      raise ValueError("Array data_C_Y array should have at least as many elements as there are tests.")

    data_A_X = torch.from_numpy(data_A_X).float().to(self.device)
    data_A_Y = torch.from_numpy(data_A_Y).float().to(self.device)
    data_C_X = torch.from_numpy(data_C_X).float().to(self.device)
    data_C_Y = torch.from_numpy(data_C_Y).float().to(self.device)

    # Unpack values from the epochs dictionary.
    epochs = epoch_settings["epochs"] if "epochs" in epoch_settings else 1
    analyzer_epochs = epoch_settings["analyzer_epochs"] if "analyzer_epochs" in epoch_settings else 1
    critic_epochs = epoch_settings["critic_epochs"] if "critic_epochs" in epoch_settings else 1
    generator_epochs = epoch_settings["generator_epochs"] if "generator_epochs" in epoch_settings else 1

    # Save the training modes for later restoring.
    training_A = self.modelA.training
    training_C = self.modelC.training
    training_G = self.modelG.training

    quiet = True

    for n in range(epochs):
      # Train the analyzer.
      # -----------------------------------------------------------------------
      # We want the analyzer to learn the mapping from tests to test outputs.
      self.modelA.train(True)
      for m in range(analyzer_epochs):
        # We map the values from [0, 1] to \R using a logit transformation so
        # that MSE loss works better. Since logit is undefined in 0 and 1, we
        # actually first transform the values to the interval [0.01, 0.99].
        A_loss = self.lossA(torch.logit(0.98*self.modelA(data_A_X) + 0.01), torch.logit(0.98*data_A_Y + 0.01))
        self.optimizerA.zero_grad()
        A_loss.backward()
        self.optimizerA.step()

        if not quiet:
          print("Epoch {}/{}, Analyzer epoch {}/{}, Loss: {}".format(n + 1, epochs, m + 1, analyzer_epochs, A_loss))

      self.modelA.train(False)

      # Visualize the computational graph.
      #print(make_dot(A_loss, params=dict(self.modelA.named_parameters())))

      # Train the critic.
      # -----------------------------------------------------------------------
      self.modelC.train(True)
      for m in range(critic_epochs):
        real_inputs = data_C_X
        real_outputs = self.modelC(real_inputs)
        real_loss = real_outputs.mean(0)

        # TODO: put size into parameter
        noise = ((torch.rand(size=(10, self.modelG.input_shape)) - 0.5)/0.5).to(self.device)
        fake_inputs = self.modelG(noise)
        fake_outputs = self.modelC(fake_inputs)
        fake_loss = fake_outputs.mean(0)

        C_loss = -1*(real_loss - fake_loss) # In fact, we do gradient ascent.
        self.optimizerC.zero_grad()
        C_loss.backward()
        self.optimizerC.step()

        # Clip the weights to the range [-c, c] where c is set below.
        # TODO: make clipping configurable / use gradient penalty
        c = 0.01
        for p in self.modelC.parameters():
          p.data.clamp_(-c, c)

        if not quiet:
          print("Epoch {}/{}, Critic epoch {}/{}, Loss: {}".format(n + 1, epochs, m + 1, critic_epochs, C_loss[0]))

      self.modelC.train(True)

      # Visualize the computational graph.
      #print(make_dot(C_loss, params=dict(self.modelC.named_parameters())))

      # Train the generator.
      # -----------------------------------------------------------------------
      for m in range(generator_epochs):
        # TODO: put size into parameter
        noise = ((torch.rand(size=(10, self.modelG.input_shape)) - 0.5)/0.5).to(self.device)
        outputs = self.modelC(self.modelG(noise))

        G_loss = -outputs.mean(0)
        self.optimizerG.zero_grad()
        G_loss.backward()
        self.optimizerG.step()

        if not quiet:
          print("Epoch {}/{}, Generator epoch {}/{}, Loss: {}".format(n + 1, epochs, m + 1, generator_epochs, G_loss[0]))

      # Visualize the computational graph.
      #print(make_dot(G_loss, params=dict(self.modelG.named_parameters())))

      # TODO: add here some sort of saving mechanism

    # Restore the training modes.
    self.modelA.train(training_A)
    self.modelC.train(training_C)
    self.modelG.train(training_G)

  def generate_test(self, N=1):
    """
    Generate N random tests.

    Args:
      N (int): Number of tests to be generated.

    Returns:
      output (np.ndarray): Array of shape (N, self.sut.ndimensions).
    """

    if N <= 0:
      raise ValueError("The number of tests should be positive.")

    # Generate uniform noise in [-1, 1].
    noise = ((torch.rand(size=(N, self.noise_dim)) - 0.5)/0.5).to(self.device)
    return self.modelG(noise).cpu().detach().numpy()

  def predict_fitness(self, test):
    """
    Predicts the fitness of the given test.

    Args:
      test (np.ndarray): Array of shape (N, self.sut.ndimensions).

    Returns:
      output (np.ndarray): Array of shape (N, 1).
    """

    if len(test.shape) != 2 or test.shape[1] != self.sut.ndimensions:
      raise ValueError("Input array expected to have shape (N, {}).".format(self.sut.ndimensions))

    test_tensor = torch.from_numpy(test).float().to(self.device)
    return self.modelA(test_tensor).cpu().detach().numpy()

class RandomGenerator(Model):
  """
  Implements the random test generator.
  """

  def __init__(self, sut, validator, device):
    # TODO: describe the arguments
    super().__init__(sut, validator, device)

  def train_with_batch(self, dataX, dataY, epochs=1, validator_epochs=1, discriminator_epochs=1, use_final=-1):
    pass

  def generate_test(self, N=1):
    """
    Generate N random tests.

    Args:
      N (int): Number of tests to be generated.

    Returns:
      output (np.ndarray): Array of shape (N, self.sut.ndimensions).
    """

    if N <= 0:
      raise ValueError("The number of tests should be positive.")

    return np.random.uniform(-1, 1, (N, self.sut.ndimensions))

  def predict_fitness(self, test):
    """
    Predicts the fitness of the given test.

    Args:
      test (np.ndarray): Array of shape (N, self.sut.ndimensions).

    Returns:
      output (np.ndarray): Array of shape (N, 1).
    """

    if len(test.shape) != 2 or test.shape[1] != self.sut.ndimensions:
      raise ValueError("Input array expected to have shape (N, {}).".format(self.sut.ndimensions))

    return np.ones(shape=(test.shape[0], 1))

