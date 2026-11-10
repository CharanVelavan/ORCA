# Offline legal hierarchy inputs

These text fixtures capture the page text used by the hierarchy parser tests for four official
sources. Form feeds preserve page boundaries. Trailing line whitespace is normalized. `manifest.json`
records each original PDF checksum and source URL, extraction method and fixture checksum.

They test clause boundaries, breadcrumb labels, parent IDs and expected text in an offline checkout.
The tests verify fixture bytes and keep the existing assertions. A separate synthetic two-page PDF
covers the PDF reader. CI does not download official PDFs or establish their current legal status.
Full source acquisition and quoted-record verification remain separate KB workflows.
