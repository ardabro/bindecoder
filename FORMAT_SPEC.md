# This file describes data format definition file syntax.

## A small tutorial

Generally a data format file specifies a set of file structure fields. A field may represent a simple data type or a structure composed of other fields. Each field specification is derived - directly or indirectly - from one of fixed fundamental field definitions. Field specification derives all parameters from its base and may redefine each of them. A list of available parameters varies from (field) type to (field) type. Indirect derivation means that field may be also derived from other field lying int same structure, or globally defined (at top level). Data format is written in **json**.

A simple data format file may look like this:

```json
{
    "format_id":{"base":"char", "size":4, "encoding":"ascii", "stop_on_zero":false},
    "checksum":{"base":"uint", "size":2, "format":"0x{:08x}"},
    "timestamp":{"base":"ts", "size":4, "format":"%Y-%m-%d %H:%M:%S"},
    "num_of_records":{"base":"uint", "size":4, "format":"{:d}"}
}
```

This code specifies something  looking like file header.

We have 4-field structure here. The key value for a field is a string that serves as label in the program output. A definition is a dictionary containing field parameters. Some of them as `base` or `count` are commonly used for all field types.

**A note about ``format`` specifier:**

Format specifiers are "borrowed" from python's standard library specification. For numeric values it is a format string used by ```str.format()``` operation: [str.format() specification](https://docs.python.org/3/library/string.html#formatspec). For timestamps it is a format string defined for `time.strftime()` operation: [time.strftime() specification](https://docs.python.org/3/library/time.html?highlight=strftime#time.strftime)

The format specification presented above looks a bit verbose, but may be compacted by using predefined types and default values. Common, universal field types are defined in config file.  Equivalent format file utilizing defaults and typedefs specified in standard config `bindecoder.cfg` may look like this:

```json
{
    "format_id":{"base":"char", "size":4},
    "checksum":{"base":"uint16"},
    "timestamp":{"base":"ts"},
    "num_of_records":{"base":"uint32"}
}
```

or even more compacted, with shorthand base specification wherever possible:

```json
{
    "format_id":{"base":"char", "size":4},
    "checksum":"uint16",
    "timestamp":"ts",
    "num_of_records":"uint32"
}
```

Now lets add some records:

```json
{
    "format_id":{"base":"char", "size":4},
    "checksum":"uint16",
    "timestamp":"ts",
    "num_of_records":"uint32",
    "records":
    {
        "base":"struct",            // optional; "struct" is assumed if "fields" key appears
        "count":"num_of_records",
        "fields":
        {
            "x":"int16",
            "y":"int16",
            "z":"int16"
        }
    }
}
```

A record is a simple `x,y,z` structure and the number of records is specified by one of the fields in header.

**A note about back-referred values**:

The value of each **unsigned integer** field met by the data file processor is put into common global dictionary serving as a source for back references. The dictionary is flat, so if more than one structure has a field with the same name, they will be interfering - the newer value overwrites the existing one in the dictionary.

A richer data format file may define a set of data structures. Some of them may be then embedded in the others, and any top-level one may be chosen to serve as root for data file structure. There is a `--struct` (`-st`) parameter selecting root structure. This means than one data format file may define a multiple binary file structures, and it is a good idea to do so if we need to handle a family of related files with partially common structures.

An example:

```json
{
    "TYPEDEFS":
    {
        "file_header":
        {
            "fields":
            {
                "format_id":{"base":"char", "size":4},
                "checksum":"uint16",
                "timestamp":"ts",
                "num_of_records":"uint32"
            }
        },

        "xy_records":
        {
            "count":"num_of_records",
            "fields":
            {
                "x":"int16",
                "y":"int16"
            }
        },

        "xyz_records":
        {
            "base":"xy_records",
            "fields":
            {
                "z":"int16"
            }
        },

        "xy_points_file":       // this one defines the structure of the whole xy file
        {
            "fields":
            {
                "header":"file_header",
                "records":"xy_records"
            }
        },

        "xyz_points_file":      // this one defines the structure of the whole xy file
        {
            "fields":
            {
                "header":"file_header",
                "records":"xyz_records"
            }
        }
    },

    "header":"file_header"      // default dataset used when structure is not specified in the command line
}
```

Example outputs:

```
> python3 -m bindecoder -f sample.json xyz_points.bin -st xyz_points_file

00000000  header:
00000000      format_id: "XYZF"
00000004      checksum: 0x55aa
00000006      timestamp: 2023-01-28 20:21:07
0000000a      num_of_records: 0x00000003
0000000e  records (count == 3):
0000000e      records[0]:
0000000e          x:     +1
00000010          y:    +11
00000012          z:   +101
00000014      records[1]:
00000014          x:     +2
00000016          y:    +12
00000018          z:   +102
0000001a      records[2]:
0000001a          x:     +3
0000001c          y:    +13
0000001e          z:   +103
SUCCESS
```

```
> python3 -m bindecoder -f sample.json xyz_points.bin

00000000  header:
00000000      format_id: "XYZF"
00000004      checksum: 0x55aa
00000006      timestamp: 2023-01-28 20:21:07
0000000a      num_of_records: 0x00000003
SUCCESS
```

## Field definition parameters list:

- **base** - specifies a base field for other field

- **count** - specifies a number of subsequent field instances (array length)

- **size** - field size in bytes; applies to ordinary fields only (all, exluding **struct**, **union**, **skip**)

- **wrap_at** - wrap line after this number of elements when **count**>1; same remark as above

- **separator** - separator string to put between elements when **count**>1; same remark as above

- **format** - format string for numeric and timestamp fields

- **endian** - byteorder for numeric and timestamp fields ("**little**", "**big**", "**system**")

- **tzoffs** - timezone offset in minutes (must be divisible by 60); **null** means current local time zone; applicable for timestamps

- **multiplier** - unix time multiplier; applicable for integer timestamps only; value 1000 means that timestamp is stored as milliseconds

- **encoding** - string character encoding; see [encodings](https://docs.python.org/3/library/codecs.html#standard-encodings); applicable for **char** fields only

- **length** - the length of the string in characters; applicable for **char** fields only

- **stop_on_zero** - (**true**, **false**); whether to end showing characters at first zero byte; applicable for **char** fields only

## Field types

- **int** - signed integer
- **uint** - unsigned integer
- **float** - floating point number; size 4 or 8 (IEEE-754 single or double)
- **ts** - integral timestamp (unix time); minimum 4 bytes, may be "shifted" i.e. multiplied by unsigned integer factor
- **fts** - floating point timestamp (unix time); the only acceptable size value is 8 bytes (IEEE-754 double)
- **char** - a string of characters;
- **struct** - a structure consisting of attributes; many containment levels allowed
- **union** - a set of variants; one of them at a time is chosen dynamically with user-defined formula
- **skip** - a special kind of field ordering the processor to simply skip the specified number (count) of bytes;

## Structures

Structure is a set of fields appearing in strict order (like in every civilized programming language). A field in the structure may be virtually anything including other structure or union.  Structure definition uses some additional special-purpose parameters:

- **fields** - a dictionary specifying structure fields; this key is not obligatory; if doesn't appear the structure simply inherits all fields from its base. In particular a structure based on fundamental **struct** with no fields defined is empty - this is correct; if **fields** key appears in the definition then **base** is not obligatory and defaults to **struct**; if structure is based on other, non-empty structure, then it simply appends its fields to the fields list inherited from base.

- **placement** - this parameter specifies how ordinary fields of the structure will be presented:****

  - **normal** - in separate lines without any additional formatting; fields names are aligned to the left, values are not

  - **aligned** - same as above + values are aligned horizontally

  - **oneline** - all fields in one line with separator between them

## Unions

Union defines a number of fields and one of them is chosen dynamically based on arbitrary conditions. Good example is a variable integer defined for bitcon blockchain. see [VarInt - Bitcoin Wiki](https://wiki.bitcoinsv.io/index.php/VarInt). Here union definition for VARINT:

```json
    "VARNINT":
    {
        "base":"union",
        "variants":
        {
            "VINT8":
            {
                "prefetch_size":1,
                "data_offset":0,
                "total_size":1,
                "trigger":"RAW[0]<0xFD",

                // and normal data type fields for the field appearing as this variant:
                "base":"uint",
                "size":1,
                "format":"{:02x}"
            },
            "VINT16":
            {
                "prefetch_size":1,
                "data_offset":1,                // skip 1st byte (0xFD)
                "trigger":"RAW[0]==0xFD",
                "base":"uint",
                "size":2,
                "format":"{:04x}"
            },
            "VINT32":
            {
                "prefetch_size":1,
                "data_offset":1,                // skip 1st byte (0xFE)
                "trigger":"RAW[0]==0xFE",
                "base":"uint",
                "size":4,
                "format":"{:08x}"
            },
            "VINT64":
            {
                "prefetch_size":1,
                "data_offset":1,                // skip 1st byte (0xFF)
                "trigger":"RAW[0]==0xFF",
                "base":"uint",
                "size":8,
                "format":"{:016x}"
            }
        }
    }
```

The **union** definition specifies a set of variants. A variants is a normal field (of any type) definition + additional control parameters:

- **prefetch_size** - how many bytes do we need to take from input data stream to determine if given variant triggers; these prefetched bytes are put into byte array named **RAW** and passed to trigger code; this parameter is optional for the very last variant definition as soon as **trigger** parameter doesn't appear as well (see below)

- **data_offset** - the offset of the actual field data; this parameters allows skipping prefetched bytes if they are not a part of the actual data; in the example above **prefetch_size** for 1st variant is zero which means that if 1st byte value is below 0xFD then it contains the actual data; in other variants the first byte is only a variant determinant and it is skipped

- **total_size** - an optional parameter specifying the total size of the variant including actual data size and offset; it may add some unused tail at the end of the variant; for example it may enforce the same total size for all variants regardless of their individual actual data sizes

- **trigger** - a python code deciding whether given variant triggers or not; if variant triggers then other variants lying below it are ignored; the very last union variant is not required to have a trigger. If doesn't then it triggers every time when no other variant triggers before. If no variant triggers, an error is reported
