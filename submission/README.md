# Submitted report

[ORCA-NTN-SolarSailors-Report.pdf](ORCA-NTN-SolarSailors-Report.pdf) is the approved, submitted
five-page PDF. It is archived unchanged as the submission record. SHA-256:
`eb40a7343f45d2fac4d980a44d51bb373e9d2915301159871200eda07fce251f`.

The older v7 working files and update script below are retained for history. They can predate the
final branding/export; use the submitted PDF as the submission record.

---

# Report v7

The DOCX and PDF contain the same updated report. The PDF is five pages, including figures and references.

This revision adds the nine selected Readiness dimension mappings and their rationale. Planned scenario
coverage is S0 5/9, N2/N3 8/9, and the other seven scenarios 9/9. Planned coverage is distinct from
observed results. The report also describes scenario briefings, condition Stop, judge review and public
recording export. Repeated prose and illustration space were reduced; template margins and body size
were preserved. The harder-test M1 false-alarm figure follows the current `orca/models/metrics.json`.

`update_v7.py` applies these approved content edits to an existing v7 DOCX without rebuilding the report
from an earlier version. Run it with the DOCX path, then export and visually verify again. It does not
generate the PDF. This PDF was rendered with the bundled LibreOffice renderer using the installed
Times New Roman fonts. Word or another renderer can paginate differently; use the verified PDF for
the five-page submission.
