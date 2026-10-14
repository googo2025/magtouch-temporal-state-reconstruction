# Published repository structure and version identities

One repository contains the joint magnetic-supervision framework, explicit epoch138 and shared epoch529 implementations and separately citable papers. Existing explicit public files and measured GIF remain at their original paths; route modules also retain the exact 79-file companion.

The root MANIFEST describes the current controlled publication files and preserved legacy Git blobs. SHA256SUMS covers controlled files and MANIFEST. Run python -B tools/verify_release.py in a clean checkout for identities and links, and python -B tools/recompute_results.py for scalar aggregation. Git metadata directories are excluded from verification. Raw arrays, checkpoints, optimizer states, private geometry and credentials are not included.

The actual commit is the publication identity. Proposed route tags are not created tags; authors, affiliations and genuine paper DOI remain to be supplied. Papers are project research manuscripts rather than journal acceptance records. The shared paper has reviewed scientific content and figures; final journal-specific layout remains for submission.
