#!/usr/bin/env python3
# _*_ coding,utf-8 _*_
############################################################################################################################################

import abc
import copy
import datetime
import enum
import re
import struct
import sys

from typing import Dict,List,Tuple,Union,Any,TextIO,BinaryIO


class FieldDefinitionException(ValueError):
    pass


class DefaultValueException(ValueError):
    pass


def raise_field_def_exception(struct_name: str, field_name: str, info: str):
    raise FieldDefinitionException("structure: \"{!s}\", field: \"{!s}\": ".format(struct_name,field_name) + info)

class FieldDef: pass    # predefinition to suppress complaints about undefined symbol


class FieldDef:
    _LEGAL_NAME_REGEX = re.compile(r"[A-Za-z_]\w*")
    _FORBIDDEN_NAMES = {"struct","char","float","fts","int","skip","struct","ts","uint","union","DEFAULTS","TYPEDEFS"}
    _MAX_COUNT = 1024*1024*1024*1024    # == 1TB
    _CONFIG_KEYS = {"base","count"}     # allowed clone construction parameters list (**kwargs argument for clone())
                                        # each subclass may add own keys

    __namespace = {}        # dynamically updated container with some values (unsigned integers for now) decoded from input stream that
                            # may be used during data processing to determine some key values as count or length of some other fields
                            # NOTE: this is 100% common class attribute, not meant to be replaced locally by any instance

    namespace = property(lambda self: self.__namespace)     # make namespace a read-only attribute

    def __init__(self, name: str):
        self.name = name            # don't verify the name; __init__() is used internally, with hardcoded names only
        self._count = 1

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        self_vars = vars(self)
        other_vars = vars(other)
        if set(self_vars.keys()) != set(other_vars.keys()):
            return False
        for k,v in self_vars.items():
            if other_vars[k] != v:
                return False
        return True

    def is_structure(self):
        return isinstance(self, StructFieldDef)

    def is_union(self):
        return isinstance(self, UnionFieldDef)

    def is_count_trivial_one(self):
        """Returns information whether it is just single field with count=1 given explicitly and not calculated dynamically."""
        return  (isinstance(self._count, int)) and (self._count == 1)

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        """
        name:                   the name of the structure owning given fields list (necessary only for error reporting)
        parent_name:            the name of the parent of this structure (necessary only for error reporting)
        field_def:              field definition dictionary created from JSON stored in input format file.
        """
        if not isinstance(name,str):
            raise_field_def_exception(parent_name, name, "field name must be a string; got: \"{!s}\"".format(name))

        if name in self._FORBIDDEN_NAMES:
            raise_field_def_exception(parent_name, name, "Reserved word \"{!s}\" used as field name".format(name))

        if not self._LEGAL_NAME_REGEX.match(name):
            msg = "Field name does not match required pattern: \"{!s}\"".format(self._LEGAL_NAME_REGEX.pattern)
            raise_field_def_exception(parent_name, name, msg)

        redundant_keys = field_def.keys() - self._CONFIG_KEYS
        if len(redundant_keys) > 0:
            raise_field_def_exception(parent_name, name, "Unknown, redundant configuration keys: {!s}".format(redundant_keys))

        count = self._count
        if "count" in field_def:
            count = field_def["count"]
            if isinstance(count,int) and (not isinstance(count,bool)):       # turned out that bool is also an int!
                if (count<0) or (count>self._MAX_COUNT):
                    msg = "Negative or too large count parameter: {:d}. The maximum value is: {:d}".format(count,self._MAX_COUNT)
                    raise_field_def_exception(parent_name, name, msg)
            elif isinstance(count,str):
                count_spec = count
                try:
                    count = compile(count_spec, filename=name, mode="eval")
                except:
                    raise_field_def_exception(parent_name, name, "Cannot compile \"count\" expression: \"{:s}\"".format(count_spec))
            else:
                msg = "Invalid type of count parameter. Only unsigned int or str are allowed; got: \"{!s}\"".format(count)
                raise_field_def_exception(parent_name, name, msg)

        result = copy.copy(self)
        result.name = name
        result._count = count
        return result

    def count_getter(self):
        if isinstance(self._count,int):
            return self._count
        else:
            return eval(self._count,{},self.__namespace)

    count = property(count_getter)


class NonStructuralTypeFieldDef(FieldDef, abc.ABC):
    """
    Not structure, not an union, but it may be an array.
    """
    DEFAULT_SEPARATOR = " "         # horizontal separator between array fields

    _CONFIG_KEYS = {"wrap_at","separator","size"} | FieldDef._CONFIG_KEYS

    def __init__(self, name: str):
        super().__init__(name)
        self.size = None                                # no default, needs to be set by subclass
        self.separator = self.DEFAULT_SEPARATOR
        self.wrap_at = 0x80000000


    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        r = super().clone(name, parent_name, field_def)

        if "wrap_at" in field_def:
            wrap_at = field_def["wrap_at"]
            if (not isinstance(wrap_at,int)) or isinstance(wrap_at,bool) or (wrap_at<1):
                raise_field_def_exception(parent_name, name, "\"wrap_at\" parameter is not a positive integer: \"{!s}\"".format(wrap_at))
            r.wrap_at = wrap_at
        if "separator" in field_def:
            separator = field_def["separator"]
            if not isinstance(separator,str):
                raise_field_def_exception(parent_name, name, "illegal, non-string \"separator\" parameter: \"{!s}\"".format(separator))
            r.separator = separator
        if "size" in field_def:
            size = field_def["size"]
            if (not isinstance(size,int)) or isinstance(size,bool) or (size<1):
                raise_field_def_exception(parent_name, name, "size parameter is not a positive integer: \"{!s}\"".format(size))
            r.size = size
        elif r.size is None:
            raise_field_def_exception(parent_name, name, "not specified an obligatory \"size\" parameter")
        return r

    @abc.abstractmethod
    def format_data(self, dest_stream: TextIO, raw_data: bytes):
        pass

    def process_data(self, dest_stream: TextIO, input_stream: BinaryIO):
        raw_data = input_stream.read(self.size)
        if len(raw_data)<self.size:                         # the end of the data in the stream
            raise EOFError("unexpected end of data file")
        self.format_data(dest_stream, raw_data)


class NumericTypeFieldDef(NonStructuralTypeFieldDef):
    """
    Number-based field definition (float,integer,timestamp): non-structural, non-union (but it may be an array).
    """
    DEFAULT_ENDIAN = sys.byteorder

    _CONFIG_KEYS = {"format","endian"} | NonStructuralTypeFieldDef._CONFIG_KEYS

    def __init__(self, name: str):
        super().__init__(name)
        self.print_format = None                # python format string or python date/time formatter depending on data type
        self.endian = self.DEFAULT_ENDIAN       # byteorder ("little" or "big")

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        r = super().clone(name, parent_name, field_def)

        if "format" in field_def:
            print_format = field_def["format"]
            if not isinstance(print_format,str):
                raise_field_def_exception(parent_name, name, "invalid (non-string) \"format\" parameter: \"{!s}\"".format(print_format))
            r.print_format = print_format
        elif r.print_format is None:
            raise_field_def_exception(parent_name, name, "not specified an obligatory \"format\" parameter")

        if "endian" in field_def:
            endian = field_def["endian"]
            if endian == "system":
                endian = sys.byteorder
            elif endian not in {"little","big"}:
                raise_field_def_exception(parent_name, name, "invalid endian (byte order) specifier: \"{!s}\"".format(endian))
            r.endian = endian

        return r


class IntegerTypeFieldDef(NumericTypeFieldDef):

    DEFAULT_FORMAT = "{:d}"
    DEFAULT_SIZE = 4

    def __init__(self, name: str):
        super().__init__(name)
        self.print_format = self.DEFAULT_FORMAT
        self.size = self.DEFAULT_SIZE

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        return super().clone(name, parent_name, field_def)


def is_tzoffs_valid(v: int):
    return not ((v is not None) and (not isinstance(v,int) or (v<-3600*12) or (v>3600*12) or (v%60!=0)))


class TimestampTypeFieldDef(NumericTypeFieldDef):
    """
    Base class for unix timestamps represented by integer value or floating point.
    """
    DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_SIZE = None         # needs to be re-set in derived classes
    DEFAULT_TZOFFS = 0          # time zone offset in seconds;  None is also acceptable and means current local time zone

    _CONFIG_KEYS = {"tzoffs"} | NumericTypeFieldDef._CONFIG_KEYS

    def __init__(self, name):
        super().__init__(name)
        self.tzoffs = self.DEFAULT_TZOFFS
        self.print_format = self.DEFAULT_FORMAT
        self.size = self.DEFAULT_SIZE

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        r = super().clone(name, parent_name, field_def)

        if "tzoffs" in field_def:
            tzoffs = field_def["tzoffs"]
            if not is_tzoffs_valid(tzoffs):
                raise_field_def_exception(parent_name, name, "invalid value of \"tzoffs\" parameter: \"{!s}\"".format(tzoffs))
            r.tzoffs = tzoffs

        if r.size < 4:
            raise_field_def_exception(parent_name, name,
                "invalid value of \"size\" parameter: {!s}; at least 4 bytes required for unix timestamp".format(r.size))

        return r

    def format_unix_time(self, dest_stream: TextIO, seconds: float):
        dt = datetime.datetime.fromtimestamp(seconds).astimezone()      # local timestamp with tzinfo properly set to local timezone
        if self.tzoffs is not None:
            dt = dt.astimezone(datetime.timezone(datetime.timedelta(seconds=self.tzoffs)))          # move to specified time zone
        dest_stream.write(dt.strftime(self.print_format))

# ============================================================================================
# Concrete (non-abstract) field classes:

class SignedIntegerFieldDef(IntegerTypeFieldDef):

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        value = int.from_bytes(raw_bytes, byteorder=self.endian, signed=True)
        dest_stream.write(self.print_format.format(value))


class UnsignedIntegerFieldDef(IntegerTypeFieldDef):

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        value = int.from_bytes(raw_bytes, byteorder=self.endian, signed=False)
        self.namespace[self.name] = value               # put all unsigned integer values into common namespace allowing future references
        dest_stream.write(self.print_format.format(value))


class IntegerTimestampFieldDef(TimestampTypeFieldDef):
    """
    UNIX timestamp, optionally multiplied, represented by an integral value.
    """
    DEFAULT_SIZE = 4
    _CONFIG_KEYS = {"multiplier"} | TimestampTypeFieldDef._CONFIG_KEYS

    def __init__(self, name):
        super().__init__(name)
        self.multiplier = 1

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        r = super().clone(name, parent_name, field_def)

        if "multiplier" in field_def:
            m = field_def["multiplier"]
            if (not isinstance(m,int)) or (m < 1) or (m > 10**12):
                raise_field_def_exception(parent_name, name,
                    "invalid value of \"multiplier\" parameter; required an integer in range [1..10^12]; got: \"{!s}\"".format(m))
            r.multiplier = m

        return r

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        value = int.from_bytes(raw_bytes, byteorder=self.endian, signed=False)
        self.format_unix_time(dest_stream, value/self.multiplier)


class FloatTimestampFieldDef(TimestampTypeFieldDef):
    """
    UNIX timestamp, optionally multiplied, represented by a double float (8 bytes) value.
    """
    DEFAULT_SIZE = 8    # NOTE: fixed value; only IEEE-754 double may be used

    def __init__(self, name):
        super().__init__(name)

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        r = super().clone(name, parent_name, field_def)

        if r.size != 8:
            raise_field_def_exception(parent_name, name,
                "invalid value of \"size\" parameter: {!s}; exactly 8 bytes required for float unix timestamp".format(r.size))

        return r

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        spec = ">d" if (self.endian == "big") else "<d"
        seconds = struct.unpack(spec, raw_bytes)[0]
        self.format_unix_time(dest_stream, seconds)


class FloatFieldDef(NumericTypeFieldDef):
    """
    IEEE-754 single or double
    """
    DEFAULT_FORMAT = "{:f}"
    DEFAULT_SIZE = 4

    def __init__(self, name):
        super().__init__(name)
        self.size = self.DEFAULT_SIZE
        self.print_format = self.DEFAULT_FORMAT

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        r = super().clone(name, parent_name, field_def)

        if r.size not in {4,8}:
            raise_field_def_exception(parent_name, name,
                "invalid value of \"size\" parameter: {!s}; only 4 and 8 values allowed for IEEE-754 float".format(r.size))

        return r

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        flag = "d" if (len(raw_bytes)==8) else "f"
        spec = (">"+flag) if (self.endian == "big") else ("<"+flag)
        value = struct.unpack(spec,raw_bytes)[0]
        dest_stream.write(self.print_format.format(value))


class CharacterFieldDef(NonStructuralTypeFieldDef):
    """
    Character (string) field definition.
    A note about size, length, stop_on_zero and count for character fields:
    - size means size in bytes of the whole field
    - length is the string length in characters; may be unspecified;
    - stop_on_zero tells whether to stop printing string when 1st \0 character is met;
      if both: stop_on_zero and length are set then the first of them that triggers before the size is reached ends the string;
    - count means - like for other field types - a number of repetitions of the whole field (size bytes)
    """
    DEFAULT_SIZE = 1
    DEFAULT_STOP_ON_ZERO = False    # whether to stop printing when \0 is met
    DEFAULT_ENCODING = "ascii"      # one of the python encoding specifiers like:
                                    # - various code pages: cpXXX,cpXXX;
                                    # - UTF-32 forms: U32==utf32 - with BOM;  UTF-32BE, UTF-32LE - no BOM
                                    # - UTF-16 forms: U16==utf16 - with BOM;  UTF-16BE, UTF-16LE - no BOM
                                    # - UTF-8: U8==utf8==UTF - no BOM
                                    # the full list: https://docs.python.org/3/library/codecs.html#standard-encodings

    _CONFIG_KEYS = {"encoding", "length", "stop_on_zero"} | NonStructuralTypeFieldDef._CONFIG_KEYS

    _length = None          # None or int or compiled code; if string is provided in format json, then it is compiled to code that
                            # is supposed to evaluate to an unsigned integer specifying actual string length

    @classmethod
    def is_encoding_name_valid(self, s: str):
        try:
            "ABC".encode(s)
        except:
            return False
        return True

    def __init__(self, name):
        super().__init__(name)
        self.size = self.DEFAULT_SIZE
        self.stop_on_zero = self.DEFAULT_STOP_ON_ZERO
        self.encoding = self.DEFAULT_ENCODING
        self._length = None         # None or int or compiled code; if string is provided in format json, then it is compiled to code that
                                    # is supposed to evaluate to an unsigned integer specifying actual string length in characters

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        r = super().clone(name, parent_name, field_def)

        if "stop_on_zero" in field_def:
            stop_on_zero = field_def["stop_on_zero"]
            if (not isinstance(stop_on_zero,bool)):
                raise_field_def_exception(parent_name, name, "stop_on_zero parameter is not a boolean: \"{!s}\"".format(stop_on_zero))
            r.stop_on_zero = stop_on_zero

        if "encoding" in field_def:
            encoding = field_def["encoding"]
            if not self.is_encoding_name_valid(encoding):
                raise_field_def_exception(parent_name, name, "invalid encoding specifier: \"{!s}\"".format(encoding))
            r.encoding = encoding

        if "length" in field_def:
            length = field_def["length"]
            if isinstance(length, int) and not isinstance(length, bool):
                if length<0:                                       # note: we allow zero-length strings
                    raise_field_def_exception(parent_name, name, "length ({:d}) less than zero".format(length))
            elif isinstance(length, str):
                specified_length = length
                try:
                    length = compile(specified_length, filename=self.qualified_name, mode="eval")
                except:
                    raise_field_def_exception(parent_name, name,
                                              "cannot compile \"length\" calculating expression: \"{!s}\"".format(specified_length))
            else:
                msg = "Invalid type of length parameter. Only unsigned int or str are allowed; got: \"{!s}\"".format(length)
                raise_field_def_exception(parent_name, name, msg)
            r._length = length
        return r

    def length_getter(self):
        if (self._length is None) or isinstance(self._length,int):
            return self._length
        else:
            return eval(self._length,{},self.namespace)

    length = property(length_getter)

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        end = len(raw_bytes)
        if self.stop_on_zero and (0 in raw_bytes):
            end = raw_bytes.index(0)

        decoded_str = raw_bytes[0:end].decode(self.encoding, errors='backslashreplace')

        if self.length is not None:
            if self.length < len(decoded_str):
                decoded_str = decoded_str[:self.length]

        dest_stream.write("\"{}\"".format(decoded_str))


class SkipFieldDef(FieldDef):
    """
    Special field definition for data that is to be skipped in processing (not presented at all).
    The count value is the exact number of bytes to skip.
    """

    def __init__(self, name):
        super().__init__(name)

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]) -> FieldDef:
        return super().clone(name, parent_name, field_def)

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        pass


class StructuralFieldDef(FieldDef):
    """
    A type containing embedded members. Known specializations: StructFileldDef and UnionFieldDef.
    Have an access to a common dictionary of predefined field definitions that may be used as bases for new ones.
    """

    _CONFIG_KEYS = set() | FieldDef._CONFIG_KEYS

    top_level_fields = dict()       # a common dictionary containing top-level field definitions; initially it should be filled with
                                    # fundamental definitions used only as base typedefs for user field definitions

    @classmethod
    def add_top_level_field(self, field: FieldDef):
        if field.name in self.top_level_fields:
            raise_field_def_exception(None, field.name, "top level field name duplication")
        self.top_level_fields[field.name] = field

    @classmethod
    def _create_field(self, field_name: str, parent_name: str, field_def: dict[str,Any],
                            local_base_fields: Dict[str,FieldDef] = None) -> FieldDef:
        """
        Creates a new field instance of appropriate class, derived from FieldDef. Does not add it anywhere.
        Local_base_fields is an optional set of fields that may be used as base for newly-created one and (if not null) they are searched
        in first place. If base isn't found in among these locals, then base field is taken from top_level_fields.
        """
        if "base" not in field_def:
            raise_field_def_exception(parent_name, field_name, "base field not specified (missing \"base\" key)")
        base_name = field_def["base"]
        if (not isinstance(base_name, str)) or (len(base_name.strip())==0):
            msg = "base field name must be non-empty, non-blank string; got: \"{!s}\"".format(base_name)
            raise_field_def_exception(parent_name, field_name, msg)
        base = None
        if local_base_fields is not None:                       # at first, look for the base in local field set (if any)
            if base_name in local_base_fields:
                base = local_base_fields[base_name]
        if base is None:
            base = self.top_level_fields.get(base_name, None)   # if we still don't have base, the look for it in top_level defs bucket
        if base is None:
            raise_field_def_exception(parent_name, field_name, "base field \"{!s}\" not found".format(base_name))

        return base.clone(field_name, parent_name, field_def)

    def format_data(self, dest_stream: TextIO, raw_bytes: bytes):
        raise RuntimeError("Illegal StructuralFieldDef.format_data() call for structure or union {!s}".format(self.name))


class StructFieldDef(StructuralFieldDef):

    _CONFIG_KEYS = {"placement","fields"} | StructuralFieldDef._CONFIG_KEYS

    STRUCT_FIELD_PLACEMENT_KEYS = ["normal","aligned","oneline"]
    STRUCT_FIELD_PLACEMENT_ENUM = enum.Enum("STRUCT_FIELD_PLACEMENT_ENUM", STRUCT_FIELD_PLACEMENT_KEYS)
    DEFAULT_STRUCT_FIELD_PLACEMENT = STRUCT_FIELD_PLACEMENT_ENUM.normal

    @classmethod
    def convert_struct_placement_name(self, s: str):
        if s in self.STRUCT_FIELD_PLACEMENT_KEYS:
            return self.STRUCT_FIELD_PLACEMENT_ENUM[s]
        return None

    def __init__(self, name: str):
        super().__init__(name)
        self.placement = self.DEFAULT_STRUCT_FIELD_PLACEMENT
        self.fields = dict()

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]):
        """
        Clones structure definition. All fields from base structure are used, and new ones may be added.
        name:                   the name of the structure owning given fields list (necessary only for error reporting)
        parent_name:            the name of the parent of this structure (necessary only for error reporting)
        field_def:              field definition dictionary created from JSON stored in input format file.
        """
        r = super().clone(name, parent_name, field_def)

        if "placement" in field_def:
            placement_name = field_def["placement"]
            placement = self.convert_struct_placement_name(placement_name)
            if placement is None:
                raise_field_def_exception(parent_name, name, "unknown placement strategy name: \"{!s}\"".format(placement_name))
            r.placement = placement

        new_field_defs = field_def.get("fields",None)
        if (new_field_defs is not None):
            if not isinstance(new_field_defs,dict):
                msg = "Invalid structure fields specification. Dictionary is expected, got: {!s}".format(type(new_field_defs))
                raise_field_def_exception(parent_name, name, msg)
            if len(new_field_defs)>0:
                r.fields = r.fields.copy()        # we need to add to the list, so a separate one is necessary
                self.create_fields(name, parent_name, False, new_field_defs, r.fields)
        return r

    @classmethod
    def create_fields(self, name: str, parent_name: str, add_fields_as_top_level_definitions: bool,
                      structure_field_defs: Union[str,Dict[str,Dict[str,Any]]], fields: Dict[str,FieldDef]):
        """
        Adds structure fields into given fields list.
        name:                   the name of the structure owning given fields list (necessary only for error reporting)
        parent_name:            the name of the parent of this structure (necessary only for error reporting); may be None
        add_fields_as_top_level_definitions:    if set to true then all created 0-level field definitions are put into common dictionary
                                                of top_level fields that may serve as base definitions for any field at any level

        structure_field_defs:   field definitions created from JSON stored in input format file.
        fields:                 destination field list; may be empty; new fields are appened at the end
        """
        if (parent_name is not None) and (len(parent_name)>0):
            field_parent_name = parent_name + "." + name
        else:
            field_parent_name = name

        for field_name, field_def in structure_field_defs.items():
            if field_name in fields:
                msg = "Structure field \"{!s}\" already exits and field redefinition is not allowed".format(field_name)
                raise_field_def_exception(field_parent_name, field_name, msg)

            if isinstance(field_def, str):          # convert shorthand definition to canonical
                field_def = {"base":field_def}

            # special case: "base" key deduction to "struct" or "union" if "fields" or "variants" key found accordingly:
            if "base" not in field_def:
                if "fields" in field_def:
                    field_def = field_def.copy()
                    field_def["base"] = "struct"
                elif "variants" in field_def:
                    field_def = field_def.copy()
                    field_def["base"] = "union"

            field = self._create_field(field_name, field_parent_name, field_def, fields)
            fields[field_name] = field
            if add_fields_as_top_level_definitions:
                self.add_top_level_field(field)


class UnionFieldDef(StructuralFieldDef):

    _CONFIG_KEYS = {"variants"} | StructuralFieldDef._CONFIG_KEYS
    _UNION_VARIANT_SPEC_DEF_KEYS = {"prefetch_size", "data_offset", "total_size", "trigger"}

    def __init__(self, name: str):
        super().__init__(name)
        self.variants = dict()

    def clone(self, name: str, parent_name: str, field_def: dict[str,Any]):
        """
        Clones union definition. All variants from base union are inherited, and new ones may be added.
        name:                   the name of the structure owning given fields list (necessary only for error reporting)
        parent_name:            the name of the parent of this structure (necessary only for error reporting)
        field_def:              field definition dictionary created from JSON stored in input format file.
                                actually it is a variant definition: a field definition + additional variant-specific keys
        """
        r = super().clone(name, parent_name, field_def)

        new_field_defs = field_def.get("variants",None)
        if (new_field_defs is not None):
            if not isinstance(new_field_defs,dict):
                msg = "Invalid union fields specification. Dictionary is expcected, got: {!s}".format(type(new_field_defs))
                raise_field_def_exception(parent_name, name, msg)
            if len(new_field_defs)>0:
                r.variants = r.variants.copy()        # we need to add to the list, so a separate one is necessary
                self.create_variants(name, parent_name, new_field_defs, r.variants)
        return r

    @classmethod
    def create_variants(self, name: str, parent_name: str, union_variant_defs: Dict[str,Dict[str,Any]], variants: Dict[str,FieldDef]):
        """
        Adds union fields into given fields list.
        name:                   the name of the structure owning given fields list (necessary only for error reporting)
        parent_name:            the name of the parent of this structure (necessary only for error reporting)
        union_variant_defs:     variant definitions created from JSON stored in input format file.
        variants:               destination variant list; may be empty; new fields are appened at the end
        """
        if (parent_name is not None) and (len(parent_name)>0):
            variant_parent_name = parent_name + "." + name
        else:
            variant_parent_name = name

        if len(variants)!=0:
            last_variant = variants[list(variants.keys())[-1]]
        else:
            last_variant = None

        for variant_name, variant_def in union_variant_defs.items():
            if variant_name in variants:
                msg = "Union variant \"{!s}\" already exits and variant redefinition is not allowed".format(variant_name)
                raise_field_def_exception(variant_parent_name, variant_name, msg)

            if (last_variant is not None) and (last_variant.trigger is None):
                raise_field_def_exception(variant_parent_name, last_variant.name,
                                          "union variant does not have trigger defined and it is not the last variant on the list")

            prefetch_size = variant_def.get("prefetch_size",0)
            if not isinstance(prefetch_size,int) or (prefetch_size not in range(0,1024+1)):
                raise_field_def_exception(variant_parent_name, last_variant.name,
                                          "prefetch_size is not an integer in range [0..1024]; got: \"{!s}\"".format(prefetch_size))

            if (last_variant is not None) and (prefetch_size < last_variant.prefetch_size):
                raise_field_def_exception(variant_parent_name, last_variant.name,
                                          "prefetch size ({:d}) for union variant is smaller than previous variant's prefetch size"
                                          .format(prefetch_size))

            data_offset = variant_def.get("data_offset",0)
            if not isinstance(data_offset,int) or (data_offset not in range(0,1024+1)):
                raise_field_def_exception(variant_parent_name, last_variant.name,
                                          "data_offset is not an integer in range [0..1024]; got: \"{!s}\"".format(data_offset))

            total_size = variant_def.get("total_size",None)
            if total_size is not None:
                if not isinstance(total_size,int) or (total_size<1):
                    raise_field_def_exception(variant_parent_name, last_variant.name,
                                              "total_size is not a positive integer; got: \"{!s}\"".format(total_size))
                if data_offset >= total_size:
                    raise_field_def_exception(variant_parent_name, last_variant.name,
                                              "data_offset ({:d}) not less than total_size ({:d})".format(self.data_offset,self.total_size))

            trigger = variant_def.get("trigger",None)
            if trigger is not None:
                if not isinstance(trigger,str):
                    raise_field_def_exception(variant_parent_name, last_variant.name,
                                              "trigger is not a string expression; got: \"{:s}\"".format(trigger))
                try:
                    compiled_trigger = compile(trigger, parent_name, "eval")
                except:
                    raise_field_def_exception(parent_name, name,
                                              "cannot compile the trigger: \"{:s}\"".format(trigger))
            else:
                compiled_trigger = None

            # get rid of variant-specific keys from field definition in order to get correct regular field definition:
            field_def = {k:variant_def[k] for k in variant_def if k not in self._UNION_VARIANT_SPEC_DEF_KEYS}

            variant = self._create_field(variant_name, variant_parent_name, field_def, variants)
            variant.prefetch_size = prefetch_size
            variant.data_offset = data_offset
            variant.total_size = total_size
            variant.trigger = compiled_trigger

            variants[variant_name] = variant
            last_variant = variant

    def choose_variant(self, input_stream: BinaryIO) -> FieldDef:
        """
        Return union variant definition that triggered by trigger code. If no variant triggered, returns None
        May read bytes from stream in order to to determine its type but at the end moves the stream pointer back to its original location.
        NOTE: The returned value is one of the normal derivatives of base field definition decorated with union-variant specific fields:
        at least: data_offset and total_size that are required by outer client in order to handle data offsets correctly.
        """
        prefetched_data = bytes()
        result = None

        for k,v in self.variants.items():
            if v.prefetch_size > len(prefetched_data):
                prefetched_data = prefetched_data + input_stream.read(v.prefetch_size - len(prefetched_data))
                if len(prefetched_data) < v.prefetch_size:
                    raise EOFError("unexpected end of data file")
                self.namespace["RAW"] = prefetched_data
            if (v.trigger is None) or eval(v.trigger, {}, self.namespace):
                result = v
                break

        self.namespace.pop("RAW",None)                  # remove prefetched data if any remained
        input_stream.seek(-len(prefetched_data), 1)     # move back stream pointer (it may be trivial move by zero bytes)
        return result       # None if no variant triggered; leave decision to the caller


def create_base_types():
    StructuralFieldDef.add_top_level_field(SignedIntegerFieldDef("int"))
    StructuralFieldDef.add_top_level_field(UnsignedIntegerFieldDef("uint"))
    StructuralFieldDef.add_top_level_field(IntegerTimestampFieldDef("ts"))
    StructuralFieldDef.add_top_level_field(FloatTimestampFieldDef("fts"))
    StructuralFieldDef.add_top_level_field(FloatFieldDef("float"))
    StructuralFieldDef.add_top_level_field(CharacterFieldDef("char"))
    StructuralFieldDef.add_top_level_field(SkipFieldDef("skip"))
    StructuralFieldDef.add_top_level_field(StructFieldDef("struct"))
    StructuralFieldDef.add_top_level_field(UnionFieldDef("union"))


def create_fields(name: str, add_fields_as_top_level_definitions: bool,
                  structure_field_defs: Dict[str,Dict[str,Any]], fields: Dict[str,FieldDef]):
    """The entrypoint to the structure creation mechanism"""
    StructFieldDef.create_fields(name, None, add_fields_as_top_level_definitions, structure_field_defs, fields)


def set_default_separator(s: str):
    if not isinstance(s,str):
        raise DefaultValueException("Invalid default field separator; expected string, got: {!s}".format(s))
    NonStructuralTypeFieldDef.DEFAULT_SEPARATOR = s


def set_default_endian(s: str):
    if s not in {"little","big","system"}:
        raise DefaultValueException(
            "Invalid default endian (byteorder) specification; legal values: \"little\",\"big\",\"system\"; got: \"{!s}\"".format(s))
    if s == "system":
        s = sys.byteorder
    NumericTypeFieldDef.DEFAULT_ENDIAN = s


def set_default_integer_format(s: str):
    if not isinstance(s,str):
        raise DefaultValueException("Invalid default integer field printing format; expected string, got: {!s}".format(s))
    IntegerTypeFieldDef.DEFAULT_FORMAT = s


def set_default_integer_size(v: int):
    if (not isinstance(v,int)) or (v<1) or (v>128):
        raise DefaultValueException("Invalid default integer field size; expected integer in range [1..128], got: {!s}".format(v))
    IntegerTypeFieldDef.DEFAULT_SIZE = v


def set_default_timestamp_format(s: str):
    if not isinstance(s,str):
        raise DefaultValueException("Invalid default timestamp field printing format; expected string, got: {!s}".format(s))
    TimestampTypeFieldDef.DEFAULT_FORMAT = s


def set_default_timezone_offset(v: int):
    if not is_tzoffs_valid(v):
        raise DefaultValueException("Invalid default timezone; expected null or integer divisible by 60, got: {!s}".format(v))
    TimestampTypeFieldDef.DEFAULT_TZOFFS = v


def set_default_integral_timestamp_size(v: int):
    if (not isinstance(v,int)) or (v<4) or (v>8):
        raise DefaultValueException("Invalid default integer timestamp field size; expected integer in range [4..8], got: {!s}".format(v))
    IntegerTimestampFieldDef.DEFAULT_SIZE = v


def set_default_float_format(s: str):
    if not isinstance(s,str):
        raise DefaultValueException("Invalid default float field printing format; expected string, got: {!s}".format(s))
    FloatFieldDef.DEFAULT_FORMAT = s


def set_default_float_size(v: int):
    if (not isinstance(v,int)) or (v not in {4,8}):
        raise DefaultValueException("Invalid default float field size; only 4 and 8 are allowed (IEEE-754), got: {!s}".format(v))
    FloatFieldDef.DEFAULT_SIZE = v


def set_default_stop_string_on_zero(v: bool):
    if not isinstance(v,bool):
        raise DefaultValueException("Invalid default character field stop-on-zero flag; boolean expected, got: {!s}".format(v))
    CharacterFieldDef.DEFAULT_STOP_ON_ZERO = v


def set_default_character_encoding(s: str):
    if not CharacterFieldDef.is_encoding_name_valid(s):
        raise DefaultValueException("invalid default character encoding specifier: \"{!s}\"".format(s))
    CharacterFieldDef.DEFAULT_ENCODING = s


def set_default_structure_fields_placement(s: str):
    placement = StructFieldDef.convert_struct_placement_name(s)
    if placement is None:
        raise DefaultValueException("invalid default structure fields placement specifier: \"{!s}\"".format(s))
    StructFieldDef.DEFAULT_STRUCT_FIELD_PLACEMENT = placement

