"""Some useful utilities."""
import numpy as np
import hashlib
import time
import multiprocessing
from tqdm import trange, tqdm


class LearningCurve(object):
    """The simple learning curve class."""

    def __init__(self, nprocs=1):
        """Initialize the class.

        Parameters
        ----------
        nprocs : int
            Number of processers used in parallel implementation. Default is 1
            e.g. serial.
        """
        self.nprocs = nprocs

    def learning_curve(self, predict, train, target, test, test_target,
                       step=1, min_data=2):
        """Evaluate custom metrics versus training data size.

        Parameters
        ----------
        predict : object
            A function that will make the predictions. predict should accept
            the parameters:
                train_features : array
                test_features : array
                train_targets : list
                test_targets : list
            predict should return either a float or a list of floats. The float
            or the first value of the list will be used as the fitness score.
        train : array
            An n, d array of training examples.
        targets : list
            A list of the target values.
        test : array
            An n, d array of training examples.
        test targets : list
            A list of the test target values.

        Returns
        -------
        output : array
            Each row is the output from the predict object.
        """
        n, d = np.shape(train)
        # Get total number of iterations
        total = (n - min_data) // step
        output = []
        # Iterate through the data subset.
        if self.nprocs != 1:
            # First a parallel implementation.
            pool = multiprocessing.Pool(self.nprocs)
            tasks = np.arange(total)
            args = (
                (x, step, train, test, target,
                 test_target, predict) for x in tasks)
            for r in tqdm(pool.imap_unordered(
                    self._single_model, args), total=total,
                    desc='nested              ', leave=False):
                output.append(r)
                # Wait to make things more stable.
                time.sleep(0.001)
            pool.close()
        else:
            # Then a more clear serial implementation.
            for x in trange(
                    total,
                    desc='nested              ', leave=False):
                args = (x, step, train, test,
                        target, test_target, predict)
                r = self._single_model(args)
                output.append(r)
        return output

    def _single_model(self, args):
        """Run a model on a subset of training data with a fixed test set.

        Parameters
        ----------
        args : tuple
            Parameters and data to be passed to model.

        Returns
        -------
        f : int
            Feature index being eliminated.
        error : float
            A cost function.
            Typically the log marginal likelihood or goodness of fit.
        meta : list
            Additional optional values. Typically cross validation scores.
        """
        # Unpack args tuple.
        x = args[0]
        n = x * args[1]
        train_features = args[2]
        test = args[3]
        train_targets = args[4]
        test_targets = args[5]
        predict = args[6]

        # Delete required subset of training examples.
        train = train_features[-n:, :]
        targets = train_targets[-n:]

        # Calculate the error or other metrics from the model.
        result = predict(train, targets, test, test_targets)
        return result


def geometry_hash(atoms):
    """A hash based strictly on the geometry features of an atoms object.

    Uses positions, cell, and symbols.

    This is intended for planewave basis set calculations, so pbc is not
    considered.

    Each element is sorted in the algorithem to help prevent new hashs for
    identical geometries.
    """
    atoms.wrap()

    pos = atoms.get_positions()

    # Sort the cell array by magnitude of z, y, x coordinates, in that order
    cell = np.array(sorted(atoms.get_cell(),
                           key=lambda x: (x[2], x[1], x[0])))

    # Flatten the array and return a string of numbers only
    # We only consider position changes up to 3 decimal places
    cell_hash = np.array_str(np.ndarray.flatten(cell.round(3)))
    cell_hash = ''.join(cell_hash.strip('[]').split()).replace('.', '')

    # Sort the atoms positions similarly, but store the sorting order
    pos = atoms.get_positions()
    srt = [i for i, _ in sorted(enumerate(pos),
                                key=lambda x: (x[1][2], x[1][1], x[1][0]))]
    pos_hash = np.array_str(np.ndarray.flatten(pos[srt].round(3)))
    pos_hash = ''.join(pos_hash.strip('[]').split()).replace('.', '')

    # Create a symbols hash in the same fashion conserving position sort order
    sym = np.array(atoms.get_atomic_numbers())[srt]
    sym_hash = np.array_str(np.ndarray.flatten(sym))
    sym_hash = ''.join(sym_hash.strip('[]').split())

    # Assemble a master hash and convert it through an md5
    master_hash = cell_hash + pos_hash + sym_hash
    md5 = hashlib.md5(master_hash)
    _hash = md5.hexdigest()

    return _hash
