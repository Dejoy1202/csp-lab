import unittest
from checkers import check_output

class ConstructionCheckerTests(unittest.TestCase):
    data='3 2 0\n1 2 4\n'
    def test_alternative_valid_order_and_labels(self):
        self.assertTrue(check_output('CSP_GROUP_PARTITION',self.data,'2\n2 1 4\n1 2\n',b'2 1 2 2 4 1'))
    def test_count_credit_requires_well_formed_output(self):
        self.assertTrue(check_output('CSP_GROUP_COUNT',self.data,'2',b'2 0 0'))
        self.assertFalse(check_output('CSP_GROUP_PARTITION',self.data,'2',b'2 0 0'))
        self.assertFalse(check_output('CSP_GROUP_COUNT',self.data,'2',b'2 0'))
    def test_membership_duplicates_and_bad_minimum(self):
        for output in (b'2 2 1 2 1 4',b'2 2 1 4 1 1',b'2 2 1 4 1 8',b'3 1 1 1 2 1 4'):
            self.assertFalse(check_output('CSP_GROUP_PARTITION',self.data,'2',output))
    def test_floor_boundaries_and_large_multiplication(self):
        self.assertFalse(check_output('CSP_GROUP_PARTITION','2 2 1\n4 11\n','1',b'1 2 4 11'))
        self.assertTrue(check_output('CSP_GROUP_PARTITION','2 2 1\n4 12\n','1',b'1 2 12 4'))
        self.assertTrue(check_output('CSP_GROUP_PARTITION','2 1000000000 1\n999999999999999999 1000000000000000000\n','1',b'1 2 999999999999999999 1000000000000000000'))
    def test_rejects_malformed_and_nonascii(self):
        for output in (b'2 -1 0',b'2 99999999999999999999',b'2 0 0 extra',b'2 0 0 \xff',b'2 0 0 0'):
            self.assertFalse(check_output('CSP_GROUP_COUNT',self.data,'2',output))
    def test_tokens_keep_format_and_unknown_fails_closed(self):
        self.assertTrue(check_output('TOKENS','', '0.500',b' 0.500\n'))
        self.assertFalse(check_output('TOKENS','', '0.500',b'0.5'))
        with self.assertRaises(ValueError):check_output('EXECUTE_SCRIPT','','1',b'1')

class FloatingCheckerTests(unittest.TestCase):
    def test_equivalent_decimal_and_exponent(self):
        for value in (b'1.5',b'1.5000000000',b'+1.5e0',b' 15e-1 \n'):
            self.assertTrue(check_output('FLOAT_ABS_1E_3','','1.500000',value))
    def test_strict_absolute_boundary(self):
        self.assertTrue(check_output('FLOAT_ABS_1E_3','','1',b'1.000999999999'))
        self.assertFalse(check_output('FLOAT_ABS_1E_3','','1',b'1.001'))
        self.assertFalse(check_output('FLOAT_ABS_1E_3','','1',b'0.999'))
        self.assertFalse(check_output('FLOAT_ABS_1E_3','','1000000',b'1000000.01'))
    def test_nonfinite_malformed_and_bounded_output(self):
        for value in (b'nan',b'NaN',b'inf',b'-Infinity',b'1 2',b'',b'1e1000000',b'1'*129,b'1.5\xff',b'1_0',b'1e-1001'):
            self.assertFalse(check_output('FLOAT_ABS_1E_3','','1',value))

class MonteCarloCheckerTests(unittest.TestCase):
    def test_strict_smaller_tolerance_and_equivalent_formats(self):
        for value in (b'1',b'1.0',b'1e0',b'+1.00009999999',b'.99990000001'):
            self.assertTrue(check_output('FLOAT_ABS_1E_4','','1',value))
        for value in (b'1.0001',b'.9999',b'1.0005',b'nan',b'Infinity',b'1 2',b'',b'1e100000',b'1'*129,b'1e-1001'):
            self.assertFalse(check_output('FLOAT_ABS_1E_4','','1',value))
        self.assertTrue(check_output('FLOAT_ABS_1E_3','','1',b'1.0005'))

if __name__=='__main__':unittest.main()

