import numpy as np
import sys
import tune

import learning_rate
import linear_models
import neural_model
import helpers
import sgd
import metrics

def conf_interval_plot(data, epochs=300):
    polynomials = 8
    X_train = linear_models.poly_design_matrix(polynomials, data['x_train'])
    X_validate = linear_models.poly_design_matrix(polynomials, data['x_validate'])


    common_ols_kwargs = {'momentum': 0.5, 'init_conds': 50, 'x_shape': X_train.shape[1]}
    common_ridge_kwargs = {'name': 'Ridge', 'beta_func': linear_models.beta_ridge, 'momentum': 0.5, 'init_conds': 50, 'x_shape': X_train.shape[1]}
    subplot_ols_uniques = [{}]
    subplot_ridge_uniques = [{'_lambda': 0.01}, {'_lambda': 0.001}]
    subsubplot_linear_uniques = [{'learning_rate': learning_rate} for learning_rate in np.logspace(-3, -1, 3)]

    unique_sgd_kwargs = [{'mini_batch_size': mini_batch_size} for mini_batch_size in [10, 20, 40]]

    ols_models = helpers.make_models(
        linear_models.LinearRegression,
        common_ols_kwargs,
        subplot_ols_uniques,
        len(unique_sgd_kwargs),
        subsubplot_linear_uniques
        )
    ridge_models = helpers.make_models(
        linear_models.RegularisedLinearRegression,
        common_ridge_kwargs,
        subplot_ridge_uniques,
        len(unique_sgd_kwargs),
        subsubplot_linear_uniques
        )

    subplots = [(models, sgd_kwargs) for models, sgd_kwargs in zip(ols_models + ridge_models, unique_sgd_kwargs*3)]
    errors, subtitle, subplots, metrics_string = sgd.sgd_on_models(X_train, X_validate, data['y_train'], data['y_validate'], *subplots, epochs=epochs)

    title = ['Confidence interval for different learning rates and mini-batch sizes', 'conf_interval', subtitle]
    sgd.plot_sgd_errors(errors, title, metrics_string)

def beta_variance(data, epochs=20000, mini_batch_sizes=[10, 20]):
    polynomials = 8
    X_train = linear_models.poly_design_matrix(polynomials, data['x_train'])
    X_validate = linear_models.poly_design_matrix(polynomials, data['x_validate'])

    total_steps = epochs * len(data['x_train'])//mini_batch_sizes[0]
    learning_rate_func = learning_rate.Learning_rate(base=5e-2, decay=1/100000).compile(total_steps)
    
    common_ridge1_kwargs = {'_lambda': 0.01, 'name': 'Ridge', 'beta_func': linear_models.beta_ridge, 'momentum': 0.5, 'init_conds': 300, 'x_shape': X_train.shape[1]}
    common_ridge2_kwargs = {'_lambda': 0.0001, 'name': 'Ridge', 'beta_func': linear_models.beta_ridge, 'momentum': 0.5, 'init_conds': 300, 'x_shape': X_train.shape[1]}
    subplot_ridge_uniques = [{}]
    subsubplot_ridge_linear_uniques = [{'learning_rate': learning_rate_func}]

    common_ols_kwargs = {'momentum': 0.5, 'init_conds': 300, 'x_shape': X_train.shape[1]}
    subplot_ols_uniques = [{}]
    subsubplot_ols_linear_uniques = [{'learning_rate': learning_rate_func}]

    unique_sgd_kwargs = [{'mini_batch_size': mini_batch_size} for mini_batch_size in mini_batch_sizes]

    ridge_models1 = helpers.make_models(
        linear_models.RegularisedLinearRegression,
        common_ridge1_kwargs,
        [{}],
        len(unique_sgd_kwargs),
        subsubplot_ridge_linear_uniques
        )

    ridge_models2 = helpers.make_models(
        linear_models.RegularisedLinearRegression,
        common_ridge2_kwargs,
        [{}],
        len(unique_sgd_kwargs),
        subsubplot_ridge_linear_uniques
        )

    ols_models = helpers.make_models(
        linear_models.LinearRegression,
        common_ols_kwargs,
        [{}],
        len(unique_sgd_kwargs),
        subsubplot_ols_linear_uniques
        )

    models_list = ridge_models1 + ridge_models2 + ols_models 

    subplots = [(models, sgd_kwargs) for models, sgd_kwargs in zip(models_list, unique_sgd_kwargs*(len(models_list)))]
    errors, subtitle, subplots, metrics_string = sgd.sgd_on_models(X_train, X_validate, data['y_train'], data['y_validate'], *subplots, epochs=epochs, epochs_without_progress=200)

    title = ['Convergence test', 'convergence', subtitle]
    sgd.plot_sgd_errors(errors, title, metrics_string)

    sgd_ridge1_betas = np.array([model.beta for models in ridge_models1 for model in models])
    sgd_ridge1_betas = sgd_ridge1_betas.transpose(1, 2, 0).reshape((sgd_ridge1_betas.shape[1], -1)).T

    sgd_ridge2_betas = np.array([model.beta for models in ridge_models2 for model in models])
    sgd_ridge2_betas = sgd_ridge2_betas.transpose(1, 2, 0).reshape((sgd_ridge2_betas.shape[1], -1)).T

    sgd_ols_betas = np.array([model.beta for models in ols_models for model in models])
    sgd_ols_betas = sgd_ols_betas.transpose(1, 2, 0).reshape((sgd_ols_betas.shape[1], -1)).T

    optimal_models = [linear_models.RegularisedLinearRegression("Ridge", linear_models.beta_ridge, _lambda=_lambda) for _lambda in (0.01, 0.)]
    optimal_betas = np.array([model.fit(X_train, data['y_train']) for model in optimal_models])[:,:,0]

    plots = [
        ['Ridge ($\\lambda 0.01$) trained by SGD', np.arange(1, optimal_betas.shape[1] + 1),
            [[sgd_ridge1_betas, {'notch': False, 'sym': ''}],
            [optimal_betas[0], plotting.scatter_plotter, {'label': 'Analytical $\\lambda$ 0.01'}],
            ]
        ],
        ['Ridge ($\\lambda 0.0001$) trained by SGD', np.arange(1, optimal_betas.shape[1] + 1),
            [[sgd_ridge2_betas, {'notch': False, 'sym': ''}],
            [optimal_betas[0], plotting.scatter_plotter, {'label': 'Analytical $\\lambda$ 0.01'}],
            ]
        ],
        ['OLS trained by SGD', np.arange(1, optimal_betas.shape[1] + 1),
            [[sgd_ols_betas, {'notch': False, 'sym': ''}],
            [optimal_betas[0], plotting.scatter_plotter, {'label': 'Analytical $\\lambda$ 0.01'}],
            ]
        ],
    ]

    side_by_side_parameters = {
        'plotter': plotting.box_plotter,
        'axis_labels': ('Beta parameter #', 'Values'),
        'title': ['$\\beta$ parameters', 'beta', subtitle],
    }
    plotting.side_by_side(*plots, **side_by_side_parameters)

def momemtun_plot(data):
    polynomials = 8
    X_train = linear_models.poly_design_matrix(polynomials, data['x_train'])
    X_validate = linear_models.poly_design_matrix(polynomials, data['x_validate'])

    common_ridge_kwargs = {'name': 'Ridge', 'beta_func': linear_models.beta_ridge, 'momentum': 0.5, 'init_conds': 50, 'x_shape': X_train.shape[1]}
    subplot_ridge_uniques = [{'momentum': 0.9}, {'momentum': 0.6}, {'momentum': 0.3}, {'momentum': 0.}]
    subsubplot_linear_uniques = [{'learning_rate': learning_rate} for learning_rate in np.logspace(-3, -1, 3)]

    unique_sgd_kwargs = [{'mini_batch_size': 10}]

    ridge_models = helpers.make_models(
        linear_models.RegularisedLinearRegression,
        common_ridge_kwargs,
        subplot_ridge_uniques,
        len(unique_sgd_kwargs),
        subsubplot_linear_uniques
        )

    subplots = [(models, sgd_kwargs) for models, sgd_kwargs in zip(ridge_models, unique_sgd_kwargs*len(ridge_models))]

    errors, subtitle, subplots, metrics_string = sgd.sgd_on_models(X_train, X_validate, data['y_train'], data['y_validate'], *subplots, epochs=300)

    title = ['Confidence interval for different momentums and learning rates', 'momentum', subtitle]

    sgd.plot_sgd_errors(errors, title, metrics_string)

def neural_regression(data, mini_batch_size=20, epochs=6000, epochs_without_progress=300):
    total_steps = epochs * len(data['x_train'])//mini_batch_size
    learning_rates = [learning_rate.Learning_rate(base=base, decay=decay).ramp_up(10).compile(total_steps) for base, decay in [(1e-4, 1/5000), (5e-3, 1/2500), (1e-3, 1/2000)]]

    common_kwargs = {'momentum': 0.5}
    hidden_layers_sets = [[{'height': hidden}] for hidden in [2, 4, 6]] + [[{'height': 2}, {'height': 2}]]
    subplot_uniques = [{'layers': [{'height': 2}, *hidden_layers, {'height': 1, 'activation': lambda x: x, 'diff_activation': lambda x: 1}]} for hidden_layers in hidden_layers_sets]
    subsubplot_uniques = [{'learning_rate': learning_rate_func} for learning_rate_func in learning_rates]

    unique_sgd_kwargs = [{'mini_batch_size': mini_batch_size}]

    neural_models = helpers.make_models(
        neural_model.Network,
        common_kwargs,
        subplot_uniques,
        len(unique_sgd_kwargs),
        subsubplot_uniques
        )

    subplots = [(models, sgd_kwargs) for models, sgd_kwargs in zip(neural_models, unique_sgd_kwargs*len(neural_models))]

    errors, subtitle, subplots, metrics_string = sgd.sgd_on_models(data['x_train'], data['x_validate'], data['y_train'], data['y_validate'], *subplots, epochs=epochs, epochs_without_progress=epochs_without_progress)

    title = ['Neural model, regression on terrain data', 'neural_regression', subtitle]

    sgd.plot_sgd_errors(errors, title, metrics_string)

def neural_regression_2(data, mini_batch_size=20, epochs=6000, epochs_without_progress=300):
    total_steps = epochs * len(data['x_train'])//mini_batch_size

    common_kwargs = {'momentum': 0.6}
    subplot_uniques = [{}]
    subsubplot_uniques = [{'name': name, 'learning_rate': learning_rate, 'layers':
                      [{'height': 2}, {'height': 2, 'activation': activation, 'diff_activation': diff_activation}, {'height': 1}]}
                        for name, activation, diff_activation, learning_rate
                        in [('Neural: Sigmoid', neural_model.sigmoid, neural_model.sigmoid_diff, learning_rate.Learning_rate(base=5e-3, decay=1/2500).compile(total_steps)),
                            ('Neural: ReLu', neural_model.ReLu, neural_model.ReLu_diff, learning_rate.Learning_rate(base=1e-4, decay=1/4000).compile(total_steps)),
                            ('Neural: Leaky ReLu', neural_model.leaky_ReLu, neural_model.leaky_ReLu_diff, learning_rate.Learning_rate(base=1e-4, decay=1/4000).compile(total_steps))]]

    unique_sgd_kwargs = [{'mini_batch_size': mini_batch_size}]

    neural_models = helpers.make_models(
        neural_model.Network,
        common_kwargs,
        subplot_uniques,
        len(unique_sgd_kwargs),
        subsubplot_uniques
        )

    subplots = [(models, sgd_kwargs) for models, sgd_kwargs in zip(neural_models, unique_sgd_kwargs*len(neural_models))]

    errors, subtitle, subplots, metrics_string = sgd.sgd_on_models(data['x_train'], data['x_validate'], data['y_train'], data['y_validate'], *subplots, epochs=epochs, epochs_without_progress=epochs_without_progress)

    title = ['Neural model, regression on terrain data', 'neural_regression_2', subtitle]

    sgd.plot_sgd_errors(errors, title, metrics_string)

def neural_classification(data, epochs=10000, epochs_without_progress=1000, mini_batch_size=40):

    total_steps = epochs * len(data['x_train'])//mini_batch_size
    learning_rates = [learning_rate.Learning_rate(base=base, decay=decay).ramp_up(100).compile(total_steps) for base, decay in [(9e-4, 1/4000)]]

    common_kwargs = {'momentum': 0.6}
    subplot_uniques = [{'name': 'Logistic', 'layers': [{'height': 64}, {'height': 10, 'activation': neural_model.softmax, 'd_func': lambda a, y, _: y - a}]}]

<<<<<<< HEAD
    learning_rates = [learning_rate.Learning_rate(base=base, decay=decay).ramp_up(1000).compile(total_steps) for base, decay in [(7e-3, 1/40000)]]

    common_kwargs = {'momentum': 0.5}
    subplot_uniques = [{'layers': [{'height': 64}, {'height': 32}, {'height': 10, 'activation': neural_model.sigmoid, 'd_func': lambda a, y, _: y - a}]}]
=======
    # learning_rates = [learning_rate.Learning_rate(base=base, decay=decay).ramp_up(1000).compile(total_steps) for base, decay in [(2e-3, 1/40000)]]

    # common_kwargs = {'momentum': 0.7}
    # subplot_uniques = [{'name':  'Logistic', 'layers': [{'height': 64}, {'height': 10, 'activation': neural_model.softmax, 'd_func': lambda a, y, _: y - a}]}]
>>>>>>> f943aba2a1b3b4959c41a3da5d02f4f78274e73d

    subsubplot_uniques = [{'learning_rate': learning_rate} for learning_rate in learning_rates]

    unique_sgd_kwargs = [{'mini_batch_size': mini_batch_size}]

    neural_models = helpers.make_models(
        neural_model.Network,
        common_kwargs,
        subplot_uniques,
        len(unique_sgd_kwargs),
        subsubplot_uniques
        )

    subplots = [(models, sgd_kwargs) for models, sgd_kwargs in zip(neural_models, unique_sgd_kwargs*len(neural_models))]

    errors, subtitle, subplots, metric_string = sgd.sgd_on_models(data['x_train'], data['x_validate'], data['y_train'], data['y_validate'], *subplots, epochs=epochs, epochs_without_progress=epochs_without_progress, metric=metrics.cross_entropy)

    title = ['Neural model, Classification test', 'neural_classification', subtitle]

    sgd.plot_sgd_errors(errors, title, metric_string)

<<<<<<< HEAD
    helpers.classification_accuracy(subplots, data)
=======
    classification_accuracy(subplots, data)


def classification_accuracy(subplots, data):
    from sklearn.metrics import classification_report, confusion_matrix, plot_confusion_matrix
    import matplotlib.pyplot as plt
    import seaborn as sns

    best_models = []

    all_models = [models for models, _ in subplots]
    true_train = np.where(mnistData['y_train'] == 1)[1]
    true_val = np.where(mnistData['y_validate'] == 1)[1]
    true_test = np.where(mnistData['y_test'] == 1)[1]
    for j, models in enumerate(all_models):
        model_scores = []

        for k, model in enumerate(models):
            predict_val = np.argmax(model.predict(data['x_validate']), axis=1)

            accuracy = np.mean(predict_val == true_val)
            model_scores.append(accuracy)
        max_score = max(model_scores)


        best_models.append([j, model_scores.index(max_score)])

    for index in best_models:
        model = all_models[index[0]][index[1]]
        predict_train = model.class_predict(data['x_train'])
        predict_val = model.class_predict(data['x_validate'])
        predict_test = model.class_predict(data['x_test'])

        print("Model assessment - test data", model.name)
        print(classification_report(true_test, predict_test))
        print("Model assessment - validation data")
        print(classification_report(true_val, predict_val))
        plt.close()
        cf = confusion_matrix(true_val, predict_val)
        sns.heatmap(cf, annot=True)
        plt.title(f"Confusion matrix - {model.name} \n {len(data['x_validate'])} samples of validation data")
        plt.savefig(f"../plots/classification_cf_{model.name}")



>>>>>>> f943aba2a1b3b4959c41a3da5d02f4f78274e73d

def regression_compare(data, epochs=6000, epochs_without_progress=300, mini_batch_size=20):
    polynomials = 8
    X_train = linear_models.poly_design_matrix(polynomials, data['x_train'])
    X_validate = linear_models.poly_design_matrix(polynomials, data['x_validate'])
    
    total_steps = epochs * len(data['x_train'])//mini_batch_size

    neural = neural_model.Network(
        momentum=0.6,
        layers=[{'height': 2}, {'height': 2}, {'height': 1, 'activation': lambda z: z, 'diff_activation': lambda z: 1}],
        learning_rate=learning_rate.Learning_rate(base=5e-3, decay=1/2500).ramp_up(10).compile(total_steps)
        )

    ridge = [linear_models.RegularisedLinearRegression(
        name='Ridge',
        beta_func=linear_models.beta_ridge,
        momentum=0.6,
        _lambda=0.001,
        x_shape=X_train.shape[1],
        learning_rate=0.01
        ), X_train, X_validate, data['y_train'], data['y_validate']]

    subplots = [([neural, ridge], {'mini_batch_size': mini_batch_size})]

    errors, subtitle, subplots, metrics_string = sgd.sgd_on_models(data['x_train'], data['x_validate'], data['y_train'], data['y_validate'], *subplots, epochs=epochs, epochs_without_progress=epochs_without_progress)

    title = ['Neural vs Ridge model, regression on terrain data', 'regression_vs', subtitle]

    sgd.plot_sgd_errors(errors, title, metrics_string)

def tune_neural_reg(data, epochs=10000, epochs_without_progress=500, mini_batch_size=20):
    total_steps =  epochs * len(data['x_train'])//mini_batch_size
    learning_rates = [learning_rate.Learning_rate(base=base, decay=decay).ramp_up(10).compile(total_steps) for base, decay in [(1e-4, 1/5000), (1e-3, 1/2500), (5e-3, 1/2000), (1e-2, 1/2000)]]

    common_kwargs = {'momentum': 0.6}
    hidden_layers_sets = [[{'height': hidden}] for hidden in [2, 4, 6, 8]] + [[{'height': hidden}, {'height': hidden}] for hidden in [2, 4, 6, 8]]
    subplot_uniques = [{'layers': [{'height': 2}, *hidden_layers, {'height': 1, 'activation': lambda x: x, 'diff_activation': lambda x: 1}]} for hidden_layers in hidden_layers_sets]
    subsubplot_uniques = [{'learning_rate': learning_rate_func} for learning_rate_func in learning_rates]

    unique_sgd_kwargs = [{'mini_batch_size': mini_batch_size}]

    neural_models = helpers.make_models(
        neural_model.Network,
        common_kwargs,
        subplot_uniques,
        len(unique_sgd_kwargs),
        subsubplot_uniques
        )

    models = [model for models in neural_models for model in models]

    tune_obj = tune.Tune(models, data, [metrics.MSE], name="Neural reg tune")
    tune_obj.validate(epochs=epochs, mini_batch_size=mini_batch_size, epochs_without_progress=epochs_without_progress)
    tune_obj.plot_validation_errors()

if __name__ == '__main__':
    import real_terrain
    import mnist

    terrainData = real_terrain.get_data(20)
    mnistData = mnist.get_data(0.6, 0.2)
    neural_classification(mnistData)
    if 'conf' in sys.argv:
        conf_interval_plot(terrainData)
    if 'momentum' in sys.argv:
        momemtun_plot(terrainData)
    if 'neural' in sys.argv and 'reg' in sys.argv:
        neural_regression(terrainData)
        #neural_regression_2(terrainData)
    if 'neural' in sys.argv and 'class' in sys.argv:
        neural_classification(mnistData)
    if 'betas' in sys.argv:
        beta_variance(terrainData)
    if 'compare' in sys.argv and 'reg' in sys.argv:
        regression_compare(terrainData)
    if 'neural_tune' in sys.argv:
        tune_neural_reg(terrainData)


