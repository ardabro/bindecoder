#!/usr/bin/env python3
# _*_ coding,utf-8 _*_
############################################################################################################################################

from . import bindecoder_fields as BF

import copy
import importlib
import io
import json
import sys
import unittest

from typing import Dict,List,Tuple,Union,Any,TextIO,BinaryIO

MIN_PYTHON = (3,7)
assert sys.version_info >= MIN_PYTHON, f"requires Python {'.'.join([str(n) for n in MIN_PYTHON])} or newer"
assert __name__ == "__main__", "This script is intended to be run directly"


class Test(unittest.TestCase):

    def setUp(self):
        importlib.reload(BF)


    def _prepare_base_types(self):
        self.ref_signedIntegerField = BF.SignedIntegerFieldDef("int")
        self.ref_unsignedIntegerField = BF.UnsignedIntegerFieldDef("uint")
        self.ref_integerTimestampField = BF.IntegerTimestampFieldDef("ts")
        self.ref_floatTimestampField = BF.FloatTimestampFieldDef("fts")
        self.ref_floatField = BF.FloatFieldDef("float")
        self.ref_characterField = BF.CharacterFieldDef("char")
        self.ref_skipField = BF.SkipFieldDef("skip")
        self.ref_structField = BF.StructFieldDef("struct")
        self.ref_unionField = BF.UnionFieldDef("union")

        self.signedIntegerField = BF.SignedIntegerFieldDef("int")
        self.unsignedIntegerField = BF.UnsignedIntegerFieldDef("uint")
        self.integerTimestampField = BF.IntegerTimestampFieldDef("ts")
        self.floatTimestampField = BF.FloatTimestampFieldDef("fts")
        self.floatField = BF.FloatFieldDef("float")
        self.characterField = BF.CharacterFieldDef("char")
        self.skipField = BF.SkipFieldDef("skip")
        self.structField = BF.StructFieldDef("struct")
        self.unionField = BF.UnionFieldDef("union")

        BF.StructuralFieldDef.add_top_level_field(self.signedIntegerField)
        BF.StructuralFieldDef.add_top_level_field(self.unsignedIntegerField)
        BF.StructuralFieldDef.add_top_level_field(self.integerTimestampField)
        BF.StructuralFieldDef.add_top_level_field(self.floatTimestampField)
        BF.StructuralFieldDef.add_top_level_field(self.floatField)
        BF.StructuralFieldDef.add_top_level_field(self.characterField)
        BF.StructuralFieldDef.add_top_level_field(self.skipField)
        BF.StructuralFieldDef.add_top_level_field(self.structField)
        BF.StructuralFieldDef.add_top_level_field(self.unionField)


    def _test_invalid_param_value(self, base_struct_def: Dict[str,Any], field_name: str, param_name: str, param_invalid_value: Any):
        struct_def = copy.deepcopy(base_struct_def)
        struct_def[field_name][param_name] = param_invalid_value
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="dummy", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})


    def _test_invalid_param_values_FieldDef(self, base_struct_def: Dict[str,Any], field_name: str):
        self._test_invalid_param_value(base_struct_def, field_name, param_name="base", param_invalid_value="foo")
        self._test_invalid_param_value(base_struct_def, field_name, param_name="count", param_invalid_value=None)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="count", param_invalid_value=True)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="count", param_invalid_value=-1)

        # in addition: test reaction for unknown parameter in field definition:
        self._test_invalid_param_value(base_struct_def, field_name, param_name="non_existing_test_param", param_invalid_value=0)


    def _test_invalid_param_values_NonStructuralTypeFieldDef(self, base_struct_def: Dict[str,Any], field_name: str):
        self._test_invalid_param_values_FieldDef(base_struct_def, field_name)

        self._test_invalid_param_value(base_struct_def, field_name, param_name="size", param_invalid_value=0)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="size", param_invalid_value=-1)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="size", param_invalid_value=True)

        self._test_invalid_param_value(base_struct_def, field_name, param_name="separator", param_invalid_value=None)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="separator", param_invalid_value=1)

        self._test_invalid_param_value(base_struct_def, field_name, param_name="wrap_at", param_invalid_value=0)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="wrap_at", param_invalid_value=-1)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="wrap_at", param_invalid_value="a")
        self._test_invalid_param_value(base_struct_def, field_name, param_name="wrap_at", param_invalid_value=True)


    def _test_invalid_param_values_NumericTypeFieldDef(self, base_struct_def: Dict[str,Any], field_name: str):
        self._test_invalid_param_values_NonStructuralTypeFieldDef(base_struct_def, field_name)

        self._test_invalid_param_value(base_struct_def, field_name, param_name="format", param_invalid_value=None)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="format", param_invalid_value=1)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="format", param_invalid_value=False)

        self._test_invalid_param_value(base_struct_def, field_name, param_name="endian", param_invalid_value=None)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="endian", param_invalid_value=1)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="endian", param_invalid_value=False)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="endian", param_invalid_value="huge")
        self._test_invalid_param_value(base_struct_def, field_name, param_name="endian", param_invalid_value="BIG")


    def _test_invalid_param_values_TimestampTypeFieldDef(self, base_struct_def: Dict[str,Any], field_name: str):
        self._test_invalid_param_values_NumericTypeFieldDef(base_struct_def, field_name)

        self._test_invalid_param_value(base_struct_def, field_name, param_name="tzoffs", param_invalid_value=-3650)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="tzoffs", param_invalid_value=3650)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="tzoffs", param_invalid_value=-13*3600)
        self._test_invalid_param_value(base_struct_def, field_name, param_name="tzoffs", param_invalid_value=13*3600)


    def test__invalid_name(self):
        self._prepare_base_types()
        fields = dict()
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={"2xyz":{"base":"int"}}, fields=fields)

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={" ":{"base":"int"}}, fields=fields)

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={" x":{"base":"int"}}, fields=fields)

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={" x":{"base":"int"}}, fields=fields)

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={"struct":{"base":"int"}}, fields=fields)

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={"int":{"base":"int"}}, fields=fields)

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={"TYPEDEFS":{"base":"int"}}, fields=fields)

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="n", add_fields_as_top_level_definitions=True, structure_field_defs={"DEFAULTS":{"base":"int"}}, fields=fields)



    def test__int_field_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"int"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        f = fields["i1"]
        self.assertIsInstance(f, BF.SignedIntegerFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 1)
        self.assertEqual(f.size, BF.SignedIntegerFieldDef.DEFAULT_SIZE)
        self.assertEqual(f.separator, BF.SignedIntegerFieldDef.DEFAULT_SEPARATOR)
        self.assertEqual(f.endian, BF.SignedIntegerFieldDef.DEFAULT_ENDIAN)
        self.assertEqual(f.print_format, BF.SignedIntegerFieldDef.DEFAULT_FORMAT)


    def test__int_field_non_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"int", "count":3, "size":7, "separator":"###", "endian":"big", "format":"{:33x}"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_signedIntegerField, self.signedIntegerField, "base field instance modified!")

        f = fields["i1"]
        self.assertIsInstance(f, BF.SignedIntegerFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 3)
        self.assertEqual(f.size, 7)
        self.assertEqual(f.separator, "###")
        self.assertEqual(f.endian, "big")
        self.assertEqual(f.print_format, "{:33x}")


    def test__int_field_invalid_params(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"int", "count":3, "size":7, "separator":"#", "endian":"big", "format":"{:x}"}
                            }
                            """

        base_struct_def = json.loads(struct_def_json)

        self._test_invalid_param_values_NumericTypeFieldDef(base_struct_def=base_struct_def, field_name="i1")

        # finally, ensure, that base definition is correct (we want to avoid influence on failing cases tested above)
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=base_struct_def, fields={})


    def test__int_field_format(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"int", "size":3, "endian":"little", "format":"{:06x}"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        dest = io.StringIO()
        src = io.BytesIO(b"\x1A\x2B\x3C\x4D")
        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "3c2b1a")

        dest.seek(0)
        dest.truncate()
        src.seek(0)
        src.write(b"\xFE\xFF\xFF\x1A")
        src.seek(0)
        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "-00002")


    def test__unsigned_int_field_invalid_params(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"uint", "count":3, "size":7, "separator":"#", "endian":"big", "format":"{:x}"}
                            }
                            """

        base_struct_def = json.loads(struct_def_json)

        self._test_invalid_param_values_NumericTypeFieldDef(base_struct_def=base_struct_def, field_name="i1")

        # finally, ensure, that base definition is correct (we want to avoid influence on failing cases tested above)
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=base_struct_def, fields={})


    def test__unsigned_int_field_format(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"uint", "size":3, "endian":"little", "format":"{:06x}"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        dest = io.StringIO()
        src = io.BytesIO(b"\x1A\x2B\x3C\x4D")
        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "3c2b1a")

        # ensure it is added to special common namespace for future references, and ensure that this namespace is really common
        self.assertEqual(fields["i1"].namespace["i1"],0x3c2b1a)
        self.assertEqual(BF.FieldDef("xxx").namespace["i1"],0x3c2b1a)

        dest.seek(0)
        dest.truncate()
        src.seek(0)
        src.write(b"\xFF\xFF\xFF\x00")
        src.seek(0)
        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "ffffff")


    def test__integer_timestamp_field_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"ts"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        f = fields["i1"]
        self.assertIsInstance(f, BF.IntegerTimestampFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 1)
        self.assertEqual(f.size, BF.IntegerTimestampFieldDef.DEFAULT_SIZE)
        self.assertEqual(f.separator, BF.IntegerTimestampFieldDef.DEFAULT_SEPARATOR)
        self.assertEqual(f.endian, BF.IntegerTimestampFieldDef.DEFAULT_ENDIAN)
        self.assertEqual(f.print_format, BF.IntegerTimestampFieldDef.DEFAULT_FORMAT)
        self.assertEqual(f.tzoffs, BF.IntegerTimestampFieldDef.DEFAULT_TZOFFS)
        self.assertEqual(f.multiplier, 1)


    def test__integer_timestamp_field_non_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":   {
                                            "base":"ts",
                                            "count":3,
                                            "size":7,
                                            "separator":"###",
                                            "endian":"big",
                                            "format":"***",
                                            "tzoffs":-7200,
                                            "multiplier":333
                                        }
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_integerTimestampField, self.integerTimestampField, "base field instance modified!")

        f = fields["i1"]
        self.assertIsInstance(f, BF.IntegerTimestampFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 3)
        self.assertEqual(f.size, 7)
        self.assertEqual(f.separator, "###")
        self.assertEqual(f.endian, "big")
        self.assertEqual(f.print_format, "***")
        self.assertEqual(f.tzoffs, -7200)
        self.assertEqual(f.multiplier, 333)


    def test__integer_timestamp_invalid_params(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":   {
                                            "base":"ts",
                                            "count":3,
                                            "size":7,
                                            "separator":"#",
                                            "endian":"big",
                                            "format":"*",
                                            "tzoffs":0,
                                            "multiplier":1
                                        }
                            }
                            """

        base_struct_def = json.loads(struct_def_json)
        self._test_invalid_param_values_TimestampTypeFieldDef(base_struct_def=base_struct_def, field_name="i1")

        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=2)
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=3)
        self._test_invalid_param_value(base_struct_def, "i1", "multiplier", param_invalid_value=0)
        self._test_invalid_param_value(base_struct_def, "i1", "multiplier", param_invalid_value=-1)
        self._test_invalid_param_value(base_struct_def, "i1", "multiplier", param_invalid_value=10**12+1)


        # finally, ensure, that base definition is correct (not at the beginning to avoid influence on tested failing cases)
        BF.create_fields(name="dummy", add_fields_as_top_level_definitions=True, structure_field_defs=base_struct_def, fields={})


    def test__integer_timestamp_field_format(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"ts", "size":6, "endian":"little", "multiplier":1000, "format":"%Y-%m-%d %H:%M:%S.%f"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        dest = io.StringIO()
        src = io.BytesIO(b"\x5b\xc2\x2e\xfe\x84\x01")

        # (GMT): 10 December 2022 22:36:28
        # t == 1670711788
        # (t * 1000) == 1670711788000 == 0x184fe2ec1e0          // t in miliseconds
        # t + 123ms == 0x184fe2ec25b -> 5b c2 2e fe 84 01       // 10 December 2022 22:36:28.123 in little endian

        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "2022-12-10 22:36:28.123000")


    def test__float_timestamp_field_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"fts"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        f = fields["i1"]
        self.assertIsInstance(f, BF.FloatTimestampFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 1)
        self.assertEqual(f.size, BF.FloatTimestampFieldDef.DEFAULT_SIZE)
        self.assertEqual(f.separator, BF.FloatTimestampFieldDef.DEFAULT_SEPARATOR)
        self.assertEqual(f.endian, BF.FloatTimestampFieldDef.DEFAULT_ENDIAN)
        self.assertEqual(f.print_format, BF.FloatTimestampFieldDef.DEFAULT_FORMAT)
        self.assertEqual(f.tzoffs, BF.FloatTimestampFieldDef.DEFAULT_TZOFFS)


    def test__float_timestamp_field_non_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":   {
                                            "base":"fts",
                                            "count":3,
                                            "size":8,
                                            "separator":"###",
                                            "endian":"big",
                                            "format":"***",
                                            "tzoffs":-7200
                                        }
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_floatTimestampField, self.floatTimestampField, "base field instance modified!")

        f = fields["i1"]
        self.assertIsInstance(f, BF.FloatTimestampFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 3)
        self.assertEqual(f.size, 8)
        self.assertEqual(f.separator, "###")
        self.assertEqual(f.endian, "big")
        self.assertEqual(f.print_format, "***")
        self.assertEqual(f.tzoffs, -7200)


    def test__float_timestamp_invalid_params(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":   {
                                            "base":"fts",
                                            "count":3,
                                            "size":8,
                                            "separator":"#",
                                            "endian":"big",
                                            "format":"*",
                                            "tzoffs":0
                                        }
                            }
                            """

        base_struct_def = json.loads(struct_def_json)
        self._test_invalid_param_values_TimestampTypeFieldDef(base_struct_def=base_struct_def, field_name="i1")

        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=4)
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=7)
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=9)

        # finally, ensure, that base definition is correct (not at the beginning to avoid influence on tested failing cases)
        BF.create_fields(name="dummy", add_fields_as_top_level_definitions=True, structure_field_defs=base_struct_def, fields={})


    def test__float_timestamp_field_format(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"fts", "size":8, "endian":"little", "format":"%Y-%m-%d %H:%M:%S.%f"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        dest = io.StringIO()
        src = io.BytesIO(b"\x3B\xDF\x07\x7B\x42\xE5\xD8\x41")

        # (GMT): 10 December 2022 22:36:28.123
        # t == 1670711788.123
        # 0x41D8E5427B07DF3B -> 3B DF 07 7B 42 E5 D8 41         // as double float in little endian

        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "2022-12-10 22:36:28.123000")


    def test__float_field_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"float"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        f = fields["i1"]
        self.assertIsInstance(f, BF.FloatFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 1)
        self.assertEqual(f.size, BF.FloatFieldDef.DEFAULT_SIZE)
        self.assertEqual(f.separator, BF.FloatFieldDef.DEFAULT_SEPARATOR)
        self.assertEqual(f.endian, BF.FloatFieldDef.DEFAULT_ENDIAN)
        self.assertEqual(f.print_format, BF.FloatFieldDef.DEFAULT_FORMAT)


    def test__float_field_non_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"float", "count":3, "size":8, "separator":"###", "endian":"big", "format":"$$$"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_floatField, self.floatField, "base field instance modified!")

        f = fields["i1"]
        self.assertIsInstance(f, BF.FloatFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 3)
        self.assertEqual(f.size, 8)
        self.assertEqual(f.separator, "###")
        self.assertEqual(f.endian, "big")
        self.assertEqual(f.print_format, "$$$")


    def test__float_field_invalid_params(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"float", "count":3, "size":8, "separator":"#", "endian":"big", "format":"{:x}"}
                            }
                            """

        base_struct_def = json.loads(struct_def_json)

        self._test_invalid_param_values_NumericTypeFieldDef(base_struct_def=base_struct_def, field_name="i1")

        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=3)
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=5)
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=9)

        # finally, ensure, that base definition is correct (we want to avoid influence on failing cases tested above)
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=base_struct_def, fields={})


    def test__float_field_format(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"float", "size":8, "endian":"little", "format":"{:.3f}"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        dest = io.StringIO()
        src = io.BytesIO(b"\x3B\xDF\x07\x7B\x42\xE5\xD8\x41")
        # 1670711788.123 -> 0x41D8E5427B07DF3B -> 3B DF 07 7B 42 E5 D8 41         // as double float in little endian

        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "1670711788.123")


    def test__char_field_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"char"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        f = fields["i1"]
        self.assertIsInstance(f, BF.CharacterFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 1)
        self.assertEqual(f.size, BF.CharacterFieldDef.DEFAULT_SIZE)
        self.assertEqual(f.separator, BF.CharacterFieldDef.DEFAULT_SEPARATOR)
        self.assertEqual(f.stop_on_zero, BF.CharacterFieldDef.DEFAULT_STOP_ON_ZERO)
        self.assertEqual(f.encoding,     BF.CharacterFieldDef.DEFAULT_ENCODING)
        self.assertEqual(f.length,       None)


    def test__char_field_non_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":   {
                                            "base":"char",
                                            "count":3,
                                            "size":77,
                                            "separator":"###",
                                            "stop_on_zero":true,
                                            "encoding":"UTF-8",
                                            "length":20
                                        }
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_characterField, self.characterField, "base field instance modified!")

        f = fields["i1"]
        self.assertIsInstance(f, BF.CharacterFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 3)
        self.assertEqual(f.size, 77)
        self.assertEqual(f.separator, "###")
        self.assertEqual(f.stop_on_zero, True)
        self.assertEqual(f.encoding, "UTF-8")
        self.assertEqual(f.length, 20)


    def test__char_field_invalid_params(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":   {
                                            "base":"char",
                                            "count":3, "size":7,
                                            "separator":"#",
                                            "stop_on_zero":true,
                                            "encoding":"UTF-8",
                                            "length":20
                                        }
                            }
                            """

        base_struct_def = json.loads(struct_def_json)

        self._test_invalid_param_values_NonStructuralTypeFieldDef(base_struct_def=base_struct_def, field_name="i1")

        self._test_invalid_param_value(base_struct_def, "i1", "stop_on_zero", param_invalid_value=1)
        self._test_invalid_param_value(base_struct_def, "i1", "stop_on_zero", param_invalid_value="abc")
        self._test_invalid_param_value(base_struct_def, "i1", "stop_on_zero", param_invalid_value=None)

        self._test_invalid_param_value(base_struct_def, "i1", "encoding", param_invalid_value="UTF-33")
        self._test_invalid_param_value(base_struct_def, "i1", "encoding", param_invalid_value="")
        self._test_invalid_param_value(base_struct_def, "i1", "encoding", param_invalid_value=True)
        self._test_invalid_param_value(base_struct_def, "i1", "encoding", param_invalid_value=1)
        self._test_invalid_param_value(base_struct_def, "i1", "encoding", param_invalid_value=None)

        self._test_invalid_param_value(base_struct_def, "i1", "length", param_invalid_value=-1)
        self._test_invalid_param_value(base_struct_def, "i1", "length", param_invalid_value="")
        self._test_invalid_param_value(base_struct_def, "i1", "length", param_invalid_value=True)

        # finally, ensure, that base definition is correct (we want to avoid influence on failing cases tested above)
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=base_struct_def, fields={})


    def test__char_field_format(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"char", "size":16, "stop_on_zero":true, "encoding":"ASCII", "length":10}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        dest = io.StringIO()
        src = io.BytesIO(b"0123456789ABCDEF\x00")
        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "\"0123456789\"")

        dest = io.StringIO()
        src = io.BytesIO(b"01234\x0056789ABCDEF")
        fields["i1"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "\"01234\"")

        dest = io.StringIO()
        data = "ĄĘĆ".encode("UTF-32LE")
        src = io.BytesIO(data)

        struct_def["i1"]["size"] = len(data)
        struct_def["i1"]["length"] = 1000
        struct_def["i1"]["stop_on_zero"] = False
        struct_def = {"i2":struct_def["i1"]}            # rename top-level field to avoid name duplication

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        fields["i2"].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "\"\x04\x01\x00\x00\x18\x01\x00\x00\x06\x01\x00\x00\"")


    def test__skip_field_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"skip"}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        f = fields["i1"]
        self.assertIsInstance(f, BF.SkipFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 1)


    def test__skip_field_non_defaults(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"skip", "count":3}
                            }
                            """

        struct_def = json.loads(struct_def_json)
        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_skipField, self.skipField, "base field instance modified!")

        f = fields["i1"]
        self.assertIsInstance(f, BF.SkipFieldDef)
        self.assertEqual(f.name, "i1")
        self.assertEqual(f.count, 3)


    def test__skip_field_invalid_params(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i1":{"base":"skip", "count":5}
                            }
                            """

        base_struct_def = json.loads(struct_def_json)
        self._test_invalid_param_values_FieldDef(base_struct_def=base_struct_def, field_name="i1")

        # size is fixed to the ONE for "skip" and "count" value specifies how many bytes need to be skipped:
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=1)
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=4)
        self._test_invalid_param_value(base_struct_def, "i1", "size", param_invalid_value=8)

        # finally, ensure, that base definition is correct (we want to avoid influence on failing cases tested above)
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=base_struct_def, fields={})


    def test__numeric_process_byterorder_and_format(self):

        BYTEORDER_TEST_DATA = bytes(
        [
            # little endian:
            0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,    # 64bit uint
            0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x80,    # 64bit int == -7FFFFFFFFFFFFFFF
            0x01,0x02,0x03,0x04,                        # 32bit uint
            0x01,0x00,0x00,0x80,                        # 32bit int == -7FFFFFFF
            0x01,0x02,                                  # 16bit uint
            0x01,0x80,                                  # 16bit int == -7FFF
            0xDB,0x0F,0x49,0x40,                        # 32bit float == PI
            0x18,0x2D,0x44,0x54,0xFB,0x21,0x09,0x40,    # 64bit float == PI
            0x3d,0x54,0x54,0x63,                        # 32bit unix time: 2022-10-22 20:36:13 UTC (1666470973)
            0x00,0x00,0x48,0x0F,0x15,0xD5,0xD8,0x41,    # 64bit float unix time: 2022-10-22 20:36:13.125 UTC (1666470973.125)

            # big endian:
            0x08,0x07,0x06,0x05,0x04,0x03,0x02,0x01,    # 64bit uint
            0x80,0x00,0x00,0x00,0x00,0x00,0x00,0x01,    # 64bit int == -7FFFFFFFFFFFFFFF
            0x04,0x03,0x02,0x01,                        # 32bit uint
            0x80,0x00,0x00,0x01,                        # 32bit int == -7FFFFFFF
            0x02,0x01,                                  # 16bit uint
            0x80,0x01,                                  # 16bit int == -7FFF
            0x40,0x49,0x0F,0xDB,                        # 32bit float == PI
            0x40,0x09,0x21,0xFB,0x54,0x44,0x2D,0x18,    # 64bit float == PI
            0x63,0x54,0x54,0x3d,                        # 32bit int unix time: 2022-10-22 20:36:13 UTC     (1666470973)
            0x41,0xD8,0xD5,0x15,0x0F,0x48,0x00,0x00,    # 64bit float unix time: 2022-10-22 20:36:13.125 UTC (1666470973.125)
        ])

        BYTEORDER_TEST_FIELDS = """
                                {
                                    "UINT64_LE":  {"base":"uint",  "endian":"little", "size":8, "format":"{:016x}h"},
                                    "INT64_LE":   {"base":"int",   "endian":"little", "size":8, "format":"{:016x}h"},
                                    "UINT32_LE":  {"base":"uint",  "endian":"little", "size":4, "format":"{:08x}h" },
                                    "INT32_LE":   {"base":"int",   "endian":"little", "size":4, "format":"{:08x}h" },
                                    "UINT16_LE":  {"base":"uint",  "endian":"little", "size":2, "format":"{:04x}h" },
                                    "INT16_LE":   {"base":"int",   "endian":"little", "size":2, "format":"{:04x}h" },
                                    "FLOAT32_LE": {"base":"float", "endian":"little", "size":4, "format":"{:8.6f}" },
                                    "FLOAT64_LE": {"base":"float", "endian":"little", "size":8, "format":"{:8.6f}" },
                                    "TIME32_LE":  {"base":"ts",    "endian":"little", "size":4, "format":"%Y-%m-%d %H:%M:%S"},
                                    "FTIME_LE":   {"base":"fts",   "endian":"little", "size":8, "format":"%Y-%m-%d %H:%M:%S.%f"},

                                    "UINT64_BE":  {"base":"uint",  "endian":"big", "size":8, "format":"{:016x}h"},
                                    "INT64_BE":   {"base":"int",   "endian":"big", "size":8, "format":"{:016x}h"},
                                    "UINT32_BE":  {"base":"uint",  "endian":"big", "size":4, "format":"{:08x}h" },
                                    "INT32_BE":   {"base":"int",   "endian":"big", "size":4, "format":"{:08x}h" },
                                    "UINT16_BE":  {"base":"uint",  "endian":"big", "size":2, "format":"{:04x}h" },
                                    "INT16_BE":   {"base":"int",   "endian":"big", "size":2, "format":"{:04x}h" },
                                    "FLOAT32_BE": {"base":"float", "endian":"big", "size":4, "format":"{:8.6f}" },
                                    "FLOAT64_BE": {"base":"float", "endian":"big", "size":8, "format":"{:8.6f}" },
                                    "TIME32_BE":  {"base":"ts",    "endian":"big", "size":4, "format":"%Y-%m-%d %H:%M:%S"},
                                    "FTIME_BE":   {"base":"fts",   "endian":"big", "size":8, "format":"%Y-%m-%d %H:%M:%S.%f"}
                                }
                                """

        # Expected outputs:
        #
        # UINT64_LE:   0807060504030201h
        # INT64_LE:   -7fffffffffffffffh
        # UINT32_LE:   04030201h
        # INT32_LE:   -7fffffffh
        # UINT16_LE:   0201h
        # INT16_LE:   -7fffh
        # FLOAT32_LE:  3.141593
        # FLOAT64_LE:  3.141593
        # TIME32_LE:   2022-10-22 20:36:13
        # FTIME_LE:    2022-10-22 20:36:13.125000
        # UINT64_BE:   0807060504030201h
        # INT64_BE:   -7fffffffffffffffh
        # UINT32_BE:   04030201h
        # INT32_BE:   -7fffffffh
        # UINT16_BE:   0201h
        # INT16_BE:   -7fffh
        # FLOAT32_BE:  3.141593
        # FLOAT64_BE:  3.141593
        # TIME32_BE:   2022-10-22 20:36:13
        # FTIME_BE:    2022-10-22 20:36:13.125000

        self._prepare_base_types()
        struct_def = json.loads(BYTEORDER_TEST_FIELDS)

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        f=iter(fields)

        src = io.BytesIO(BYTEORDER_TEST_DATA)

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "0807060504030201h", "field: UINT64_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "-7fffffffffffffffh", "field: INT64_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "04030201h", "field: UINT32_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "-7fffffffh", "field: INT32_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "0201h", "field: UINT16_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "-7fffh", "field: INT16_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "3.141593", "field: FLOAT32_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "3.141593", "field: FLOAT64_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "2022-10-22 20:36:13", "field: TIME32_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "2022-10-22 20:36:13.125000", "field: FTIME_LE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "0807060504030201h", "field: UINT64_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "-7fffffffffffffffh", "field: INT64_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "04030201h", "field: UINT32_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "-7fffffffh", "field: INT32_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "0201h", "field: UINT16_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "-7fffh", "field: INT16_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "3.141593", "field: FLOAT32_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "3.141593", "field: FLOAT64_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "2022-10-22 20:36:13", "field: TIME32_BE")

        dest = io.StringIO()
        fields[next(f)].process_data(dest,src)
        self.assertEqual(dest.getvalue(), "2022-10-22 20:36:13.125000", "field: FTIME_BE")


    def test__one_level_structure_success(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "s1":
                                {
                                    "base":"struct",
                                    "fields":
                                    {
                                        "i1":{"base":"int", "size":4, "format":"format_a"},
                                        "i2":{"base":"int", "count":"22", "size":2, "wrap_at":7, "separator":"##"},
                                        "i3":{"base":"i2", "format":"format_b"}
                                    }
                                },

                                "s2":
                                {
                                    "base":"struct"
                                }
                            }
                            """

        struct_def = json.loads(struct_def_json)

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_structField, self.structField, "base field instance modified!")

        self.assertEqual(len(fields),2)
        self.assertTrue("s1" in fields)
        self.assertTrue("s2" in fields)

        s1 = fields["s1"]
        self.assertIsInstance(s1, BF.StructFieldDef)
        self.assertEqual(s1.placement, BF.StructFieldDef.DEFAULT_STRUCT_FIELD_PLACEMENT)

        self.assertEqual(len(s1.fields),3)

        self.assertTrue("i1" in s1.fields)
        i = s1.fields["i1"]
        self.assertIsInstance(i,BF.SignedIntegerFieldDef)
        self.assertEqual(i.count, 1)
        self.assertEqual(i.size, 4)
        self.assertEqual(i.print_format, "format_a")
        self.assertEqual(i.separator, BF.SignedIntegerFieldDef.DEFAULT_SEPARATOR)
        self.assertGreaterEqual(i.wrap_at, 1000)

        self.assertTrue("i2" in s1.fields)
        i = s1.fields["i2"]
        self.assertIsInstance(i,BF.SignedIntegerFieldDef)
        self.assertEqual(i.count, 22)
        self.assertEqual(i.size, 2)
        self.assertEqual(i.print_format, BF.SignedIntegerFieldDef.DEFAULT_FORMAT)
        self.assertEqual(i.separator, "##")
        self.assertEqual(i.wrap_at, 7)

        self.assertTrue("i3" in s1.fields)
        i = s1.fields["i3"]
        self.assertIsInstance(i,BF.SignedIntegerFieldDef)
        self.assertEqual(i.count, 22)
        self.assertEqual(i.size, 2)
        self.assertEqual(i.print_format, "format_b")
        self.assertEqual(i.separator, "##")
        self.assertEqual(i.wrap_at, 7)

        s2 = fields["s2"]
        self.assertIsInstance(s2, BF.StructFieldDef)
        self.assertEqual(s2.placement, BF.StructFieldDef.DEFAULT_STRUCT_FIELD_PLACEMENT)
        self.assertEqual(len(s2.fields),0)


    def test__structure__invalid_and_missing_fields(self):
        self._prepare_base_types()

        struct_def_json =   """{"s0":{"base":"struct", "placement":"normal", "fields":{}}}"""
        struct_def = json.loads(struct_def_json)

        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})
        # the above should pass since the structure is initially correct

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["s0"]["placement"] = "xxx"
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        del struct_def["s0"]["placement"]
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})
        # sholud pass again, placement is optional

        # Now "base" is optional for structures and unions!
        # importlib.reload(BF)
        # self._prepare_base_types()
        # del struct_def["s0"]["base"]
        # with self.assertRaises(BF.FieldDefinitionException):
        #     BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})


    def test__structure_inheritance_success(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "s1":
                                {
                                    "base":"struct",
                                    "placement":"aligned",
                                    "fields":
                                    {
                                        "i1":{"base":"int"},
                                        "i2":{"base":"uint"}
                                    }
                                },

                                "s2":
                                {
                                    "base":"s1",
                                    "fields":
                                    {
                                        "i3":{"base":"ts"},
                                        "i4":{"base":"fts"}
                                    }
                                }
                            }
                            """

        struct_def = json.loads(struct_def_json)

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(len(fields),2)
        self.assertTrue("s1" in fields)
        self.assertTrue("s2" in fields)

        s1 = fields["s1"]
        s2 = fields["s2"]

        self.assertIsInstance(s1, BF.StructFieldDef)
        self.assertIsInstance(s2, BF.StructFieldDef)

        self.assertEqual(s1.placement, BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.aligned)
        self.assertEqual(s2.placement, BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.aligned)

        self.assertEqual(len(s1.fields),2)
        self.assertTrue("i1" in s1.fields)
        self.assertTrue("i2" in s1.fields)

        self.assertEqual(len(s2.fields),4)

        self.assertTrue("i1" in s2.fields)
        self.assertTrue("i2" in s2.fields)
        self.assertTrue("i3" in s2.fields)
        self.assertTrue("i4" in s2.fields)

        self.assertIsInstance(s2.fields["i1"], BF.SignedIntegerFieldDef)
        self.assertIsInstance(s2.fields["i2"], BF.UnsignedIntegerFieldDef)
        self.assertIsInstance(s2.fields["i3"], BF.IntegerTimestampFieldDef)
        self.assertIsInstance(s2.fields["i4"], BF.FloatTimestampFieldDef)


    def test__structure_local_and_top_level_field_inheritance_success(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "base_top_level":{"base":"float", "count":99},
                                "base2":{"base":"float", "count":88},

                                "s1":
                                {
                                    "base":"struct",
                                    "fields":
                                    {
                                        "i1":{"base":"int", "count":"11"},
                                        "i2":{"base":"i1"},
                                        "i3":{"base":"base_top_level"}
                                    }
                                },

                                "s2":
                                {
                                    "base":"struct",
                                    "fields":
                                    {
                                        "i1":{"base":"uint", "count":22},
                                        "i2":{"base":"i1"},
                                        "i3":{"base":"base_top_level"}
                                    }
                                },

                                "s3":
                                {
                                    "base":"struct",
                                    "fields":
                                    {
                                        "derived1":{"base":"base2"},
                                        "base2":{"base":"int", "count":33},
                                        "derived2":{"base":"base2"}
                                    }
                                }
                            }
                            """

        struct_def = json.loads(struct_def_json)

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(len(fields),5)
        self.assertTrue("base_top_level" in fields)
        self.assertTrue("base2" in fields)
        self.assertTrue("s1" in fields)
        self.assertTrue("s2" in fields)
        self.assertTrue("s3" in fields)

        b1 = fields["base_top_level"]
        b2 = fields["base2"]
        s1 = fields["s1"]
        s2 = fields["s2"]
        s3 = fields["s3"]

        self.assertIsInstance(b1, BF.FloatFieldDef)
        self.assertIsInstance(b2, BF.FloatFieldDef)
        self.assertIsInstance(s1, BF.StructFieldDef)
        self.assertIsInstance(s2, BF.StructFieldDef)
        self.assertIsInstance(s3, BF.StructFieldDef)

        self.assertEqual(len(s1.fields),3)
        self.assertTrue("i1" in s1.fields)
        self.assertTrue("i2" in s1.fields)
        self.assertTrue("i3" in s1.fields)

        i1 = s1.fields["i1"]
        i2 = s1.fields["i2"]
        i3 = s1.fields["i3"]

        self.assertIsInstance(i1, BF.SignedIntegerFieldDef)
        self.assertIsInstance(i2, BF.SignedIntegerFieldDef)
        self.assertIsInstance(i3, BF.FloatFieldDef)

        self.assertEqual(i1.count, 11)
        self.assertEqual(i2.count, 11)
        self.assertEqual(i3.count, 99)

        self.assertEqual(len(s2.fields),3)
        self.assertTrue("i1" in s2.fields)
        self.assertTrue("i2" in s2.fields)
        self.assertTrue("i3" in s2.fields)

        i1 = s2.fields["i1"]
        i2 = s2.fields["i2"]
        i3 = s2.fields["i3"]

        self.assertIsInstance(i1, BF.UnsignedIntegerFieldDef)
        self.assertIsInstance(i2, BF.UnsignedIntegerFieldDef)
        self.assertIsInstance(i3, BF.FloatFieldDef)

        self.assertEqual(i1.count, 22)
        self.assertEqual(i2.count, 22)
        self.assertEqual(i3.count, 99)

        self.assertEqual(len(s3.fields),3)
        self.assertTrue("derived1" in s3.fields)
        self.assertTrue("base2" in s3.fields)
        self.assertTrue("derived2" in s3.fields)

        d1 = s3.fields["derived1"]
        b2 = s3.fields["base2"]
        d2 = s3.fields["derived2"]

        self.assertIsInstance(d1, BF.FloatFieldDef)
        self.assertIsInstance(b2, BF.SignedIntegerFieldDef)
        self.assertIsInstance(d2, BF.SignedIntegerFieldDef)

        self.assertEqual(d1.count, 88)
        self.assertEqual(b2.count, 33)
        self.assertEqual(d2.count, 33)


    def test__invalid_inheritance(self):

        struct_def_json =   """
                            {
                                "i0_1":{"base":"float"},

                                "s0":
                                {
                                    "base":"struct",
                                    "fields":
                                    {
                                        "i1_1":{"base":"float"},

                                        "s1":
                                        {
                                            "base":"struct",
                                            "fields":
                                            {
                                                "i2_1":{"base":"float"},
                                                "i2_2":{"base":"i0_1"},
                                                "i2_3":{"base":"float"}
                                            }
                                        }
                                    }
                                },

                                "i0_2":{"base":"float"}
                            }
                            """

        struct_def = json.loads(struct_def_json)

        self._prepare_base_types()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})
        # the above should pass since the structure is initially correct

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["s0"]["fields"]["s1"]["fields"]["i2_2"]["base"] = "i0_2"
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["s0"]["fields"]["s1"]["fields"]["i2_2"]["base"] = "i1_1"
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["s0"]["fields"]["s1"]["fields"]["i2_2"]["base"] = "i2_3"
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["s0"]["fields"]["s1"]["fields"]["i2_2"]["base"] = "i2_1"
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})
        # the above should pass again


    def test_shorthand_defs_success(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "s1":
                                {
                                    "placement":"aligned",
                                    "fields":
                                    {
                                        "i1":"int",
                                        "i2":"uint"
                                    }
                                },

                                "s2":
                                {
                                    "base":"s1",
                                    "fields":
                                    {
                                        "i3":"ts",
                                        "i4":{"base":"fts"}
                                    }
                                },

                                "s3":"s2"
                            }
                            """

        struct_def = json.loads(struct_def_json)

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(len(fields),3)
        self.assertTrue("s1" in fields)
        self.assertTrue("s3" in fields)

        s1 = fields["s1"]
        s3 = fields["s3"]

        self.assertIsInstance(s1, BF.StructFieldDef)
        self.assertIsInstance(s3, BF.StructFieldDef)

        self.assertEqual(s1.placement, BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.aligned)
        self.assertEqual(s3.placement, BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.aligned)

        self.assertEqual(len(s1.fields),2)
        self.assertTrue("i1" in s1.fields)
        self.assertTrue("i2" in s1.fields)

        self.assertEqual(len(s3.fields),4)

        self.assertTrue("i1" in s3.fields)
        self.assertTrue("i2" in s3.fields)
        self.assertTrue("i3" in s3.fields)
        self.assertTrue("i4" in s3.fields)

        self.assertIsInstance(s3.fields["i1"], BF.SignedIntegerFieldDef)
        self.assertIsInstance(s3.fields["i2"], BF.UnsignedIntegerFieldDef)
        self.assertIsInstance(s3.fields["i3"], BF.IntegerTimestampFieldDef)
        self.assertIsInstance(s3.fields["i4"], BF.FloatTimestampFieldDef)



    def test__top_level_field_name_duplication(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "i0_0": {"base":"int"}
                            }
                            """

        struct_def = json.loads(struct_def_json)

        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})


    def test__not_existing_params(self):
        self._prepare_base_types()

        struct_def = {"i0_0": {"base":"int"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i0_1": {"base":"int", "tzoffs":0}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i1_0": {"base":"uint"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i1_1": {"base":"uint", "tzoffs":0}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i2_0": {"base":"float"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i2_1": {"base":"float", "tzoffs":0}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i3_0": {"base":"char"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i3_1": {"base":"char", "endian":"little"}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i4_0": {"base":"ts"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i4_1": {"base":"ts", "length":0}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i5_0": {"base":"fts"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i5_1": {"base":"fts", "multiplier":0}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i6_0": {"base":"struct"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i6_1": {"base":"struct", "endian":"little"}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i7_0": {"base":"union"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i7_1": {"base":"union", "endian":"little"}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i8_0": {"base":"skip"}}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i8_1": {"base":"skip", "endian":"little"}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i9_1": {"base":"struct", "fields":{}, "variants":{}}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        struct_def = {"i9_1": {"base":"union", "fields":{}, "variants":{}}}
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})


    def test__union_simple_definition_success(self):
        struct_def_json = \
            """
            {
                "u0":
                {
                    "base":"union",
                    "variants":
                    {
                        "v0":{"base":"float",                    "total_size":13, "data_offset":0, "trigger":"False"},
                        "v1":{"base":"int",   "prefetch_size":1, "total_size":11, "data_offset":2, "trigger":"RAW[0]==0xFF"},
                        "v2":{"base":"uint",  "prefetch_size":1, "total_size":11, "data_offset":1, "trigger":"RAW[0]==0xFE"},
                        "v3":{"base":"ts",    "prefetch_size":2,                  "data_offset":2}
                    }
                }
            }
            """

        struct_def = json.loads(struct_def_json)

        self._prepare_base_types()

        fields = {}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_unionField, self.unionField, "base field instance modified!")

        self.assertEqual(len(fields),1)
        self.assertTrue("u0" in fields)
        u0 = fields["u0"]
        self.assertIsInstance(u0, BF.UnionFieldDef)

        self.assertEqual(len(u0.variants),4)
        self.assertTrue("v0" in u0.variants)
        self.assertTrue("v1" in u0.variants)
        self.assertTrue("v2" in u0.variants)
        self.assertTrue("v3" in u0.variants)

        v0 = u0.variants["v0"]
        v1 = u0.variants["v1"]
        v2 = u0.variants["v2"]
        v3 = u0.variants["v3"]

        self.assertIsInstance(v0,BF.FloatFieldDef)
        self.assertIsInstance(v1,BF.SignedIntegerFieldDef)
        self.assertIsInstance(v2,BF.UnsignedIntegerFieldDef)
        self.assertIsInstance(v3,BF.IntegerTimestampFieldDef)

        self.assertTrue(hasattr(v0,"total_size"))
        self.assertEqual(v0.total_size, 13)
        self.assertTrue(hasattr(v0,"prefetch_size"))
        self.assertEqual(v0.prefetch_size, 0)
        self.assertTrue(hasattr(v0,"data_offset"))
        self.assertEqual(v0.data_offset, 0)
        # self.assertTrue(hasattr(v0,"trigger"))      # lets consider it a private implementation detail

        self.assertTrue(hasattr(v1,"total_size"))
        self.assertEqual(v1.total_size, 11)
        self.assertTrue(hasattr(v1,"prefetch_size"))
        self.assertEqual(v1.prefetch_size, 1)
        self.assertTrue(hasattr(v1,"data_offset"))
        self.assertEqual(v1.data_offset, 2)
        # self.assertTrue(hasattr(v0,"trigger"))      # lets consider it a private implementation detail

        self.assertTrue(hasattr(v2,"total_size"))
        self.assertEqual(v2.total_size, 11)
        self.assertTrue(hasattr(v2,"prefetch_size"))
        self.assertEqual(v2.prefetch_size, 1)
        self.assertTrue(hasattr(v2,"data_offset"))
        self.assertEqual(v2.data_offset, 1)
        # self.assertTrue(hasattr(v0,"trigger"))      # lets consider it a private implementation detail

        self.assertTrue(hasattr(v2,"total_size"))
        self.assertEqual(v3.total_size, None)
        self.assertTrue(hasattr(v2,"prefetch_size"))
        self.assertEqual(v3.prefetch_size, 2)
        self.assertTrue(hasattr(v2,"data_offset"))
        self.assertEqual(v3.data_offset, 2)
        # self.assertTrue(hasattr(v0,"trigger"))      # lets consider it a private implementation detail


    def test__union_inheritance_success(self):

        struct_def_json = \
            """
            {
                "u0":
                {
                    "base":"union",
                    "variants": {}
                },

                "u1":
                {
                    "base":"u0",
                    "variants":
                    {
                        "v0":{"base":"float",                    "total_size":13, "data_offset":0, "trigger":"False"},
                        "v1":{"base":"int",   "prefetch_size":1, "total_size":11, "data_offset":2, "trigger":"RAW[0]==0xFF"}
                    }
                },

                "u2":
                {
                    "base":"u1",
                    "variants":
                    {
                        "v2":{"base":"uint",  "prefetch_size":1, "total_size":11, "data_offset":1, "trigger":"RAW[0]==0xFE"},
                        "v3":{"base":"ts",    "prefetch_size":2,                  "data_offset":2}
                    }
                }
            }
            """

        struct_def = json.loads(struct_def_json)

        self._prepare_base_types()

        fields = {}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(len(fields),3)
        self.assertTrue("u0" in fields)
        u0 = fields["u0"]
        self.assertIsInstance(u0, BF.UnionFieldDef)
        self.assertTrue("u1" in fields)
        u1 = fields["u1"]
        self.assertIsInstance(u1, BF.UnionFieldDef)
        self.assertTrue("u2" in fields)
        u2 = fields["u2"]
        self.assertIsInstance(u2, BF.UnionFieldDef)

        self.assertEqual(len(u0.variants),0)
        self.assertEqual(len(u1.variants),2)
        self.assertEqual(len(u2.variants),4)
        self.assertTrue("v0" in u2.variants)
        self.assertTrue("v1" in u2.variants)
        self.assertTrue("v2" in u2.variants)
        self.assertTrue("v3" in u2.variants)


    def test__union_incorrect_variant_definitions(self):
        struct_def_json = \
            """
            {
                "u0":
                {
                    "base":"union",
                    "variants":
                    {
                        "v0":{"base":"float", "prefetch_size":1, "trigger":"RAW[0]==0x12"},
                        "v1":{"base":"int",   "prefetch_size":2, "trigger":"RAW[0]==0x34 and RAW[1]==0x56"},
                        "v2":{"base":"uint",  "prefetch_size":3, "trigger":"RAW[0]==0x78 and RAW[1]==0x9a and RAW[2]==0xbc"},
                        "v3":{"base":"ts",    "prefetch_size":4}
                    }
                }
            }
            """

        struct_def = json.loads(struct_def_json)

        self._prepare_base_types()

        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})
        # the above should pass since the structure is initially correct

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["u0"]["variants"]["v2"]["prefetch_size"] = 1     # prefetch size smaller than value for predecessing variant
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["u0"]["variants"]["v2"]["prefetch_size"] = 2
        struct_def["u0"]["variants"]["v2"]["trigger"] = "/+-#%"     # not compilable trigger
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        del struct_def["u0"]["variants"]["v2"]["trigger"]           # no trigger for non-last variant
        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["u0"]["variants"]["v2"]["trigger"] = "True"

        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})
        # should succeeded again when all modification are reverted


    def test__union_cross_inheritance_incorrect_variant_definitions(self):

        struct_def_json = \
            """
            {
                "u0":
                {
                    "base":"union",
                    "variants":
                    {
                        "v0":{"base":"float"}
                    }
                },

                "u1":
                {
                    "base":"u0",
                    "variants":
                    {
                        "v1":{"base":"int", "trigger":"True"}
                    }
                }
            }
            """

        struct_def = json.loads(struct_def_json)
        self._prepare_base_types()

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        struct_def["u0"]["variants"]["v0"]["trigger"] = "True"
        struct_def["u0"]["variants"]["v0"]["prefetch_size"] = 1

        with self.assertRaises(BF.FieldDefinitionException):
            BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})

        importlib.reload(BF)
        self._prepare_base_types()
        del struct_def["u0"]["variants"]["v0"]["prefetch_size"]

        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields={})
        # should pass after definition repair


    def test__union_choose_variant_success(self):
        struct_def_json = \
            """
            {
                "u0":
                {
                    "base":"union",
                    "variants":
                    {
                        "v0":{"base":"float", "prefetch_size":1, "trigger":"RAW[0]==0x12"},
                        "v1":{"base":"int",   "prefetch_size":2, "trigger":"RAW[0]==0x34 and RAW[1]==0x56"},
                        "v2":{"base":"uint",  "prefetch_size":3, "trigger":"RAW[0]==0x78 and RAW[1]==0x9a and RAW[2]==0xbc"},
                        "v3":{"base":"ts",    "prefetch_size":4}
                    }
                }
            }
            """

        struct_def = json.loads(struct_def_json)

        self._prepare_base_types()

        fields = {}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(len(fields),1)
        self.assertTrue("u0" in fields)
        u0 = fields["u0"]
        self.assertIsInstance(u0, BF.UnionFieldDef)

        data = io.BytesIO(b"\xFF\xFF\xFF\xFF")
        f = u0.choose_variant(data)
        self.assertEqual(f.name, "v3")

        data = io.BytesIO(b"\x12")
        f = u0.choose_variant(data)
        self.assertEqual(f.name, "v0")
        data = io.BytesIO(b"\x12")

        data = io.BytesIO(b"\x34\x56\x78\x9a")
        f = u0.choose_variant(data)
        self.assertEqual(f.name, "v1")
        self.assertEqual(data.read(),b"\x34\x56\x78\x9a")

        data = io.BytesIO(b"\x78\x9a\xbc")
        f = u0.choose_variant(data)
        self.assertEqual(f.name, "v2")
        self.assertEqual(data.read(),b"\x78\x9a\xbc")


    def test__union_choose_variant_unknown_variant(self):
        struct_def_json = \
            """
            {
                "u0":
                {
                    "base":"union",
                    "variants":
                    {
                        "v0":{"base":"float", "prefetch_size":1, "trigger":"RAW[0]==0x12"},
                        "v1":{"base":"int",   "prefetch_size":2, "trigger":"RAW[0]==0x34 and RAW[1]==0x56"},
                        "v2":{"base":"uint",  "prefetch_size":3, "trigger":"RAW[0]==0x78 and RAW[1]==0x9a and RAW[2]==0xbc"}
                    }
                }
            }
            """

        struct_def = json.loads(struct_def_json)

        self._prepare_base_types()

        fields = {}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)
        # the above should pass since the structure is initially correct

        self.assertEqual(len(fields),1)
        self.assertTrue("u0" in fields)
        u0 = fields["u0"]
        self.assertIsInstance(u0, BF.UnionFieldDef)

        data = io.BytesIO(b"\x78\x9a\xbc")
        f = u0.choose_variant(data)
        self.assertEqual(f.name, "v2")
        self.assertEqual(data.read(),b"\x78\x9a\xbc")
        # the above is expected to pass

        data = io.BytesIO(b"\xaa\xaa\xaa")
        f = u0.choose_variant(data)
        self.assertIsNone(f,"No variant match, so None is expected")


    def test__default_values(self):

        self.assertEqual(BF.StructFieldDef.DEFAULT_STRUCT_FIELD_PLACEMENT, BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.normal)
        self.assertTrue(BF.FloatFieldDef.DEFAULT_SIZE in {4,8})

        self.assertEqual(BF.SignedIntegerFieldDef.DEFAULT_ENDIAN, sys.byteorder)
        self.assertEqual(BF.UnsignedIntegerFieldDef.DEFAULT_ENDIAN, sys.byteorder)
        self.assertEqual(BF.FloatFieldDef.DEFAULT_ENDIAN, sys.byteorder)
        self.assertEqual(BF.IntegerTimestampFieldDef.DEFAULT_ENDIAN, sys.byteorder)
        self.assertEqual(BF.FloatTimestampFieldDef.DEFAULT_ENDIAN, sys.byteorder)

        self.assertEqual(BF.CharacterFieldDef.DEFAULT_ENCODING, "ascii")

        struct_def_json = \
            """
            {
                "s0":   {"base":"struct", "placement":"aligned"},
                "s1":   {"base":"struct"},
                "i0":   {"base":"int","size":13, "format":"xx1", "endian":"TODO", "separator":"%"},
                "i1":   {"base":"int"},
                "t0":   {"base":"ts", "size":5, "format":"xx2", "tzoffs":3660},
                "t1":   {"base":"ts"},
                "f0":   {"base":"float", "size":"TODO", "format":"xx3"},
                "f1":   {"base":"float"},
                "c0":   {"base":"char", "stop_on_zero":"TODO", "encoding":"big5"},
                "c1":   {"base":"char"}
            }
            """
        struct_def = json.loads(struct_def_json)

        BF.set_default_separator("*")

        if sys.byteorder == "little":
            BF.set_default_endian("big")
            struct_def["i0"]["endian"]="little"
        else:
            BF.set_default_endian("little")
            struct_def["i0"]["endian"]="big"

        BF.set_default_integer_format("yy1")
        BF.set_default_integer_size(7)
        BF.set_default_timestamp_format("yy2")

        BF.set_default_timezone_offset(7320)
        BF.set_default_integral_timestamp_size(6)

        BF.set_default_float_format("yy3")

        if BF.FloatFieldDef.DEFAULT_SIZE == 4:
            BF.set_default_float_size(8)
            struct_def["f0"]["size"]=4
            default_float_size = 8
        else:
            BF.set_default_float_size(4)
            struct_def["f0"]["size"]=8
            default_float_size = 4

        struct_def["c0"]["stop_on_zero"] = BF.CharacterFieldDef.DEFAULT_STOP_ON_ZERO
        BF.set_default_stop_string_on_zero(not BF.CharacterFieldDef.DEFAULT_STOP_ON_ZERO)

        BF.set_default_character_encoding("cp1006")               # URDU - why not?
        BF.set_default_structure_fields_placement("oneline")

        self._prepare_base_types()
        fields = {}
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(fields["s0"].placement, BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.aligned)
        self.assertEqual(fields["s1"].placement, BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.oneline)
        self.assertEqual(fields["i0"].print_format, "xx1")
        self.assertNotEqual(fields["i1"].print_format, "xx1")
        self.assertEqual(fields["i0"].endian, sys.byteorder)
        self.assertEqual(fields["i1"].endian, "big" if (sys.byteorder=="little") else "little")
        self.assertEqual(fields["i0"].separator, "%")
        self.assertEqual(fields["i1"].separator, "*")
        self.assertEqual(fields["t0"].size, 5)
        self.assertEqual(fields["t1"].size, 6)
        self.assertEqual(fields["t0"].print_format, "xx2")
        self.assertNotEqual(fields["t1"].print_format, "xx2")
        self.assertEqual(fields["t0"].tzoffs, 3660)
        self.assertEqual(fields["t1"].tzoffs, 7320)
        self.assertEqual(fields["f0"].size, default_float_size ^ (4+8))
        self.assertEqual(fields["f1"].size, default_float_size)
        self.assertEqual(fields["f0"].print_format, "xx3")
        self.assertNotEqual(fields["f1"].print_format, "xx3")
        self.assertEqual(fields["c0"].stop_on_zero, not BF.CharacterFieldDef.DEFAULT_STOP_ON_ZERO)
        self.assertEqual(fields["c1"].stop_on_zero, BF.CharacterFieldDef.DEFAULT_STOP_ON_ZERO)
        self.assertEqual(fields["c0"].encoding, "big5")
        self.assertEqual(fields["c1"].encoding, "cp1006")


    def test_inheritance_count_and_length_propagation_success(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "ch1":{"base":"char", "count":5, "length":3},
                                "ch2":{"base":"char", "count":51, "length":31},

                                "s1":
                                {
                                    "base":"struct",
                                    "count":7,
                                    "fields":
                                    {
                                        "s1_ch1":{"base":"ch1"},
                                        "s1_ch2":{"base":"ch2"},
                                        "s1_ch3":{"base":"s1_ch2", "count":52, "length":32}
                                    }
                                },

                                "s2":
                                {
                                    "base":"s1",
                                    "count":8
                                }
                            }
                            """

        struct_def = json.loads(struct_def_json)

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_structField, self.structField, "base field instance modified!")

        self.assertEqual(len(fields),4)

        self.assertTrue("ch1" in fields)
        self.assertTrue("ch2" in fields)
        self.assertTrue("s1" in fields)
        self.assertTrue("s2" in fields)

        ch1 = fields["ch1"]
        ch2 = fields["ch2"]

        self.assertIsInstance(ch1, BF.CharacterFieldDef)
        self.assertIsInstance(ch2, BF.CharacterFieldDef)

        self.assertEqual(ch1.count, 5)
        self.assertEqual(ch1.length, 3)

        self.assertEqual(ch2.count, 51)
        self.assertEqual(ch2.length, 31)

        s1 = fields["s1"]
        s2 = fields["s2"]

        self.assertIsInstance(s1, BF.StructFieldDef)
        self.assertIsInstance(s2, BF.StructFieldDef)

        self.assertEqual(s1.count, 7)
        self.assertEqual(s2.count, 8)

        ch1 = s2.fields["s1_ch1"]
        ch2 = s2.fields["s1_ch2"]
        ch3 = s2.fields["s1_ch3"]

        self.assertEqual(ch1.count, 5)
        self.assertEqual(ch1.length, 3)

        self.assertEqual(ch2.count, 51)
        self.assertEqual(ch2.length, 31)

        self.assertEqual(ch3.count, 52)
        self.assertEqual(ch3.length, 32)


    def test_struct_union_default_base_success(self):
        self._prepare_base_types()

        struct_def_json =   """
                            {
                                "s1":
                                {
                                    "fields":
                                    {
                                        "f1":{"base":"int"}
                                    }
                                },

                                "u1":
                                {
                                    "variants":
                                    {
                                        "v0":{"base":"int",   "trigger":"False"},
                                        "v1":{"base":"int"}
                                    }
                                }
                            }
                            """

        struct_def = json.loads(struct_def_json)

        fields = dict()
        BF.create_fields(name="main", add_fields_as_top_level_definitions=True, structure_field_defs=struct_def, fields=fields)

        self.assertEqual(self.ref_structField, self.structField, "base field instance modified!")
        self.assertEqual(self.ref_unionField, self.unionField, "base field instance modified!")

        self.assertEqual(len(fields),2)

        self.assertTrue("s1" in fields)
        self.assertTrue("u1" in fields)

        s1 = fields["s1"]
        u1 = fields["u1"]

        self.assertIsInstance(s1, BF.StructFieldDef)
        self.assertIsInstance(u1, BF.UnionFieldDef)


unittest.main()
