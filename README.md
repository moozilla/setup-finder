# setup-finder

**setup-finder** is a tool for generating opening setups in Tetris. It leverages knewjade's **solution-finder** program to find setups that span multiple bags.

My goal is to be able to find any setups that fit a broad set of user-defined rules (T-Spins, Tetrises, or custom shapes) and classify them based on how likely they are possible to build and if they are possible to Perfect Clear. The current version of setup-finder supports any number of bags with each bag containing a TSS, TSD, TST, or Tetris, and optionally ending with a PC.

Current version requires solution-finder v0.511 (I will be updating this soon):
https://github.com/knewjade/solution-finder/

## Usage

Grab the v0.1 release here: https://github.com/moozilla/setup-finder/releases/tag/v0.1

I recommend using setup-finder from the command-line. To run with the default settings, simply run the command `finder` from setup-finder's folder. This will look for the input file `input.txt` and use the skin `default.png` to output results. Results will be in `output/output.html`. Example output:

![Example setup-finder output](https://i.imgur.com/5ZY9kUQ.png)

(An image representing the best continuation for each bag is shown. For PCs an example of how to clear the PC with the highest success rate is shown (not necessarily the best method overall). To see all the continuations, click the **# continuations** link for a fumen diagram.)

To specify an input file use the `--input` or `-i` flag. To specify a different skin files (there are some options in the included `skins` folder) use `--skin` or `-s`. See below for how to setup input files.

**Warning:** More complicated setups (TSS→TST→TSD or TSD→TSD→TSD) can take a long time to run (several hours) even on a fairly beefy machine. Note that setup-finder saves every setup and PC result solution-finder finds in a cache file (`cache.bin`), so if you stop in the middle of a calculation or want to regenerate a setup it will go much faster the next time (near instantaneously if you re-run the same input).

To compress the generated cache file (`cache.bin`) use the `--pack` flag (this is intended for sharing cache files, it will take longer to save the cache with this set).

## input.txt

Setups to be searched are specified in `input.txt`. Example:

```
TSD row-1,2 col-any filter-isTSD-any
TSD row-1,2 col-any filter-isTSD-any
PC height-4 cutoff-80.00
```

Each line corresponds to a bag of 7 pieces. Arguments are separated by spaces. The first argument of the line is the _setup-type_. Here are the currently supported *setup-type*s:

* _TSS1_ - T-Spin single that clears the bottom row
* _TSS2_ - T-Spin single that clears the top row
* _TSS_/_TSS-any_ - T-Spin single that clears either row
* _TSD_/_TSD-any_ - T-Spin double (TSD-any will differentiate between standard TSD and weirder TSDs like Fin, Neo, etc.)
* _TST_ - T-Spin triple
* _Tetris_ - Tetris setup (note: unlike T-Spin setups with a filter argument, this _does not_ clear any rows, it just sets up the Tetris)
* _PC_ - Perfect Clear (note: this should be the last line specified)

Each line can contain additional arguments:

* _row_ - Which rows to look for setups on. For T-Spins the row being searched corresponds to the center of the T-piece. For Tetrises, the row should be the bottom row of the Tetris. The bottom of the field is row 0, and it counts upwards from there. You can specify a single row (eg. `row-0`) or multiple rows (eg. `row-0,2,3`).
* _col_ - Which columns to look for setups in. For T-Spins this corresponds to the center of the T-piece, for Tetrises it's the column where the I piece will drop. Columns go from 0-9 left to right. `col-any` will try all the possible columns for that particular setup (so 0-9 for Tetris, 1-7 for TSD, 1-8 for TST).
* _filter_ - Used after setups are found to make sure they fit the specified criteria. You should probably use a filter if you are looking for T-Spins.
  * `isTSS-any` tests if a solution is a T-Spin single, with either a flat or vertical T.
  * `isTSD-any` tests if a solution is a T-Spin double.
  * `isTST` tests if a solution is a T-Spin triple.
  * `isTSS-any`, `isTSD-any`, and `isTST` all require the setup to use all 7 pieces, they will also automatically add the T piece and clear lines before the next stage is calculated.
  * Use `testTSD` to test if a solution is a TSD without actually adding the T piece and clearing lines - useful if you want to setup a TSD and then potentially clear it a different way (with a PC for example).

The _PC setup-type_ has it's own special arguments:

* _height_ - The height of the PC. (eg. If you are looking for 8-high PCs and you have already cleared a TSD, use `height-6`)
* _cutoff_ - The cutoff rate for PC success (percentage). PCs with success rate lower than this won't be shown. Use `cutoff-0.01` to show all PCs (this is the lowest success rate solution-finder can return).

### More examples:

TSS → TST → TSD+PC:

```
TSS row-1,2 col-any filter-isTSS-any
TST row-1,2 col-any filter-isTST
TSD row-1,2 col-any filter-testTSD
PC height-4 cutoff-0.01
```

## Custom skins

With the `--skin` flag you can specify a custom skin used for generating the images in `output.html`. Example:

![Example skin file](https://raw.githubusercontent.com/moozilla/setup-finder/master/res/skins/nullpo1.png)

This should be in PNG format and the block colors should follow the order shown in the example. Any size block should work as long as blocks are square (block size is determined by the height of the image).

## Running on Mac/Linux

1. Clone the source code with `git clone https://github.com/moozilla/setup-finder.git`
2. Install the python package by running `pip install .` from inside the directory you cloned the project into.
3. Download the release and copy over `input.txt`, `default.png`, `cache.bin` and the `solution-finder-0.511` directory into the directory you installed the package.
4. Run the tool from the terminal using `setup-finder`.

Note: Because this program using solution-finder, you will also need a valid Java installation.

## License and Contact Info

`setup-finder` is copyright 2018 moozilla. Code licensed under the [MIT License](https://github.com/moozilla/setup-finder/blob/master/LICENSE). Licenses of all dependencies included and linked against can be found in LICENSES.md.

Feel free to contact me with any questions, ideas, or suggestions:

Twitter: [@spikeman](https://twitter.com/spikeman)
Discord: pwn#4801 (find me on the [Hard Drop discord server](https://discord.gg/harddrop))
