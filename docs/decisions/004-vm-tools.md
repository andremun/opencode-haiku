# 004. VM tools come from haiku-k40c

Date: 2026-10-23. Status: accepted (alignment plan decision D4).

`haiku-k40c` `tools/haiku/` owns the Haiku VM tools. This repository uses them for its
development and acceptance runs only, pinned by commit and hash. The VM disk moves from
`vm/` to `HAIKU_VM_DIR`. Users of the installed port need none of this.
