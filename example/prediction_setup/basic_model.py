"""Basic test for the ML model."""
from __future__ import print_function
from __future__ import absolute_import

import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from atoml.cross_validation import HierarchyValidation
from atoml.feature_preprocess import standardize
from atoml.predict import GaussianProcess

# Set some parameters.
plot = True
ds = 100

# Define the hierarchey cv class method.
hv = HierarchyValidation(db_name='../../data/train_db.sqlite',
                         table='FingerVector',
                         file_name='split')
# Split the data into subsets.
hv.split_index(min_split=ds, max_split=ds*2)
# Load data back in from save file.
ind = hv.load_split()

# Split out the various data.
train_data = np.array(hv._compile_split(ind['1_1'])[:, 1:-1], np.float64)
train_target = np.array(hv._compile_split(ind['1_1'])[:, -1:], np.float64)
test_data = np.array(hv._compile_split(ind['1_2'])[:, 1:-1], np.float64)
test_target = np.array(hv._compile_split(ind['1_2'])[:, -1:], np.float64)

# Scale and shape the data.
std = standardize(train_matrix=train_data, test_matrix=test_data)
train_data, test_data = std['train'], std['test']
train_target = train_target.reshape(len(train_target), )
test_target = test_target.reshape(len(test_target), )


def do_predict(train, test, train_target, test_target, hopt=False):
    """Function to make predictions."""
    kdict = {'k1': {'type': 'gaussian', 'width': 10.}}
    gp = GaussianProcess(train_fp=train, train_target=train_target,
                         kernel_dict=kdict, regularization=0.001,
                         optimize_hyperparameters=hopt)

    pred = gp.get_predictions(test_fp=test,
                              test_target=test_target,
                              get_validation_error=True,
                              get_training_error=True)
    return pred


print('Original parameters')
opt = do_predict(train=train_data, test=test_data, train_target=train_target,
                 test_target=test_target, hopt=False)

# Print the error associated with the predictions.
print('Training error:', opt['training_error']['rmse_average'])
print('Model error:', opt['validation_error']['rmse_average'])

print('Optimized parameters')
nopt = do_predict(train=train_data, test=test_data, train_target=train_target,
                  test_target=test_target, hopt=True)

# Print the error associated with the predictions.
print('Training error:', nopt['training_error']['rmse_average'])
print('Model error:', nopt['validation_error']['rmse_average'])

if plot:
    fig = plt.figure(figsize=(15, 8))
    sns.axes_style('dark')
    sns.set_style('ticks')

    # Setup pandas dataframes.
    opt['actual'] = test_target
    index = [i for i in range(len(test_data))]
    opt_df = pd.DataFrame(data=opt, index=index)
    nopt['actual'] = test_target
    nopt_df = pd.DataFrame(data=nopt, index=index)

    ax = fig.add_subplot(121)
    sns.regplot(x='actual', y='prediction', data=opt_df)
    plt.title('Validation RMSE: {0:.3f}'.format(
        opt['validation_error']['rmse_average']))

    ax = fig.add_subplot(122)
    sns.regplot(x='actual', y='prediction', data=nopt_df)
    plt.title('Validation RMSE: {0:.3f}'.format(
        nopt['validation_error']['rmse_average']))

    plt.show()