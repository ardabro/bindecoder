from . import bindecoder

import copy
import importlib
import io
import re
import sys
import unittest

from typing import Dict,List,Tuple,Union,Any,TextIO,BinaryIO

MIN_PYTHON = (3,7)
assert sys.version_info >= MIN_PYTHON, f"requires Python {'.'.join([str(n) for n in MIN_PYTHON])} or newer"
assert __name__ == "__main__", "This script is intended to be run directly"

class Test(unittest.TestCase):

    # the purpose of these typedef definitions is to define some standard type environment for other tests
    #TODO# add character (string) types
    TEST_TYPEDEFS_STANDARD = """
    {
        "uint8": {"base_type":"uint","size":1,"format":"{:02x}h"},
        "uint16":{"base_type":"uint","size":2,"format":"{:04x}h"},
        "uint32":{"base_type":"uint","size":4,"format":"{:08x}h"},
        "uint64":{"base_type":"uint","size":8,"format":"{:016x}h"},

        "int8": {"base_type":"int","size":1,"format":"{:02x}h"},
        "int16":{"base_type":"int","size":2,"format":"{:04x}h"},
        "int32":{"base_type":"int","size":4,"format":"{:08x}h"},
        "int64":{"base_type":"int","size":8,"format":"{:016x}h"},

        "uint8_be": {"base_type":"uint8", "endian":"big"},
        "uint16_be":{"base_type":"uint16","endian":"big"},
        "uint32_be":{"base_type":"uint32","endian":"big"},
        "uint64_be":{"base_type":"uint64","endian":"big"},

        "int8_be": {"base_type":"int8", "endian":"big"},
        "int16_be":{"base_type":"int16","endian":"big"},
        "int32_be":{"base_type":"int32","endian":"big"},
        "int64_be":{"base_type":"int64","endian":"big"},

        "uint8_le": {"base_type":"uint8", "endian":"little"},
        "uint16_le":{"base_type":"uint16","endian":"little"},
        "uint32_le":{"base_type":"uint32","endian":"little"},
        "uint64_le":{"base_type":"uint64","endian":"little"},

        "int8_le": {"base_type":"int8", "endian":"little"},
        "int16_le":{"base_type":"int16","endian":"little"},
        "int32_le":{"base_type":"int32","endian":"little"},
        "int64_le":{"base_type":"int64","endian":"little"},

        "float32":{"base_type":"float","size":4,"format":"{:8.6f}"},
        "float64":{"base_type":"float","size":8,"format":"{:8.6f}"},

        "float32_be":{"base_type":"float32","endian":"big"},
        "float64_be":{"base_type":"float64","endian":"big"},

        "float32_le":{"base_type":"float32","endian":"little"},
        "float64_le":{"base_type":"float64","endian":"little"},

        "time32":{"base_type":"ts", "size":4, "tzoffs":0,"format":"%Y-%m-%d %H:%M:%S"},
        "time64":{"base_type":"ts", "size":8, "tzoffs":0,"format":"%Y-%m-%d %H:%M:%S"},

        "time32_be":{"base_type":"time32","endian":"big"},
        "time64_be":{"base_type":"time64","endian":"big"},

        "time32_le":{"base_type":"time32","endian":"little"},
        "time64_le":{"base_type":"time64","endian":"little"},

        "ftime":{"base_type":"fts","tzoffs":0,"format":"%Y-%m-%d %H:%M:%S.%f"},
        "ftime_be":{"base_type":"ftime","endian":"big"},
        "ftime_le":{"base_type":"ftime","endian":"little"}
    }
    """


    TEST_DATA_1 = """
    {
        "data":
        [
            {
                "name":"struct_1",
                "fields":
                {
                    "field_1":{},                           // default_type, default_format
                },
                "count":1       // number of structures of this type lying one after another
            }
        ]
    }
    """


    def set_namespace_for_field_expressions(self, namespace: Dict = None):
        bindecoder.FieldDef._FieldDef__namespace = (namespace if (namespace is not None) else {})


    def setUp(self):
        importlib.reload(bindecoder)


    def test_process_default_values(self):

        TEST_DEFAULT_VALUES = """
        {
            "default_endian":"big",                     // little, big, system
            "default_type":"float",
            "default_int_format":"I_{:d}",              // pertains int of any size
            "default_uint_format":"U_0x{:x}",           // pertains int of any size
            "default_float_format":"F_{:f}",
            "default_ts_format":"%x %X",
            "default_fts_format":"%A %x %X",
            "default_timezone_offset":36000,
            "default_stop_str_on_zero":true,            // present strings up-to 1st zero character by default
            "default_char_encoding":"ascii",
            "default_array_separator":"_"
        }
        """

        td = bindecoder.load_json_with_comments(io.StringIO(TEST_DEFAULT_VALUES))

        FD = bindecoder.FUNDAMENTAL_TYPEDEFS

        # corrupt all values that are expected to be set in the test:
        bindecoder.DEFAULT_ENDIAN = None
        bindecoder.DEFAULT_TYPE = None
        bindecoder.DEFAULT_ARRAY_SEPARATOR = None
        FD["int"]["size"] = None
        FD["uint"]["size"] = None
        FD["float"]["size"] = None
        FD["ts"]["size"] = None
        FD["int"]["format"] = None
        FD["uint"]["format"] = None
        FD["float"]["format"] = None
        FD["ts"]["utc"] = None
        FD["char"]["stop_on_zero"] = None
        FD["char"]["encoding"] = None

        bindecoder.process_default_values(td)

        default_endian           = td.pop("default_endian")
        default_type             = td.pop("default_type")
        default_array_separator  = td.pop("default_array_separator")
        default_int_format       = td.pop("default_int_format")
        default_uint_format      = td.pop("default_uint_format")
        default_float_format     = td.pop("default_float_format")
        default_ts_format        = td.pop("default_ts_format")
        default_fts_format       = td.pop("default_fts_format")
        default_timezone_offset  = td.pop("default_timezone_offset")

        default_stop_str_on_zero = td.pop("default_stop_str_on_zero")
        default_char_encoding    = td.pop("default_char_encoding")

        if len(td) != 0:    # there are some remaining definitions not known by the test
            self.fail("Extra default definitions not known by the test: " + str(td))

        self.assertEqual(bindecoder.DEFAULT_ENDIAN, default_endian, "default_endian not set as expected")
        self.assertEqual(bindecoder.DEFAULT_TYPE, default_type, "default_type not set as expected")
        self.assertEqual(bindecoder.DEFAULT_ARRAY_SEPARATOR, default_array_separator, "default_array_separator not set as expected")
        self.assertEqual(FD["int"]["format"] , default_int_format, "default_int_format not set as expected")
        self.assertEqual(FD["uint"]["format"] , default_uint_format, "default_uint_format not set as expected")
        self.assertEqual(FD["float"]["format"] , default_float_format, "default_float_format not set as expected")
        self.assertEqual(FD["ts"]["format"] , default_ts_format, "default_ts_format not set as expected")
        self.assertEqual(FD["fts"]["format"] , default_fts_format, "default_fts_format not set as expected")
        self.assertEqual(FD["ts"]["tzoffs"] , default_timezone_offset, "default_timezone_offset not set in ts as expected")
        self.assertEqual(FD["fts"]["tzoffs"] , default_timezone_offset, "default_timezone_offset not set in fts as expected")
        self.assertEqual(FD["char"]["stop_on_zero"] , default_stop_str_on_zero, "default_stop_str_on_zero not set as expected")
        self.assertEqual(FD["char"]["encoding"] , default_char_encoding, "default_char_encoding not set as expected")

        bindecoder.DEFAULT_ENDIAN = None
        td = {"default_endian":"system"}            # expect to be set to sys.byteorder and all the rest defaults remain unchanged

        bindecoder.process_default_values(td)

        self.assertEqual(bindecoder.DEFAULT_ENDIAN, sys.byteorder, "default_endian not set to sys.byteorder as expected")
        self.assertEqual(bindecoder.DEFAULT_TYPE, default_type, "(retest): default_type not left unchanged")
        self.assertEqual(bindecoder.DEFAULT_ARRAY_SEPARATOR, default_array_separator, "(retest): default_array_separator not left unchanged")
        self.assertEqual(FD["int"]["format"] , default_int_format, "(retest): default_int_format not left unchanged")
        self.assertEqual(FD["uint"]["format"] , default_uint_format, "(retest): default_uint_format not left unchanged")
        self.assertEqual(FD["float"]["format"] , default_float_format, "(retest): default_float_format not left unchanged")
        self.assertEqual(FD["ts"]["format"] , default_ts_format, "(retest): default_ts_format not left unchanged")
        self.assertEqual(FD["fts"]["format"] , default_fts_format, "(retest): default_fts_format not left unchanged")
        self.assertEqual(FD["ts"]["tzoffs"] , default_timezone_offset, "(retest): default_timezone_offset not left unchanged in ts")
        self.assertEqual(FD["fts"]["tzoffs"] , default_timezone_offset, "(retest): default_timezone_offset not left unchanged in fts")
        self.assertEqual(FD["char"]["stop_on_zero"] , default_stop_str_on_zero, "(retest): default_stop_str_on_zero not left unchanged")
        self.assertEqual(FD["char"]["encoding"] , default_char_encoding, "(retest): default_char_encoding not left unchanged")


    def check_type(self, type_name: str, type_def: dict, expected_values: dict):

        for k,v in expected_values.items():
            if k not in type_def:
                self.fail("Parameter \"{!s}\" for type \"{!s}\" not defined.".format(k, type_name))
            d = type_def[k]
            self.assertEqual(d, v, "Invalid parameter \"{!s}\" value ({!s}) for type \"{!s}\".".format(k, d, type_name))


    def test_complete_type_definitions(self):

        TEST_TYPEDEFS = """
        {
            "uint_1":{"base_type":"uint"},
            "uint_2":{"base_type":"uint", "size":2},
            "uint_3":{"base_type":"uint_2", "format":"xxx"},

            "int_1":{"base_type":"int"},
            "int_2":{"base_type":"int", "size":5},
            "int_3":{"base_type":"int_2", "format":"yyy"},

            "float_1":{"base_type":"float"},
            "float_2":{"base_type":"float", "format":"zzz"},
            "float_3":{"base_type":"float_1", "size":4},

            "utc_time":{"base_type":"ts", "size":8, "multiplier":100, "tzoffs":0},
            "loc_time":{"base_type":"utc_time", "tzoffs":null},

            "char_16":{"base_type":"char", "size":2, "stop_on_zero":false, "encoding":"UTF-16LE"},
            "char_32":{"base_type":"char_16", "size":4, "encoding":"UTF-32LE"}
        }
        """

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(TEST_TYPEDEFS))
        orig_typedefs = copy.deepcopy(test_typedefs)

        bindecoder.complete_type_definitions(test_typedefs)

        self.assertEqual(len(test_typedefs), len(orig_typedefs),
                         "The length of typedefs dictionary after processing doesn't match the original")

        self.check_type("uint_1", test_typedefs["uint_1"], {"base_type":"uint", "size":4, "format":"{:d}"})
        self.check_type("uint_2", test_typedefs["uint_2"], {"base_type":"uint", "size":2, "format":"{:d}"})
        self.check_type("uint_3", test_typedefs["uint_3"], {"base_type":"uint", "size":2, "format":"xxx"})

        self.check_type("int_1", test_typedefs["int_1"], {"base_type":"int", "size":4, "format":"0x{:x}"})
        self.check_type("int_2", test_typedefs["int_2"], {"base_type":"int", "size":5, "format":"0x{:x}"})
        self.check_type("int_3", test_typedefs["int_3"], {"base_type":"int", "size":5, "format":"yyy"})

        self.check_type("float_1", test_typedefs["float_1"], {"base_type":"float", "size":8, "format":"{:f}"})
        self.check_type("float_2", test_typedefs["float_2"], {"base_type":"float", "size":8, "format":"zzz"})
        self.check_type("float_3", test_typedefs["float_3"], {"base_type":"float", "size":4, "format":"{:f}"})

        self.check_type("utc_time", test_typedefs["utc_time"],
                                    {"base_type":"ts", "size":8, "multiplier":100, "tzoffs":0})

        self.check_type("loc_time", test_typedefs["loc_time"],
                                    {"base_type":"ts", "size":8, "multiplier":100, "tzoffs":None})

        self.check_type("char_16",  test_typedefs["char_16"],
                                    {"base_type":"char", "size":2, "encoding":"UTF-16LE", "stop_on_zero":False})

        self.check_type("char_32",  test_typedefs["char_32"],
                                    {"base_type":"char", "size":4, "encoding":"UTF-32LE", "stop_on_zero":False})


    def test_create_field_float(self):

        td =    {
                    "default_type"          :"float",
                    "default_float_format"  :"{xxx}"
                }

        bindecoder.process_default_values(td)

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        field = bindecoder.create_field(struct_qualified_name="float_test_struct_1", field_name="float_field_1", field_def={})

        self.assertEqual(field.data_type_name,"float")
        self.assertEqual(field.field_name,"float_field_1")
        self.assertEqual(field.qualified_name,"float_test_struct_1.float_field_1")
        self.assertEqual(field.count,1)

        self.assertEqual(field.size,bindecoder.FUNDAMENTAL_TYPEDEFS["float"]["size"])
        self.assertGreater(field.wrap_at,999999999)         # big number is expected
        self.assertEqual(field.separator,bindecoder.DEFAULT_ARRAY_SEPARATOR)

        self.assertEqual(field.print_format,"{xxx}")
        self.assertEqual(field.endian,bindecoder.DEFAULT_ENDIAN)

        field_def = {"type":"float64", "format":"{yyy}"}
        field = bindecoder.create_field(struct_qualified_name="float_test_struct_2", field_name="float_field_2", field_def=field_def)

        self.assertEqual(field.data_type_name,"float64")
        self.assertEqual(field.field_name,"float_field_2")
        self.assertEqual(field.qualified_name,"float_test_struct_2.float_field_2")
        self.assertEqual(field.count,1)

        self.assertEqual(field.size,8)
        self.assertGreater(field.wrap_at,999999999)         # big number is expected
        self.assertEqual(field.separator,bindecoder.DEFAULT_ARRAY_SEPARATOR)

        self.assertEqual(field.print_format, "{yyy}")
        self.assertEqual(field.endian, bindecoder.DEFAULT_ENDIAN)

        field_def = {"type":"float64_be"}
        field = bindecoder.create_field(struct_qualified_name="float_test_struct_3", field_name="float_field_3", field_def=field_def)
        self.assertEqual(field.endian, "big")

        field_def = {"type":"float64_le"}
        field = bindecoder.create_field(struct_qualified_name="float_test_struct_4", field_name="float_field_4", field_def=field_def)
        self.assertEqual(field.endian, "little")

        td =    {
                    "default_endian"            :"big",
                    "default_array_separator"   :"##"
                }

        bindecoder.process_default_values(td)

        field_def = {"type":"float64", "count":7}
        field = bindecoder.create_field(struct_qualified_name="float_test_struct_5", field_name="float_field_5", field_def=field_def)
        self.assertEqual(field.count, 7)
        self.assertEqual(field.endian, "big")
        self.assertEqual(field.separator, "##")

        td =    {
                    "default_type"          :"int",
                    "default_float_format"  :"{zzz}"
                }

        bindecoder.process_default_values(td)

        field_def = {"type":"float", "count":2}
        field = bindecoder.create_field(struct_qualified_name="float_test_struct_6", field_name="float_field_6", field_def=field_def)
        self.assertEqual(field.data_type_name, "float")
        self.assertEqual(field.size, bindecoder.FUNDAMENTAL_TYPEDEFS["float"]["size"])
        self.assertEqual(field.count, 2)
        self.assertEqual(field.print_format, "{zzz}")


    def test_create_field_int(self):

        td =    {
                    "default_type"        :"int",
                    "default_int_format"  :"{xxx}"
                }

        bindecoder.process_default_values(td)

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        field = bindecoder.create_field(struct_qualified_name="int_test_struct_1", field_name="int_field_1", field_def={})

        self.assertEqual(field.data_type_name,"int")
        self.assertEqual(field.size,bindecoder.FUNDAMENTAL_TYPEDEFS["int"]["size"])
        self.assertEqual(field.print_format,"{xxx}")

        field_def = {"type":"int64", "format":"{yyy}"}
        field = bindecoder.create_field(struct_qualified_name="int_test_struct_2", field_name="int_field_2", field_def=field_def)

        self.assertEqual(field.data_type_name,"int64")
        self.assertEqual(field.size,8)
        self.assertEqual(field.print_format,"{yyy}")

        field_def = {"type":"int16_be"}
        field = bindecoder.create_field(struct_qualified_name="int_test_struct_3", field_name="int_field_3", field_def=field_def)

        self.assertEqual(field.size,2)
        self.assertEqual(field.endian,"big",
                         "Unexpected field definition endian after update (other than {!s})".format("big"))

        field_def = {"type":"int32_le"}
        field = bindecoder.create_field(struct_qualified_name="int_test_struct_4", field_name="int_field_4", field_def=field_def)

        self.assertEqual(field.endian,"little",
                         "Unexpected field definition endian after update (other than {!s})".format("little"))

        td =    {
                    "default_type"        :"uint",
                    "default_int_size"    :4,
                    "default_int_format"  :"{xxx}"
                }

        bindecoder.process_default_values(td)

        field_def = {"type":"int", "count":12}
        field = bindecoder.create_field(struct_qualified_name="int_test_struct_5", field_name="int_field_5", field_def=field_def)

        self.assertEqual(field.data_type_name,"int")
        self.assertEqual(field.size,bindecoder.FUNDAMENTAL_TYPEDEFS["int"]["size"])
        self.assertEqual(field.count,12)
        self.assertEqual(field.print_format,"{xxx}")


    def test_create_field_uint(self):

        td =    {
                    "default_type"        :"uint",
                    "default_uint_format" :"{xxx}"
                }

        bindecoder.process_default_values(td)

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        field = bindecoder.create_field(struct_qualified_name="uint_test_struct_1", field_name="uint_field_1", field_def={})

        self.assertEqual(field.data_type_name,"uint")
        self.assertEqual(field.size,bindecoder.FUNDAMENTAL_TYPEDEFS["uint"]["size"])
        self.assertEqual(field.print_format,"{xxx}")

        field_def = {"type":"int64", "format":"{yyy}"}
        field = bindecoder.create_field(struct_qualified_name="uint_test_struct_2", field_name="uint_field_2", field_def=field_def)

        self.assertEqual(field.data_type_name,"int64")
        self.assertEqual(field.size,8)
        self.assertEqual(field.print_format,"{yyy}")

        field_def = {"type":"int16_be"}
        field = bindecoder.create_field(struct_qualified_name="uint_test_struct_3", field_name="uint_field_3", field_def=field_def)

        self.assertEqual(field.size,2)
        self.assertEqual(field.endian,"big",
                         "Unexpected field definition endian after update (other than {!s})".format("big"))

        field_def = {"type":"int32_le"}
        field = bindecoder.create_field(struct_qualified_name="uint_test_struct_4", field_name="uint_field_4", field_def=field_def)

        self.assertEqual(field.endian,"little",
                         "Unexpected field definition endian after update (other than {!s})".format("little"))

        td =    {
                    "default_type"        :"int",
                    "default_uint_size"   :4,
                    "default_uint_format" :"{xxx}"
                }

        bindecoder.process_default_values(td)

        field_def = {"type":"uint", "count":12}
        field = bindecoder.create_field(struct_qualified_name="uint_test_struct_5", field_name="uint_field_5", field_def=field_def)

        self.assertEqual(field.data_type_name,"uint")
        self.assertEqual(field.size,bindecoder.FUNDAMENTAL_TYPEDEFS["uint"]["size"])
        self.assertEqual(field.count,12)
        self.assertEqual(field.print_format,"{xxx}")


    def test_create_field_char(self):

        # ------------------------------
        td =    {
                    "default_type"              :"char",
                    "default_char_encoding"     :"ascii",
                    "default_stop_str_on_zero"  :False,
                }

        bindecoder.process_default_values(td)

        field = bindecoder.create_field(struct_qualified_name="char_test_struct_1", field_name="char_field_1", field_def={})

        self.assertIsInstance(field,bindecoder.CharacterTypeFieldDef)

        self.assertEqual(field.data_type_name,"char")
        self.assertEqual(field.field_name,"char_field_1")
        self.assertEqual(field.qualified_name,"char_test_struct_1.char_field_1")
        self.assertEqual(field.count,1)

        self.assertEqual(field.size,1)
        self.assertGreater(field.wrap_at,999999999)         # big number is expected
        self.assertEqual(field.separator,bindecoder.DEFAULT_ARRAY_SEPARATOR)

        self.assertEqual(field.stop_on_zero,False)
        self.assertEqual(field.encoding,"ascii")
        self.assertIsNone(field.length)

        # ------------------------------
        field_def = {"size":8, "encoding":"UTF-32BE", "stop_on_zero":True, "length":33}
        field = bindecoder.create_field(struct_qualified_name="char_test_struct_2", field_name="char_field_2", field_def=field_def)

        self.assertEqual(field.stop_on_zero,True)
        self.assertEqual(field.encoding,"UTF-32BE")
        self.assertEqual(field.size,8)
        self.assertEqual(field.length,33)

        # ------------------------------
        td =    {
                    "default_type"              :"int",
                    "default_char_encoding"     :"U16",
                    "default_stop_str_on_zero"  :True
                }

        bindecoder.process_default_values(td)
        self.set_namespace_for_field_expressions({"count_key":11,"length_key":22})

        field_def = {"type":"char", "count":"count_key", "size":128, "length":"length_key"}
        field = bindecoder.create_field(struct_qualified_name="char_test_struct_3", field_name="char_field_3", field_def=field_def)

        self.assertEqual(field.data_type_name,"char")
        self.assertEqual(field.count,11)
        self.assertEqual(field.size,128)
        self.assertEqual(field.length,22)
        self.assertEqual(field.stop_on_zero,True)
        self.assertEqual(field.encoding,"U16")


    def test_create_field_ts(self):

        td =    {
                    "default_type"      :"ts",
                    "default_ts_format" :"{xxx}"
                }

        bindecoder.process_default_values(td)

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_1", field_name="ts_field_1", field_def={})
        self.assertEqual(field.data_type_name,"ts")
        self.assertEqual(field.size,bindecoder.FUNDAMENTAL_TYPEDEFS["ts"]["size"])
        self.assertEqual(field.print_format,"{xxx}")
        self.assertEqual(field.multiplier,1)
        self.assertIsNone(field.tzoffs)

        field_def = {"type":"time32", "format":"{yyy}", "tzoffs":1800, "multiplier":100}
        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_2", field_name="ts_field_2", field_def=field_def)
        self.assertEqual(field.data_type_name,"time32")
        self.assertEqual(field.size,4)
        self.assertEqual(field.print_format,"{yyy}")
        self.assertEqual(field.multiplier,100)
        self.assertEqual(field.tzoffs,1800)

        field_def = {"type":"time64_be"}
        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_3", field_name="ts_field_3", field_def=field_def)
        self.assertEqual(field.endian,"big")
        self.assertEqual(field.size,8)

        field_def = {"type":"time64_le"}
        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_4", field_name="ts_field_4", field_def=field_def)
        self.assertEqual(field.endian,"little")
        self.assertEqual(field.size,8)

        field_def = {"tzoffs":None}
        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_5", field_name="ts_field_5", field_def=field_def)
        self.assertIsNone(field.tzoffs)

        field_def = {"tzoffs":-7200}
        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_6", field_name="ts_field_6", field_def=field_def)
        self.assertEqual(field.tzoffs,-7200)

        field_def = {"tzoffs":0}
        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_7", field_name="ts_field_7", field_def=field_def)
        self.assertEqual(field.tzoffs,0)

        field_def = {"tzoffs":3630}             # invalid offset - not full minutes
        with self.assertRaises(bindecoder.FieldDefinitionException):
            bindecoder.create_field(struct_qualified_name="tss", field_name="tsf", field_def=field_def)

        field_def = {"tzoffs":-3630}            # invalid offset - not full minutes
        with self.assertRaises(bindecoder.FieldDefinitionException):
            bindecoder.create_field(struct_qualified_name="tss", field_name="tsf", field_def=field_def)

        field_def = {"multiplier":None}
        with self.assertRaises(bindecoder.FieldDefinitionException):
            bindecoder.create_field(struct_qualified_name="tss", field_name="tsf", field_def=field_def)

        field_def = {"multiplier":0}
        with self.assertRaises(bindecoder.FieldDefinitionException):
            bindecoder.create_field(struct_qualified_name="tss", field_name="tsf", field_def=field_def)

        field_def = {"multiplier":-1}
        with self.assertRaises(bindecoder.FieldDefinitionException):
            bindecoder.create_field(struct_qualified_name="tss", field_name="tsf", field_def=field_def)

        td =    {
                    "default_type"      :"fts",
                    "default_ts_size"   :4,
                    "default_ts_format" :"{zzz}"
                }

        bindecoder.process_default_values(td)

        field_def = {"type":"ts", "count":2}
        field = bindecoder.create_field(struct_qualified_name="ts_test_struct_8", field_name="ts_field_8", field_def=field_def)
        self.assertEqual(field.data_type_name,"ts")
        self.assertEqual(field.size,4)
        self.assertEqual(field.count,2)
        self.assertEqual(field.print_format,"{zzz}")
        self.assertEqual(field.multiplier,1)
        self.assertEqual(field.tzoffs,None)


    def test_create_field_fts(self):

        td =    {
                    "default_type"          :"fts",
                    "default_fts_format"    :"{xxx}"
                }

        bindecoder.process_default_values(td)

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_1", field_name="fts_field_1", field_def={})
        self.assertEqual(field.data_type_name,"fts")
        self.assertEqual(field.size,8)
        self.assertEqual(field.print_format,"{xxx}")
        self.assertIsNone(field.tzoffs)

        field_def = {"format":"{yyy}", "tzoffs":1800}
        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_2", field_name="fts_field_2", field_def=field_def)
        self.assertEqual(field.data_type_name,"fts")
        self.assertEqual(field.size,8)
        self.assertEqual(field.print_format,"{yyy}")
        self.assertEqual(field.tzoffs,1800)

        field_def = {"type":"ftime_be"}
        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_3", field_name="fts_field_3", field_def=field_def)
        self.assertEqual(field.endian,"big")
        self.assertEqual(field.size,8)

        field_def = {"type":"ftime_le"}
        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_4", field_name="fts_field_4", field_def=field_def)
        self.assertEqual(field.endian,"little")
        self.assertEqual(field.size,8)

        field_def = {"tzoffs":None}
        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_5", field_name="fts_field_5", field_def=field_def)
        self.assertIsNone(field.tzoffs)

        field_def = {"tzoffs":-7200}
        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_6", field_name="fts_field_6", field_def=field_def)
        self.assertEqual(field.tzoffs,-7200)

        field_def = {"tzoffs":0}
        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_7", field_name="fts_field_7", field_def=field_def)
        self.assertEqual(field.tzoffs,0)

        field_def = {"tzoffs":3630}             # invalid offset - not full minutes
        with self.assertRaises(bindecoder.FieldDefinitionException):
            bindecoder.create_field(struct_qualified_name="ftss", field_name="ftsf", field_def=field_def)

        field_def = {"tzoffs":-3630}            # invalid offset - not full minutes
        with self.assertRaises(bindecoder.FieldDefinitionException):
            bindecoder.create_field(struct_qualified_name="ftss", field_name="ftsf", field_def=field_def)

        td =    {
                    "default_type"      :"ts",
                    "default_fts_format" :"{zzz}"
                }

        bindecoder.process_default_values(td)

        field_def = {"type":"fts", "count":2}
        field = bindecoder.create_field(struct_qualified_name="fts_test_struct_8", field_name="fts_field_8", field_def=field_def)
        self.assertEqual(field.data_type_name,"fts")
        self.assertEqual(field.size,8)
        self.assertEqual(field.count,2)
        self.assertEqual(field.print_format,"{zzz}")
        self.assertEqual(field.tzoffs,None)


    def test_create_field_predef_struct(self):

        struct_def =    {
                            "header":
                            {
                                "id":{"type":"uint16"},
                                "num_records":{"type":"uint64"}
                            },
                        }


        td =    {
                    "default_type"          :"header",
                }

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        bindecoder.parse_structures_definitions(struct_def)
        bindecoder.process_default_values(td)

        field1 = bindecoder.create_field(struct_qualified_name="file_1", field_name="header_1", field_def={})
        field2 = bindecoder.create_field(struct_qualified_name="file_1", field_name="header_2", field_def={"count":3})

        self.assertEqual(field1.data_type_name,"header")
        self.assertEqual(field1.field_name,"header_1")
        self.assertEqual(field1.qualified_name,"file_1.header_1")
        self.assertEqual(field1.count,1)
        self.assertEqual(field1.placement, bindecoder.StructFieldDef.DEFAULT_STRUCT_FIELD_PLACEMENT)

        self.assertEqual(field2.data_type_name,"header")
        self.assertEqual(field2.field_name,"header_2")
        self.assertEqual(field2.qualified_name,"file_1.header_2")
        self.assertEqual(field2.count,3)
        self.assertEqual(field2.placement, bindecoder.StructFieldDef.DEFAULT_STRUCT_FIELD_PLACEMENT)

        field_it = field1.field_iterator()
        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint16")
        self.assertEqual(f.field_name,"id")
        self.assertEqual(f.qualified_name,"header.id")
        self.assertEqual(f.size,2)

        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint64")
        self.assertEqual(f.field_name,"num_records")
        self.assertEqual(f.qualified_name,"header.num_records")
        self.assertEqual(f.size,8)

        field_it = field2.field_iterator()
        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint16")
        self.assertEqual(f.field_name,"id")
        self.assertEqual(f.qualified_name,"header.id")
        self.assertEqual(f.size,2)

        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint64")
        self.assertEqual(f.field_name,"num_records")
        self.assertEqual(f.qualified_name,"header.num_records")
        self.assertEqual(f.size,8)


    def test_create_field_immediate_struct(self):

        field_def =     {
                            "type":"struct",
                            "fields":
                            {
                                "id":{"type":"uint16"},
                                "num_records":{"type":"uint64"}
                            }
                        }

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        field1 = bindecoder.create_field(struct_qualified_name="file_1", field_name="header_1", field_def=field_def)
        field_def["count"] = 7
        field_def["placement"] = "aligned"

        field2 = bindecoder.create_field(struct_qualified_name="file_1", field_name="header_2", field_def=field_def)

        self.assertEqual(field1.data_type_name,"struct")
        self.assertEqual(field1.field_name,"header_1")
        self.assertEqual(field1.qualified_name,"file_1.header_1")
        self.assertEqual(field1.count,1)
        self.assertEqual(field1.placement, bindecoder.StructFieldDef.DEFAULT_STRUCT_FIELD_PLACEMENT)

        self.assertEqual(field2.data_type_name,"struct")
        self.assertEqual(field2.field_name,"header_2")
        self.assertEqual(field2.qualified_name,"file_1.header_2")
        self.assertEqual(field2.count,7)
        self.assertEqual(field2.placement, bindecoder.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.aligned)

        field_it = field1.field_iterator()
        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint16")
        self.assertEqual(f.field_name,"id")
        self.assertEqual(f.qualified_name,"file_1.header_1.id")
        self.assertEqual(f.size,2)

        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint64")
        self.assertEqual(f.field_name,"num_records")
        self.assertEqual(f.qualified_name,"file_1.header_1.num_records")
        self.assertEqual(f.size,8)

        field_it = field2.field_iterator()
        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint16")
        self.assertEqual(f.field_name,"id")
        self.assertEqual(f.qualified_name,"file_1.header_2.id")
        self.assertEqual(f.size,2)

        f = next(field_it)
        self.assertEqual(f.data_type_name,"uint64")
        self.assertEqual(f.field_name,"num_records")
        self.assertEqual(f.qualified_name,"file_1.header_2.num_records")
        self.assertEqual(f.size,8)


    def test_create_field_predef_union(self):

        union_def =     {
                            "my_union":
                            {
                                "variant_1":
                                {
                                    "type":"uint8",
                                    "total_size":4,
                                    "trigger":"1"
                                },
                                "variant_2":
                                {
                                    "prefetch_size":1,
                                    "data_offset":3,
                                    "type":"uint16",
                                    "trigger":"2"
                                },
                                "variant_3":
                                {
                                    "prefetch_size":1,
                                    "type":"uint16",
                                    "trigger":"3",
                                    "total_size":5
                                },
                                "variant_4":
                                {
                                    "prefetch_size":2,
                                    "data_offset":2,
                                    "type":"uint64"
                                },
                            },
                        }

        td =    {
                    "default_type"          :"my_union",
                }

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        bindecoder.parse_unions_definitions(union_def)
        bindecoder.process_default_values(td)

        field1 = bindecoder.create_field(struct_qualified_name="file_1", field_name="union_1", field_def={"count":3})

        self.assertEqual(field1.data_type_name, "my_union")
        self.assertEqual(field1.field_name, "union_1")
        self.assertEqual(field1.qualified_name, "file_1.union_1")
        self.assertEqual(field1.count,3)

        self.assertEqual(len(field1.variants),4)

        v = field1.variants[0]
        self.assertEqual(v.prefetch_size,0)
        self.assertEqual(v.total_size,4)
        self.assertEqual(v.data_offset,0)
        self.assertEqual(v.trigger,"1")

        v = field1.variants[1]
        self.assertEqual(v.prefetch_size,1)
        self.assertEqual(v.total_size,None)
        self.assertEqual(v.data_offset,3)
        self.assertEqual(v.trigger,"2")

        v = field1.variants[2]
        self.assertEqual(v.prefetch_size,1)
        self.assertEqual(v.total_size,5)
        self.assertEqual(v.data_offset,0)
        self.assertEqual(v.trigger,"3")

        v = field1.variants[3]
        self.assertEqual(v.prefetch_size,2)
        self.assertEqual(v.total_size,None)
        self.assertEqual(v.data_offset,2)
        self.assertEqual(v.trigger,None)


    def _assertPattern(self, pattern: str, where: str, message: str = None):
        if re.search(pattern,where) is None:
            self.fail("pattern \"{!s}\" not found".format(pattern))


    def test_little_big_endian_interpretation(self):

        BYTEORDER_TEST_DATA = \
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
        ]

        BYTEORDER_TEST_STRUCTURE = """
        {
            "UINT64_LE":  {"type":"uint64_le"},
            "INT64_LE":   {"type":"int64_le"},
            "UINT32_LE":  {"type":"uint32_le"},
            "INT32_LE":   {"type":"int32_le"},
            "UINT16_LE":  {"type":"uint16_le"},
            "INT16_LE":   {"type":"int16_le"},
            "FLOAT32_LE": {"type":"float32_le"},
            "FLOAT64_LE": {"type":"float64_le"},
            "TIME32_LE":  {"type":"time32_le"},
            "FTIME_LE":   {"type":"ftime_le"},

            "UINT64_BE":  {"type":"uint64_be"},
            "INT64_BE":   {"type":"int64_be"},
            "UINT32_BE":  {"type":"uint32_be"},
            "INT32_BE":   {"type":"int32_be"},
            "UINT16_BE":  {"type":"uint16_be"},
            "INT16_BE":   {"type":"int16_be"},
            "FLOAT32_BE": {"type":"float32_be"},
            "FLOAT64_BE": {"type":"float64_be"},
            "TIME32_BE":  {"type":"time32_be"},
            "FTIME_BE":   {"type":"ftime_be"}
        }
        """

        test_typedefs = bindecoder.load_json_with_comments(io.StringIO(self.TEST_TYPEDEFS_STANDARD))
        bindecoder.complete_type_definitions(test_typedefs)
        bindecoder.CUSTOM_TYPEDEFS = test_typedefs

        format_def = {"type":"struct"}
        format_def["fields"] = bindecoder.load_json_with_comments(io.StringIO(BYTEORDER_TEST_STRUCTURE))
        main_struct = bindecoder.create_field("", "DATASET_FRIENDLY_NAME", format_def)

        stream = io.BytesIO(bytes(BYTEORDER_TEST_DATA + [1,2,3,4]))
        output = io.StringIO()
        bindecoder.process_data(stream, output, main_struct)
        s = output.getvalue()

        # Expected output is something along these lines and we will look for each of these lines using regex pattern:
        #
        # 00000000  UINT64_LE: 0807060504030201h
        # 00000008  INT64_LE: -7fffffffffffffffh
        # 00000010  UINT32_LE: 04030201h
        # 00000014  INT32_LE: -7fffffffh
        # 00000018  UINT16_LE: 0201h
        # 0000001a  INT16_LE: -7fffh
        # 0000001c  FLOAT32_LE: 3.141593
        # 00000020  FLOAT64_LE: 3.141593
        # 00000028  TIME32_LE: 2022-10-22 20:36:13
        # 0000002c  FTIME_LE: 2022-10-22 20:36:13.125000
        # 00000034  UINT64_BE: 0807060504030201h
        # 0000003c  INT64_BE: -7fffffffffffffffh
        # 00000044  UINT32_BE: 04030201h
        # 00000048  INT32_BE: -7fffffffh
        # 0000004c  UINT16_BE: 0201h
        # 0000004e  INT16_BE: -7fffh
        # 00000050  FLOAT32_BE: 3.141593
        # 00000054  FLOAT64_BE: 3.141593
        # 0000005c  TIME32_BE: 2022-10-22 20:36:13
        # 00000060  FTIME_BE: 2022-10-22 20:36:13.125000

        self._assertPattern(r"0+\W+UINT64_LE\W+0807060504030201", s)
        self._assertPattern(r"0+8\W+INT64_LE\W+-7fffffffffffffff", s)
        self._assertPattern(r"0+10\W+UINT32_LE\W+04030201", s)
        self._assertPattern(r"0+14\W+INT32_LE\W+-7fffffff", s)
        self._assertPattern(r"0+18\W+UINT16_LE\W+0201", s)
        self._assertPattern(r"0+1a\W+INT16_LE\W+-7fff", s)
        self._assertPattern(r"0+1c\W+FLOAT32_LE\W+3.14159", s)
        self._assertPattern(r"0+20\W+FLOAT64_LE\W+3.14159", s)
        self._assertPattern(r"0+28\W+TIME32_LE\W+2022-10-22 20:36:13", s)
        self._assertPattern(r"0+2c\W+FTIME_LE\W+2022-10-22 20:36:13.125", s)

        self._assertPattern(r"0+34\W+UINT64_BE\W+0807060504030201", s)
        self._assertPattern(r"0+3c\W+INT64_BE\W+-7fffffffffffffff", s)
        self._assertPattern(r"0+44\W+UINT32_BE\W+04030201", s)
        self._assertPattern(r"0+48\W+INT32_BE\W+-7fffffff", s)
        self._assertPattern(r"0+4c\W+UINT16_BE\W+0201", s)
        self._assertPattern(r"0+4e\W+INT16_BE\W+-7fff", s)
        self._assertPattern(r"0+50\W+FLOAT32_BE\W+3.14159", s)
        self._assertPattern(r"0+54\W+FLOAT64_BE\W+3.14159", s)
        self._assertPattern(r"0+5c\W+TIME32_BE\W+2022-10-22 20:36:13", s)
        self._assertPattern(r"0+60\W+FTIME_BE\W+2022-10-22 20:36:13.125", s)

        return True


unittest.main()
