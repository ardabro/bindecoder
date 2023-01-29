#!/usr/bin/env python3
# _*_ coding,utf-8 _*_
############################################################################################################################################

import argparse
import io
import json
import math
import os
import re
import sys
import time

from typing import Dict,List,Tuple,Union,Any,TextIO,BinaryIO

from . import bindecoder_fields as BF

MIN_PYTHON = (3,7)
assert sys.version_info >= MIN_PYTHON, f"requires Python {'.'.join([str(n) for n in MIN_PYTHON])} or newer"

RESERVED_FORMAT_FILE_KEYS = {"DEFAULTS","TYPEDEFS"}

FILE_OFFSET_WIDTH = 8
INITIAL_INDENT = 2          # how many spaces between file offset column and data
INDENT_STEP = 4             # per level


class InputDataErrorException(ValueError):
    pass


def process_default_values(defaults: dict):
    """
    Parses "default_*" fields from input structure (defined in json file). Configures related field params accordingly.
    """
    if "default_array_separator" in defaults:
        BF.set_default_separator(defaults["default_array_separator"])
    if "default_endian" in defaults:
        BF.set_default_endian(defaults["default_endian"])
    if "default_integer_format" in defaults:
        BF.set_default_integer_format(defaults["default_integer_format"])
    if "default_integer_size" in defaults:
        BF.set_default_integer_size(defaults["default_integer_size"])
    if "default_timestamp_format" in defaults:
        BF.set_default_timestamp_format(defaults["default_timestamp_format"])
    if "default_timezone_offset" in defaults:
        BF.set_default_timezone_offset(defaults["default_timezone_offset"])
    if "default_integral_timestamp_size" in defaults:
        BF.set_default_integral_timestamp_size(defaults["default_integral_timestamp_size"])
    if "default_float_format" in defaults:
        BF.set_default_float_format(defaults["default_float_format"])
    if "default_float_size" in defaults:
        BF.set_default_float_size(defaults["default_float_size"])
    if "default_stop_str_on_zero" in defaults:
        BF.set_default_stop_string_on_zero(defaults["default_stop_str_on_zero"])
    if "default_character_encoding" in defaults:
        BF.set_default_character_encoding(defaults["default_character_encoding"])
    if "default_struct_field_placement" in defaults:
        BF.set_default_structure_fields_placement(defaults["default_struct_field_placement"])


def remove_comments_and_trim(text, comment_delimiter: str = "//"):
    """
    Parses string or list of strings (lines), removes end-of-line comments but leaving ones lying inside strings.
    Removes front and back line whitespaces.
    Removes all empty lines.
    Legal string delimiter: " or '  (triplequoted strings not allowed!)
    params:
    - text: string or list of strings
    - result: string or list of strings accordingly
    """
    if type(text) is str:
        lines=text.splitlines()
    else:
        lines=text

    rx_open=re.compile("(?<!\\\\)(\'|\"|{:s})".format(comment_delimiter))
    rx_single_close=re.compile("(?<!\\\\)\'")
    rx_double_close=re.compile("(?<!\\\\)\"")
    result=list()
    inside_str=False
    what=None

    for line in lines:
        if not inside_str:
            line=line.lstrip()
        start=0
        end=len(line)
        while start<end:
            if not inside_str:
                match=rx_open.search(line,start)                 # match first opening quotation mark or comment delimiter
                if match is None:
                    break
                what=match.group(0)
                if what==comment_delimiter:
                    end=match.start()
                    break
                inside_str=True
                start=match.start()+1
            if what=='"':
                match=rx_double_close.search(line,start)    # find closing quotation mark (double)
            else:
                match=rx_single_close.search(line,start)    # find closing quotation mark (single)
            if match is None:
                break
            inside_str=False
            start=match.start()+1
        line=line[0:end]
        if not inside_str:
            line=line.rstrip()
        if line!="":                        # skip empty/comment only lines
            result.append(line)

    if type(text) is str:
        if len(result)==0:
            return ""
        else:
            return "\n".join(result)
    else:
        return result


def load_json_with_comments(stream, comment_delimiter:str = "//") -> dict:
    data = stream.read()
    bare_json = remove_comments_and_trim(data, comment_delimiter)
    try:
        cfg=json.loads(bare_json)
    except json.decoder.JSONDecodeError as ex:      # adds error context (a copule of lines from document) to the message, and rethrows
        lines = ex.doc.splitlines()
        start_line_idx = max(ex.lineno-10,0)
        line="\nthe context (the error was detected in the last line before separator):\n    "
        context=[]
        for i in range(start_line_idx,ex.lineno):
            context.append(lines[i])
        end_line="\n----------------------------------------"
        ex.args=(ex.args[0]+line+"\n    ".join(context)+end_line),   # tuple; the comma at the end is intended
        raise
    return cfg


class BindecoderCore:

    def process(self, input_stream: BinaryIO, output_stream: TextIO, dataset: BF.StructFieldDef):
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.nesting_level = 0
        self.input_offset = 0
        self.field_label_width = 1
        self.trivial_field_suffix = ""
        self.dump_structure_fields(dataset)

    @staticmethod
    def determine_field_label_width(structure: BF.StructFieldDef) -> int:
        """
        Calculates common field width for all non-structural field types according to the field placement specified for the structure.
        """
        field_label_width = 1   # 1 as field with passed to str.format() is always legal, and has no effect for non-empty strings
        if structure.placement == BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.aligned:
            for f in structure.fields.values():
                if (not f.is_structure()) and ((not f.is_union())) and (f.is_count_trivial_one()):
                    field_label_width = max(len(f.name), field_label_width)
        return field_label_width

    @staticmethod
    def determine_trivial_field_suffix(structure: BF.StructFieldDef) -> str:
        if structure.placement == BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.oneline:
            return ";"
        return ""

    @staticmethod
    def calculate_num_of_digits_for_value(value: int) -> int:
        if value == 1:
            return 1
        return int(math.log(value-1, 10))+1


    def dump_line_header(self):
        """
        Dumps standard line beginning:  <line break> + <offset value> + <indent>.
        """
        self.output_stream.write("\n{:0{}x}{:{}s}"
                                 .format(self.input_offset, FILE_OFFSET_WIDTH, "", INITIAL_INDENT+(self.nesting_level*INDENT_STEP)))


    def dump_structural_field(self, field: BF.StructFieldDef):
        """
        Dumps single or array structural field into output stream.
        Returns the number of bytes fetched from input stream.
        """
        field_count = field.count

        if field_count>1:
            self.output_stream.write("{:s} (count == {:d}):".format(field.name, field_count))
            count_digits = self.calculate_num_of_digits_for_value(field_count)
            self.nesting_level+=1
            for i in range(field_count):
                self.dump_line_header()
                self.output_stream.write("{:s}[{:{}d}]:".format(field.name, i, count_digits))
                self.nesting_level+=1
                self.dump_structure_fields(field)
                self.nesting_level-=1
            self.nesting_level-=1
        else:
            self.output_stream.write("{:s}:".format(field.name))
            self.nesting_level+=1
            self.dump_structure_fields(field)
            self.nesting_level-=1


    def dump_non_structural_field(self, field: BF.NonStructuralTypeFieldDef):
        """
        Dumps single or array non-structural field into output stream.
        Returns the number of bytes fetched from input stream.
        """
        field_size = field.size

        if field.is_count_trivial_one():
            self.output_stream.write("{:{}s} ".format(field.name+":", self.field_label_width+1))
            field.process_data(self.output_stream, self.input_stream)
            self.output_stream.write(self.trivial_field_suffix)
            self.input_offset += field_size
        else:
            field_count = field.count
            self.output_stream.write("{:s} (count == {:d})".format(field.name, field_count))
            if field_count>0:
                self.output_stream.write(":")
                count_digits = self.calculate_num_of_digits_for_value(field_count)
                separator = field.separator
                wrap_at = field.wrap_at
                wrap_counter = 0
                self.nesting_level+=1
                for i in range(field_count):
                    if (wrap_counter%wrap_at) == 0:
                        self.dump_line_header()
                        if field_count>wrap_at:
                            self.output_stream.write("{:s}[{:{}d}]: ".format(field.name, i, count_digits))
                    if (i%wrap_at) != 0:
                        self.output_stream.write(separator)
                    field.process_data(self.output_stream, self.input_stream)
                    self.input_offset += field_size
                    wrap_counter+=1
                self.nesting_level-=1
            elif field_count < 0:
                raise InputDataErrorException("Field \"{:s}\" count is negative: {:d}".format(field_count))



    def update_offset_according_to_variant_total_size(self, field: BF.FieldDef, variant: BF.FieldDef, index: int, start_offset: int):

        if variant.total_size is None:
            return

        remaining = variant.total_size - (self.input_offset - start_offset)
        if remaining >= 0:
            self.input_stream.seek(remaining, io.SEEK_CUR)
            self.input_offset += remaining
            return

        full_name = field.name + "." + variant.name
        if index is not None:
            full_name = "{:s}[{:d}]".format(full_name, index)

        raise InputDataErrorException(
            "Total size ({:d}) specified for field variant {:s} is smaller than the actual number of bytes consumed ({:d})"
            .format(variant.total_size, full_name, self.input_offset - start_offset))

    def dump_union_field(self, field: BF.FieldDef):

        prev_label_width = self.field_label_width
        self.field_label_width = 1                      # no name alignment for union fields

        field_count = field.count       # store locally for optimization, since it may be dynamically calculated

        self.output_stream.write("{:s}".format(field.name))

        if field_count>1:
            self.output_stream.write(" (count == {:d}):".format(field_count))
            count_digits = self.calculate_num_of_digits_for_value(field_count)
            self.nesting_level+=1

            for i in range(field_count):
                start_offset = self.input_offset
                variant = field.choose_variant(self.input_stream)
                self.dump_line_header()
                self.output_stream.write("{:s}[{:{}d}].".format(field.name, i, count_digits))
                if variant.data_offset > 0:
                    self.input_stream.seek(variant.data_offset,1)
                    self.input_offset += variant.data_offset
                self.dump_field(variant)
                self.update_offset_according_to_variant_total_size(field, variant, i, start_offset)
            self.nesting_level-=1
        else:
            start_offset = self.input_offset
            self.output_stream.write(".")           # a separator before variant name
            variant = field.choose_variant(self.input_stream)
            if variant.data_offset > 0:
                self.input_stream.seek(variant.data_offset,1)
                self.input_offset += variant.data_offset
            self.dump_field(variant)
            self.update_offset_according_to_variant_total_size(field, variant, None, start_offset)

        self.field_label_width = prev_label_width   # restore name alignment for enclosing structure


    def dump_field(self, field: BF.FieldDef):

        if field.is_union():
            self.dump_union_field(field)
        elif field.is_structure():
            self.dump_structural_field(field)
        else:
            self.dump_non_structural_field(field)


    def dump_structure_fields(self, structure: BF.StructFieldDef):

        prev_label_width = self.field_label_width
        prev_trivial_field_suffix = self.trivial_field_suffix

        self.field_label_width = self.determine_field_label_width(structure)
        self.trivial_field_suffix = self.determine_trivial_field_suffix(structure)

        need_new_line = True            # we need or does not need a new line before next field depending on a couple of conditions

        for f in structure.fields.values():

            field_count = f.count       # NOTE: this is property that may be calculated by compiled code chunk, so take it once

            if isinstance(f, BF.SkipFieldDef):
                self.input_stream.seek(field_count, io.SEEK_CUR)
                self.dump_line_header()
                self.output_stream.write("-------- skipped {:d} bytes".format(field_count))
                self.input_offset += field_count
                need_new_line = True
                continue

            # if one-line field placement is set then do not start a new line for subsequent field if it is a simple, single value
            if (need_new_line or
                (not f.is_count_trivial_one()) or
                f.is_structure() or
                f.is_union() or
                (structure.placement != BF.StructFieldDef.STRUCT_FIELD_PLACEMENT_ENUM.oneline)):
                self.dump_line_header()
            else:
                self.output_stream.write("  ")                      # in one-line mode only add a horizontal field separator

            need_new_line = (field_count > 1) or f.is_structure() or f.is_union()

            self.dump_field(f)

        self.trivial_field_suffix = prev_trivial_field_suffix
        self.field_label_width = prev_label_width


# This is the contents of standard common configuration file loaded automatically before format specification file provided by client.
# It defines default values and some convenient standard data type aliases.
# Config file may be recreated with this content by starting the program with option --recreate-config


STANDARD_CONFIG = """
{
    "DEFAULTS":
    {
        // for "*_format" specifiers syntax see https://docs.python.org/3/library/string.html#formatspec
        // for timestamp format syntax see https://docs.python.org/3/library/time.html?highlight=strftime#time.strftime
        // for available character encodings see https://docs.python.org/3/library/codecs.html#standard-encodings

        "default_array_separator":" ",
        "default_endian":"system",                      // little, big, system
        "default_integer_format":"0x{:x}",              // for int and uint of any size
        "default_integer_size":4,                       // default size in bytes for int and uint
        "default_timestamp_format":"%Y-%m-%d %H:%M:%S", // default timestamp format
        "default_timezone_offset":3600,                 // timezone offset for time presentation in seconds; null == local timezone;
        "default_integral_timestamp_size":4,            // default size in bytes for integral timestamp (unix time)
        "default_float_format":"{:f}",                  // default floating point number format
        "default_stop_str_on_zero":true,                // present strings up-to 1st zero character by default (skip remaining bytes)
        "default_float_size":4,                         // default size of floating point number; only 4 and 8 values allowed (IEEE-754)
        "default_character_encoding":"ascii",           // default character encoding
        "default_struct_field_placement":"normal"       // normal, aligned, oneline; it specifies how simple (non-structural, no-array)
                                                        //   structure fields are presented;
                                                        //   normal: one per line, "label: value", without any alignment
                                                        //   aligned: one per line but both: labels and values aligned to the same column
                                                        //   oneline: "label1: value1;  label2: value2"... all in the same line
    },

    // Fundamental, predefined data types (see FORMAT_SPEC.md for more comprehensive guide):
    //   int - signed integer
    //   uint - unsigned integer
    //   ts - integral timestamp (unix time); minimum 4 bytes, may be "shifted" i.e. multiplied by unsigned integer factor
    //   fts - floating point timestamp (unix time); the only acceptable size value is 8 (bytes)
    //   char - a string of characters; may have specified length in characters (besides the size in bytes)
    //   struct - a structure consisting of attributes; many containment levels allowed
    //   union - a set of variants; one of them at a time is chosen dynamically with user-defined formula
    //   skip - a special kind of field which orders the processor to simply skip the specified number of bytes;

    "TYPEDEFS":
    {
        // Derived field types defined for convenience:

        "uint8" :{"base":"uint", "size":1, "format":"0x{:02x}"},
        "uint16":{"base":"uint", "size":2, "format":"0x{:04x}"},
        "uint32":{"base":"uint", "size":4, "format":"0x{:08x}"},
        "uint64":{"base":"uint", "size":8, "format":"0x{:016x}"},

        "int8"  :{"base":"int",  "size":1, "format":"{:+4d}"},
        "int16" :{"base":"int",  "size":2, "format":"{:+6d}"},
        "int32" :{"base":"int",  "size":4, "format":"{:+11d}"},
        "int64" :{"base":"int",  "size":8, "format":"{:+20d}"},

        "utc_time32":{"base":"ts", "size":4, "multiplier":1, "tzoffs":0},
        "loc_time32":{"base":"utc_time32", "tzoffs":null},

        "float32":{"base":"float", "size":4, "format":"{:f}"},
        "float64":{"base":"float", "size":8, "format":"{:f}"},

        // A couple of trivial structure definitions for raw data dumps:

        "uint8_dump":
        {
            "fields":
            {
                "data": {"base":"uint8", "count":1000000000000, "wrap_at":32}
            }
        },

        "byte_dump":"uint8_dump",

        "uint16_dump":
        {
            "fields":
            {
                "data": {"base":"uint16", "count":500000000000, "wrap_at":16}
            }
        },

        "word_dump":"uint16_dump",

        "uint32_dump":
        {
            "fields":
            {
                "data": {"base":"uint32", "count":250000000000, "wrap_at":8}
            }
        },

        "dword_dump":"uint32_dump"
    }
}
"""

def range_checker(range_min: int, range_max: int):

    def checker(astr: str):

        nonlocal range_min
        nonlocal range_max

        value = int(astr)
        if range_min <= value <= range_max:
            return value
        else:
            raise argparse.ArgumentTypeError("value not in range [{:d}..{:d}]".format(range_min, range_max))

    return checker


def true_main():
    program_file_name = os.path.basename(__file__)
    program_path = os.path.dirname(os.path.abspath(__file__))
    config_full_path = os.path.join(program_path, os.path.splitext(program_file_name)[0] + ".cfg")

    parser=argparse.ArgumentParser(
                        prog=program_file_name,
                        description="Decodes a binary file according to the format specified in configuration file")

    parser.add_argument("--recreate-config", action="store_true", help="re-create configuration file using standard values")
    parser.add_argument("--skip-config", "-sc", action="store_true",
                        help="skip using config file; default values will be the same as with default config, no typedefs will be created")
    parser.add_argument("--input-offset","-s", type=range_checker(0,max(sys.maxsize,1024*1024*1024*1024)), default=0,
                        help="starting offset in the input file")
    parser.add_argument("--struct","-st", type=str, default=None,
                        help="structure name to start from instead of top-level dataset")
    parser.add_argument("--format","-f", help="json file containing format specification")
    parser.add_argument("input_file", nargs='?', help="binary input file to process")

    args = parser.parse_args()
    cfg_data = None

    if args.recreate_config:
        sys.stderr.write("re-creating config file \"{!s}\"\n".format(config_full_path))
        if os.path.isfile(config_full_path):
            os.rename(config_full_path, config_full_path + time.strftime(".%Y%m%d_%H%M%S"))     # backup original config if exists

        with open(config_full_path,"w") as f:
            f.write(STANDARD_CONFIG)
    elif not args.skip_config:
        sys.stderr.write("loading config file \"{!s}\"\n".format(config_full_path))
        if not os.path.isfile(config_full_path):
            sys.stderr.write("warning: config file \"{!s}\" not found; continuing using defaults\n".format(config_full_path))
        else:
            with open(config_full_path,"r") as f:
                cfg_data = load_json_with_comments(f)

    if cfg_data is None:
        cfg_data = load_json_with_comments(io.StringIO(STANDARD_CONFIG))    # use default config values

    if "DEFAULTS" in cfg_data:
        process_default_values(cfg_data["DEFAULTS"])

    if args.format is not None:
        with open(args.format) as f:
            fmt = load_json_with_comments(f, comment_delimiter = "//")
    else:
        sys.stderr.write("NOTE: no format definition file specified; only predefined structures may be used\n")
        fmt = {}

    if "DEFAULTS" in fmt:
        process_default_values(fmt["DEFAULTS"])

    # NOTE: base types creation and processing type definitions after default values from format file were applied,
    # ensures that all - predefined and user-defined default values are applied to all defined fields;

    BF.create_base_types()

    default_structures = {}
    if not args.skip_config:
        if "TYPEDEFS" in cfg_data:
            BF.create_fields(name="default_typedefs", add_fields_as_top_level_definitions=True,
                             structure_field_defs=cfg_data["TYPEDEFS"], fields=default_structures)

    user_defined_structures = {}
    if "TYPEDEFS" in fmt:
        BF.create_fields(name="user_typedefs", add_fields_as_top_level_definitions=True,
                         structure_field_defs=fmt["TYPEDEFS"], fields=user_defined_structures)

    if args.struct is not None:
        root_struct = user_defined_structures.get(args.struct, default_structures.get(args.struct))
        if root_struct is None:
            raise InputDataErrorException("Selected structure \"{!s}\" definition not found".format(args.struct))
        if not root_struct.is_structure():
            raise InputDataErrorException("Selected data structure \"{!s}\" is actually not a structure (invalid type)".format(args.struct))
    else:
        # structure name not specified, default dataset will be used
        field_defs = {k:v for k,v in fmt.items() if k not in RESERVED_FORMAT_FILE_KEYS}
        if len(field_defs) == 0:
            raise InputDataErrorException("Structure not specified and there is no default dataset in format file")
        selected_fields = {}
        BF.create_fields(name="default_dataset", add_fields_as_top_level_definitions=False,
                         structure_field_defs=field_defs, fields=selected_fields)
        root_struct = BF.StructFieldDef("default_dataset")                              # create dynamic fake root struct default placement
        root_struct.fields = selected_fields

    if args.input_file is None:
        sys.stderr.write("NOTE: No input file, skipping data processing\n")
    else:
        with open(args.input_file,"rb") as f:
            if args.input_offset > 0:
                f.seek(args.input_offset)

            try:
                core = BindecoderCore()
                core.process(input_stream=f, output_stream=sys.stdout, dataset=root_struct)
            except EOFError:
                sys.stdout.write("\nWARNING: Unexpected end of input data.\n")
            else:
                sys.stdout.write("\nSUCCESS\n")


def main():
    try:
        true_main()
    except (InputDataErrorException, BF.FieldDefinitionException, BF.DefaultValueException) as e:
        sys.stderr.write("{}: {}\n".format(type(e), str(e)))
        sys.exit(1)
