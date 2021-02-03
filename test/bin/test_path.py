import unittest
import logging

import os


from core import typing as T
from api.vault.file import convert_vault_rel_to_work_dir_rel, convert_work_dir_rel_to_vault_rel

# At the vault root
# +- some/
#    +- path/
#    |  +- file1
#    |  +- file2

#    +- file3

class TestVaultRelativeToWorkDirRelative(unittest.TestCase):

    def test_child_to_work_dir(self):
        #  some/path/file1, some/path ->  file1
        work_dir = T.Path("some/path")
        vault_relative_path = T.Path("some/path/file1")
        expected = T.Path("file1")
        work_dir_rel = convert_vault_rel_to_work_dir_rel(vault_relative_path, work_dir)
        self.assertEqual(expected, work_dir_rel)


    def test_sibling_to_work_dir(self):
        # this/is/my/file3, this/is/my/path  ->  ../file3,
        work_dir = T.Path("this/is/my/path")
        vault_relative_path = T.Path("this/is/my/file3")
        expected = T.Path("../file3")
        work_dir_rel = convert_vault_rel_to_work_dir_rel(vault_relative_path, work_dir)
        self.assertEqual(expected, work_dir_rel)


