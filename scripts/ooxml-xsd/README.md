# OOXML schemas for the built-deck test

`scripts/test_ooxml_schema.py` builds every deck in `plugins/decks/examples/` and
validates each `ppt/slides/slide*.xml` and `ppt/charts/chart*.xml` part against
these schemas. PowerPoint silently drops XML that breaks the schema, while
LibreOffice and python-pptx both accept it: that is how every builder bullet went
missing from real decks without a single test going red.

## Source

ECMA-376 5th edition, Part 4, *Transitional Migration Features* (December 2016),
the text of ISO/IEC 29500-4:2016. Downloaded from Ecma International:

- <https://ecma-international.org/publications-and-standards/standards/ecma-376/>
- archive `ECMA-376-4_5th_edition_december_2016.zip`,
  sha256 `bd25da1109f73762356596918bf5ff8b74a1331642dba5f1c1d1dfc6bed34ecd`
- inner archive `OfficeOpenXML-XMLSchema-Transitional.zip`,
  sha256 `d34187520749998af306faf1b730e568b0ca6d88ad24638a407c0a9bb4ca04fc`

Only the nine files `pml.xsd` and `dml-chart.xsd` import, directly or through each
other, are vendored:

| File | Namespace |
|---|---|
| `pml.xsd` | PresentationML (slides) |
| `dml-chart.xsd` | DrawingML charts |
| `dml-main.xsd` | DrawingML main |
| `dml-chartDrawing.xsd` | chart drawings |
| `dml-diagram.xsd` | diagrams |
| `dml-lockedCanvas.xsd` | locked canvas |
| `dml-picture.xsd` | pictures |
| `shared-commonSimpleTypes.xsd` | shared simple types |
| `shared-relationshipReference.xsd` | relationship references |

The schemas are unmodified apart from line endings: the repository's pre-commit
hooks store every text file with LF endings, and five of these files ship with CRLF.

## Licence

These files are Ecma International documents, distributed under Ecma's copyright
notice, reproduced here as it requires:

> © 2016 Ecma International
>
> This document may be copied, published and distributed to others, and certain
> derivative works of it may be prepared, copied, published, and distributed, in
> whole or in part, provided that the above copyright notice and this Copyright
> License and Disclaimer are included on all such copies and derivative works. The
> only derivative works that are permissible under this Copyright License and
> Disclaimer are:
>
> 1. works which incorporate all or portion of this document for the purpose of
>    providing commentary or explanation (such as an annotated version of the
>    document),
> 2. works which incorporate all or portion of this document for the purpose of
>    incorporating features that provide accessibility,
> 3. translations of this document into languages other than English and into
>    different formats and
> 4. works by making use of this specification in standard conformant products by
>    implementing (e.g. by copy and paste wholly or partly) the functionality
>    therein.
>
> However, the content of this document itself may not be modified in any way,
> including by removing the copyright notice or references to Ecma International,
> except as required to translate it into languages other than English or into a
> different format.
>
> The official version of an Ecma International document is the English language
> version on the Ecma International website. In the event of discrepancies between
> a translated version and the official version, the official version shall govern.
> The limited permissions granted above are perpetual and will not be revoked by
> Ecma International or its successors or assigns.
>
> This document and the information contained herein is provided on an "AS IS"
> basis and ECMA INTERNATIONAL DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED,
> INCLUDING BUT NOT LIMITED TO ANY WARRANTY THAT THE USE OF THE INFORMATION HEREIN
> WILL NOT INFRINGE ANY OWNERSHIP RIGHTS OR ANY IMPLIED WARRANTIES OF
> MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.

Ecma's policy page for this notice:
<https://ecma-international.org/policies/by-ipr/ecma-text-copyright-policy/>.
Do not replace these files with copies taken from another tool's bundle: some of
those carry their own, more restrictive licence. Download from Ecma instead.
