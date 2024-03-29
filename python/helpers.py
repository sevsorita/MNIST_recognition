import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def filter_dicts(dicts):
    """Splits list of dictionaries into what is common, and what is unique with them.

    Takes in a list of dictionaries, and goes through them all, removing keys where all of the dictionaries have
    that key, and the associated values are all the same. The removed values are stored in a dict, and returnes as well.

    Parameters:
    -----------
    dicts:      list of dictionaries
                Dictionaries you want filtered.

    Returns:
    --------
    filtered_dicts:
                list of dictionaries
                Dictionaries with only the unique key/value combinations in them
    common:     dictionaries
                The key/value combinations that were shared between all the input dictionaries
    """

    common = {}
    unique_keys = {}
    
    keys = [[i, key, value] for i, label_dict in enumerate(dicts) for key, value in label_dict.items()]
    for i, key, value in keys:
        if key not in unique_keys:
            unique_keys[key] = [[i, value]]
        else:
            unique_keys[key].append([i, value])

    for unique_key, value_list in unique_keys.items():
        if len(value_list) == len(dicts):
            equals = 0
            for e, _ in enumerate(value_list[:-1]):
                if value_list[e][1] == value_list[e+1][1]:
                    equals += 1
            if equals == len(value_list)-1:
                common[unique_key] = value_list[0][1]
                for dict_to_filter in dicts:
                    del dict_to_filter[unique_key]
    return dicts, common

def listify_dict_values(dicts):
    """Makes a dict with all the keys from all the dicts, where the values is a list of all the values.
    
    Parameters:
    -----------
    dicts:      list of dicts

    Returns:
    --------
    key_values: dict
    """
    key_values = {}
    for dictionary in dicts:
        for key, value in dictionary.items():
            if key in key_values:
                if value not in key_values[key]:
                    key_values[key].append(value)
            else:
                key_values[key] = [value]
    return key_values

def textify_dict(dictionary):
    """Takes in a dictionary, and makes it into a relatively tidy string.

    Has special rules for some cases, where it for example omits the key name
    because the value is explanatory enough on itself.

    Parameters:
    -----------
    dictionary: dictionarie
                Dictionary you want turned into a string

    Returns:
    --------
    string:     string
                String which describes input dict
    """

    string_list = []
    for key, value in dictionary.items():
        if key == 'model_name':
            string_list.append(value)
        elif key == '_lambda':
            string_list.append(f"($\\lambda ${value})")
        elif key == 'epochs_without_progress':
            string_list.append(f"Epochs w/o progress: {value}")
        elif key == 'epochs':
            pass
        else:
            key = key.replace('_', ' ').capitalize()
            string_list.append(f"{key}: {value}")
    return ' | '.join(string_list)

def make_models(model_class, common_kwargs, subplot_uniques, subplot_copies, subsubplot_uniques):
    """Make list of models with different parameters. Useful for passing to sgd.sgd_on_models.

    Parameters:
    -----------
    model_class:class
                Class (not instance of class) to be called with parameters later specified
    common_kwargs:
                dictionary
                Keyword arguments shared by all the models
    subplot_uniques:
                list of dictionaries
                Each dictionary represents keyword arguments shared by the models in a subplot
    subplot_copies:
                int
                Amount of copies of each model. Used if you want to test the same models on different environments
    subsubplot_uniques:
                list of dictionaries
                Keyword arguments used to differentiate models within subplot

    Returns:
    --------
    models:     list of instances of model:class
                Nested list with subplot as first level, and subsubplots at second level
    """
    models = []
    for _ in range(subplot_copies):
        for subplot_unique_kwargs in subplot_uniques:
            subplot_kwargs = common_kwargs.copy()
            subplot_kwargs.update(subplot_unique_kwargs)
            subplot_models = []
            for subsubplot_unique_kwargs in subsubplot_uniques:
                subsubplot_kwargs = subplot_kwargs.copy()
                subsubplot_kwargs.update(subsubplot_unique_kwargs)
                subplot_models.append(model_class(**subsubplot_kwargs))
            models.append(subplot_models)
    return models