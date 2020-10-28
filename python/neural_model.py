import numpy as np
import matplotlib.pyplot as plt

def sigmoid(z):
    return 1/(1 + np.exp(-z))


def sigmoidPrime(z):
    return sigmoid(z)*(1-sigmoid(z))


def cost(actualOutput, optimal_output):
    return np.square(optimal_output - actualOutput)


def cost_diff(actualOutput, optimal_output):
    return 2 * (optimal_output - actualOutput)


class Layer:
    """Generic layer in neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    """
    def __init__(self, height):
        self.a = np.zeros(height)
        self.height = height


class Input(Layer):
    """Input layer in neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    """
    def __init__(self, height):
        super().__init__(height)


class Dense(Layer):
    """Hidden, dense layer in neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    activation: array of floats -> array of floats
                Activation function. Sigmoid by default.
    diff_activation:
                array of floats -> array of floats
                Differentiation of activation function.
    """
    def __init__(self, height, activation=sigmoid, diff_activation=sigmoidPrime):
        super().__init__(height)
        self.z = np.zeros_like(self.a)
        self.d = np.zeros_like(self.a)
        self.activation, self.diff_activation = activation, diff_activation

    def feed_forward(self, prevLayer):
        """Feed forward values through this layer.

        Parameters:
        -----------
        prevLayer:  array of floats
                    Activation values from previous layer
        """
        self.z = np.dot(prevLayer.a, self.weights) + self.bias
        self.a = self.activation(self.z)

    def back_propagate(self, nextLayer):
        self.d = np.dot(nextLayer.weights, nextLayer.d.T).T * self.diff_activation(self.z)

    def set_prevLayer(self, prevLayerHeight):
        """Initialise weights and biases after making the layer before it.

        Parameters:
        -----------
        prevLayerHeight:
                    int
                    Number of neurons in previous layer.
        """
        self.weights = np.random.normal(0, 1, (prevLayerHeight, self.height))
        self.bias = np.random.normal(0, 1, self.height)



class Output(Dense):
    """Output layer for neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    activation: array of floats -> array of floats
                Activation function. Sigmoid by default.
    diff_activation:
                array of floats -> array of floats
                Differentiation of activation function.
    cost_diff:  array of floats -> array of floats
                Differentiation of cost function.
    """
    def __init__(self, height, activation=sigmoid, diff_activation=sigmoidPrime, cost_diff=cost_diff):
        super().__init__(height, activation, diff_activation)
        self.cost_diff = cost_diff

    def back_propagate(self, optimal):
        """back_propagate error through this layer.

        Parameters:
        -----------
        optimal:    array of floats
                    Optimal output.
        """
        self.d = self.cost_diff(self.a, optimal) * self.diff_activation(self.z)


class Network:
    """Network class that stores layers, and organises interactions between them
    
    Parameters:
    -----------
    learning_rate:
                float
                Learning rate for network, used during backpropagation. Should be between 0 and 1.
    """
    def __init__(self, learning_rate=0.006):
        self.learning_rate = learning_rate
        self.network = []
        self.theta = np.array([], dtype=object)

    def addLayer(self, layer):
        """Add a layer to network.
        
        Parameters:
        -----------
        layer:      subclass of Layer
                    Layer to add to the end of this network.
        """
        self.network.append(layer)


    def compile(self):
        """Compiles the network by initialising weights, and making the list of layers an array.

        Also functions as a reset to random initial conditions.
        """
        theta = self.theta.tolist()
        for i in range(1, len(self.network)):
            self.network[i].set_prevLayer(self.network[i-1].height)
            theta.append((self.network[i].weights, self.network[i].bias))
        self.theta = np.array(theta, dtype=object)
        self.network = np.asarray(self.network)

    def feed_forward(self, input_neurons):
        """Feeds forward through the network with a given input.
        
        Parameters:
        -----------
        input_neurons:
                    array of floats
                    Input values. Must have same shape as input layer.
        """
        self.network[0].a = input_neurons
        for i in range(1, len(self.network)):
            self.network[i].feed_forward(self.network[i-1])

    def predict(self, x):
        self.feed_forward(x)
        return self.network[-1].a

    def back_propagate(self, optimal_output):
        """Propagates the error back through the network, and steps in a direction of less loss.
        
        Parameters:
        -----------
        optimal_output:
                    array of floats
                    Optimal or desired output values. Must have same shape as output layer.
        """

        for i in reversed(range(1, len(self.network))):
            if i == len(self.network) - 1:
                backprop_data = optimal_output
            else:
                backprop_data = self.network[i+1]

            self.network[i].back_propagate(backprop_data)

            self.network[i].bias += np.mean(self.network[i].d, axis=0) * self.learning_rate
            self.network[i].weights += np.dot(self.network[i - 1].a.T, self.network[i].d) * self.learning_rate

    def backprop(self, input, optimal_output):
        """

        Args:
            input: input data
            optimal_output: target data

        Returns:
            nabla_b: gradient of bias
            nabla_w: gradient of weights
        """

        nabla_b = []
        nabla_w = []
        self.feed_forward(input)
        for i in reversed(range(1, len(self.network))):
            if i == len(self.network) - 1:
                backprop_data = optimal_output
            else:
                backprop_data = self.network[i+1]
            self.network[i].back_propagate(backprop_data)

            nabla_b.append(np.mean(self.network[i].d, axis=0))
            nabla_w.append(np.dot(self.network[i - 1].a.T, self.network[i].d))

        return nabla_b, nabla_w

    def update_parameters(self, mini_batch_x):
        nabla_b = []
        nabla_w = []
        for i in reversed(range(1, len(self.network))):
            nabla_b.append(np.zeros_like(self.network[i].bias))
            nabla_w.append(np.zeros_like(self.network[i].weights))

        for x in mini_batch_x:
            delta_nabla_b, delta_nabla_w = self.backprop(x[0], x[1])
            nabla_b = [nb + dnb for nb, dnb in zip(nabla_b, delta_nabla_b)]
            nabla_w = [nw + dnw for nw, dnw in zip(nabla_w, delta_nabla_w)]

        nabla_b.reverse()
        nabla_w.reverse()
        for i in reversed(range(1, len(self.network))):
            self.network[i].weights += nabla_w[i-1]*self.learning_rate
            self.network[i].bias += nabla_b[i-1]*self.learning_rate

    def __str__(self):
        """Returns a printable string with all the networks biases and weights.
        """
        string = "Neural net\n"
        for i in range(1, len(self.network)):
            string += f"Layer {i}\n   Biases: {self.network[i].bias.shape}\n   Weights: {self.network[i].weights.shape}\n"
            #string += f"delta_b = {self.network[i].delta_b.shape}\n delta_w: {self.network[i].delta_w.shape}"
        return string