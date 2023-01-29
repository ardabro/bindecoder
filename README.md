# bindecoder

**When hexdump is not enough...**

This is a small utility program that presents binary file of known format in a human friendly fashion. The only requirement is to specify the file structure in dedicated json file.

**Main program usage:**

```
> python3 -m utils.misc.bindecoder --help
usage: bindecoder.py [-h] [--recreate-config] [--skip-config] [--input-offset INPUT_OFFSET] [--struct STRUCT] [--format FORMAT] [input_file]

Decodes a binary file according to the format specified in configuration file

positional arguments:
  input_file            binary input file to process

optional arguments:
  -h, --help            show this help message and exit
  --recreate-config     re-create configuration file using standard values
  --skip-config, -sc    skip using config file; default values will be the same as with default config, no typedefs will be created
  --input-offset INPUT_OFFSET, -s INPUT_OFFSET
                        starting offset in the input file
  --struct STRUCT, -st STRUCT
                        structure name to start from instead of top-level dataset
  --format FORMAT, -f FORMAT
                        json file containing format specification
```

**Key files:**

* `FORMAT_SPEC.md` - a document describing format file structure

* `bindecoder.py` - the main program

* `bindecoder.cfg` - configuration file in json format. It defines some common default values as well as trivial data structures for raw-data dumps. One can add own data structures here; default configuration file may be recreated with option `--recreate-config` passed to the main program

* `test_structures_format.json` - a couple of data structure definitions for test and presentation purposes;

* `generate_test_bin_files.py` - Program creating a couple of tiny binary files that may be decoded using format file mentioned above.

**Sample usage and output:**

```
> python3 -m bindecoder -f test_structures_format.json header_and_points.bin -st header_and_points

00000000  eyecatcher:    "EYECATCHER"
0000000a  num_of_points: 6
0000000e  points (count == 6):
0000000e      points[0]:
0000000e          x: 0x0101
00000010          y: 0x1111
00000012      points[1]:
00000012          x: 0x0202
00000014          y: 0x2222
00000016      points[2]:
00000016          x: 0x0303
00000018          y: 0x3333
0000001a      points[3]:
0000001a          x: 0x0404
0000001c          y: 0x4444
0000001e      points[4]:
0000001e          x: 0x0505
00000020          y: 0x5555
00000022      points[5]:
00000022          x: 0x0606
00000024          y: 0x6666
00000026  footer:        "FOOTER"
SUCCESS
```

```
> python3 -m utils.misc.bindecoder -f test_structures_format.json list_of_lists.bin -st list_of_lists

00000000  num_of_lists: 5
00000002  lists (count == 5):
00000002      lists[0]:
00000002          length: 03;  eyecatcher: "AAAA1";  checksum: 0xaaaa;  timestamp: 2002-08-10 00:46:41;
0000000e          data (count == 3):
0000000e              00 01 02
00000011      lists[1]:
00000011          length: 00;  eyecatcher: "BBBB2";  checksum: 0xbbbb;  timestamp: 2002-08-10 00:46:42;
0000001d          data (count == 0)
0000001d      lists[2]:
0000001d          length: 01;  eyecatcher: "CCCC3";  checksum: 0xcccc;  timestamp: 2002-08-10 00:46:43;
00000029          data (count == 1):
00000029              10
0000002a      lists[3]:
0000002a          length: 13;  eyecatcher: "DDDD4";  checksum: 0xdddd;  timestamp: 2002-08-10 00:46:44;
00000036          data (count == 13):
00000036              data[ 0]: 20 21 22 23 24 25
0000003c              data[ 6]: 26 27 28 29 30 31
00000042              data[12]: 32
00000043      lists[4]:
00000043          length: 06;  eyecatcher: "EEEE5";  checksum: 0xeeee;  timestamp: 2002-08-10 00:46:45;
0000004f          data (count == 6):
0000004f              30 31 32 33 34 35
00000055  footer:       "FOOTER"
SUCCESS
```
