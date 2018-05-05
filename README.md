# setup-finder

setup-finder is a tool for generating opening setups in Tetris. It leverages knewjade's solution-finder program to find setups that span multiple bags.

My goal is to be able to find any setups that fit a broad set of user-defined rules, but for now I am working on setups that start with a T-Spin and end in a Perfect Clear after 3 bags. (Example: setup-finder output this result: https://tinyurl.com/ycfjueav. Me performing the discovered techinque: https://youtu.be/QXB4dC58tMw)

Current version requires solution-finder v0.511: (I will be updating this soon)
https://github.com/knewjade/solution-finder/

To try out the current script, unzip solution-finder into setup-finder's folder and run "py find.py". (Warning: the current demo looks at almost 3000 possible TSS setups, and takes ~12min to run on my machine.) The results will be in output.txt. You can use the customized version of fumen included to import a list of continuations into one diagram.
