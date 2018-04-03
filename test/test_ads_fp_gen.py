"""Script to test data generation functions."""
from __future__ import print_function
from __future__ import absolute_import

import os
import numpy as np
import unittest

from ase.build import fcc111, add_adsorbate
from ase.data import atomic_numbers
from atoml.fingerprint.adsorbate_prep import autogen_info
from atoml.fingerprint.periodic_table_data import get_radius
from atoml.fingerprint.setup import FeatureGenerator

wkdir = os.getcwd()


class TestAdsorbateFeatures(unittest.TestCase):
    """Test out the adsorbate feature generation."""

    def setup_atoms(self):
        """Get the atoms objects."""
        symbols = ['Ag', 'Au', 'Cu', 'Pt', 'Pd', 'Ir', 'Rh', 'Ni', 'Co']
        images = []
        for i, s in enumerate(symbols):
            rs = get_radius(atomic_numbers[s])
            a = 2 * rs * 2 ** 0.5
            atoms = fcc111(s, (2, 2, 3), a=a)
            atoms.center(vacuum=6, axis=2)
            h = (get_radius(6) + rs) / 2 ** 0.5
            add_adsorbate(atoms, 'C', h, 'bridge')
            atoms.info['dbid'] = i
            atoms.info['key_value_pairs'] = {}
            atoms.info['key_value_pairs']['species'] = 'C'
            atoms.info['key_value_pairs']['layers'] = 3
            atoms.info['key_value_pairs']['bulk'] = s
            atoms.info['key_value_pairs']['term'] = s
            atoms.info['key_value_pairs']['dbid'] = i
            images.append(atoms)
        return images

    def test_ads_fp_gen(self):
        """Test the feature generation."""
        images = self.setup_atoms()
        images = autogen_info(images)
        print(str(len(images)) + ' training examples.')
        gen = FeatureGenerator()
        train_fpv = [gen.ads_nbonds,
                     gen.primary_addatom,
                     gen.primary_adds_nn,
                     gen.bulk,
                     gen.term,
                     gen.strain,
                     gen.Z_add,
                     gen.ads_av,
                     gen.primary_surf_nn,
                     gen.primary_surfatom,
                     gen.get_dbid
                     ]
        matrix = gen.return_vec(images, train_fpv)
        labels = gen.return_names(train_fpv)
        print(np.shape(matrix), type(matrix))
        if __name__ == '__main__':
            for i, l in enumerate(labels):
                print(i, l)
            for dbid in matrix[:, -1]:
                print('last column:', int(dbid))
        self.assertTrue(len(labels) == np.shape(matrix)[1])


if __name__ == '__main__':
    unittest.main()
