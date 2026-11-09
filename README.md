# Verity — Text Integrity Studio

A local document-similarity screening application built with **Python** and **Streamlit**. Verity compares text using the **Rabin–Karp rolling-hash algorithm**, identifies verified exact-text overlaps, highlights matching passages, and reports directional coverage scores.

> **Important:** This application is an exact-text screening aid. Its scores are not probabilities, authorship conclusions, or proof of plagiarism. A person should review the highlighted passages and their context before drawing conclusions.

## Author

|           |                            |
| --------- | -------------------------- |
| **Name**  | Rohit Khobare              |
| **Email** | rohitkhobare2005@gmail.com |

## Project at a glance

- Compare two documents using a sample, pasted text, or an uploaded text/PDF file.
- Compare a collection of documents pairwise and inspect a similarity matrix.
- See directional coverage, matched passages, original-text highlights, and algorithm statistics.
- Benchmark Rabin–Karp against a naive matching baseline on generated text.
- Switch the Streamlit interface between light and dark themes.
- Run the analysis locally; the detector compares the documents provided to it and does not search the web.

## Contents

- [Features](#features)
- [How text matching works](#how-text-matching-works)
- [Understanding the scores](#understanding-the-scores)
- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Installation and launch](#installation-and-launch)
- [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
- [Using the application](#using-the-application)
- [Command-line usage](#command-line-usage)
- [Tests](#tests)
- [Limitations](#limitations)
- [Example experiments](#example-experiments)
- [Frequently asked questions](#frequently-asked-questions)
- [Author](#author)

## Features

### Two-document comparison

- Choose a sample document, paste or write text, or upload a `.txt` or `.pdf` file for each side.
- View live word counts and the number of characters available for matching after normalization.
- Set the minimum match length, `k`, in the sidebar.
- Review coverage in both directions, an overall score, and the number of matched passages.
- Inspect highlighted text in the original documents and a table of verified passages with character offsets.
- Download matched passages as CSV and expand technical hash and timing statistics.
- See when displayed analysis results need to be rerun after inputs or settings change.

### Multiple-document review

- Compare all unique pairs among the sample documents and uploaded files.
- View pairwise scores sorted by similarity and a symmetric similarity matrix.
- Download the pairwise report as CSV.

### Algorithm benchmark

- Generate synthetic document pairs with a copied section inserted into one document.
- Compare Rabin–Karp with a straightforward naive matching method.
- Adjust document sizes and approximate copied-text ratio.
- Inspect runtime, character comparisons, hash lookups, passage counts, and similarity charts.
- The interface limits requested text lengths to 8,000 characters because the naive comparison can become slow.

### Theme and guidance

- Switch the whole workspace between light and dark appearance using the sidebar toggle.
- Follow the method guide for normalization, rolling hashes, verification, passage grouping, and score interpretation.
- Review the limitations before interpreting a screening result.

## How text matching works

1. **Normalize:** Convert letters and digits to lowercase, discard spaces and punctuation, and retain a map back to each character's position in the original text.
2. **Create k-grams:** Divide the normalized text into every overlapping window of `k` characters.
3. **Calculate rolling hashes:** Compute Rabin–Karp polynomial hashes for the windows. The default hash base is `257`; the default modulus is `2^61 - 1`.
4. **Find candidates:** Index the hashes from one document and look up hashes from the other.
5. **Verify candidates:** Compare candidate text character by character. Equal hashes with unequal text are hash collisions and are rejected.
6. **Group passages:** Merge overlapping, adjacent k-gram matches along the same alignment into passages and remove fully redundant coverage.
7. **Map and score:** Map passage positions back to the original text, highlight them, and calculate normalized-text coverage.

The Rabin–Karp approach takes expected linear time to hash and look up windows, plus the time required to verify hash hits. The naive benchmark compares every k-gram window in one document with every window in the other, so its work grows roughly with the product of the window counts.

## Understanding the scores

- **A covered by B** is the percentage of Document A's normalized characters covered by matched passages in Document B.
- **B covered by A** is the reverse calculation.
- **Overall similarity** is the larger of those two directional coverage values. This makes copied content visible when one document is substantially shorter than the other; it is not an average of the two percentages.
- Coverage is calculated over normalized letters and digits, not the original character count. Spaces and punctuation do not count toward the denominator.
- The verdict bands used by the core engine are:
  - **60% or higher:** High similarity.
  - **30% to below 60%:** Moderate similarity.
  - **10% to below 30%:** Low similarity.
  - **Below 10%:** Very low similarity.

These are descriptive screening labels, not academic-integrity decisions. Short common phrases can match coincidentally; review passages in context.

## Project structure

```text
plagiarism_detector/
├── app.py                  # Streamlit user interface
├── plagiarism_core.py      # Normalization, rolling hashes, matching, scoring, CLI, benchmark
├── requirements.txt        # Python package dependencies
├── samples/
│   ├── original.txt
│   ├── copied_partial.txt
│   └── unrelated.txt
└── tests/
    └── test_core.py        # Core algorithm unit tests
```

## Requirements

- Python **3.10 or later** is recommended.
- Dependencies are listed in [`requirements.txt`](requirements.txt):
  - Streamlit 1.40 or later
  - pandas 2.0 or later
  - pypdf 4.0 or later

## Installation and launch

Run these commands from the project directory.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell activation is restricted by your system policy, call the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local URL (typically `http://localhost:8501`) when the application starts. Stop the server with `Ctrl+C` in the terminal.

## Deploying to Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub and select **Create app**.
3. Choose the repository and branch, and set the app file path to `app.py` (the project root).
4. Select **Deploy**. Streamlit installs the dependencies from `requirements.txt`.

The app does not require secrets or external services. Do not commit `.streamlit/secrets.toml` or other credentials; the repository's `.gitignore` excludes local Streamlit secrets and virtual environments.

## Using the application

1. Open the **Compare** view.
2. Select a source for Document A and Document B:
   - **Sample library** loads one of the bundled `.txt` examples.
   - **Paste or write text** opens an editor for direct text entry.
   - **Upload a document** accepts `.txt` or `.pdf`.
3. Check that both document cards show matchable text.
4. Choose the minimum match length in the sidebar. The default is `20` normalized characters.
5. Select **Analyze text overlap**.
6. Review both coverage directions, the overall similarity, highlighted text, and matched passage positions.
7. Use the CSV download to save matched passages when available.

Use **Batch review** to compare multiple documents, **Benchmark** to run the generated performance experiment, and **Method guide** to review how results are produced. The **Dark appearance** toggle is in the sidebar.

### Input notes

- Uploaded text files are decoded as UTF-8, replacing invalid byte sequences where needed.
- PDF files are read with `pypdf`; only extractable/selectable text is analyzed. Scanned image-only PDFs need OCR, which is not included.
- If two uploaded documents have the same filename in batch review, the app assigns a suffix to keep them distinct.
- Files are compared by their extracted or entered text. The application does not query an online database or external search engine.

## Command-line usage

The core module can compare two UTF-8 text files without launching Streamlit:

```bash
python plagiarism_core.py samples/original.txt samples/copied_partial.txt -k 20
```

Arguments:

| Argument | Description                                                             |
| -------- | ----------------------------------------------------------------------- |
| `file_a` | Path to the first text file.                                            |
| `file_b` | Path to the second text file.                                           |
| `-k`     | Minimum consecutive normalized character match length; default is `20`. |

The command prints the verdict, directional coverage, technical statistics, and up to ten matching passages.

## Tests

Run the core unit tests from the project directory:

```bash
python -m unittest discover -s tests -v
```

The test suite checks normalization and original-position mapping, rolling-hash correctness, agreement between Rabin–Karp and naive matching, collision verification, identical/partial/unrelated documents, punctuation and case handling, short input behavior, and HTML escaping in highlights.

## Limitations

- Detects exact normalized character sequences only; it does not detect paraphrasing, synonyms, translation, or semantic similarity.
- Does not search the internet, journals, student repositories, or other external collections.
- Does not identify an author or establish intent or misconduct.
- Small `k` values can include coincidental matches; large values may miss shorter copied passages.
- Because spaces and punctuation are removed, the displayed matched span may include intervening formatting or punctuation from the original text.
- PDF extraction cannot read text embedded only in scanned page images.
- DOCX, image OCR, cloud storage, and external-source checking are not implemented.
- The naive method is intended as a small-scale benchmark; increasing document lengths can make it slow.

## Example experiments

Use the **Compare** view and sample library to try these cases with `k = 20`:

| Experiment                   | Suggested inputs                                           | Expected observation                                                                                     |
| ---------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Identical documents          | `original.txt` and `original.txt`                          | Nearly 100% coverage in both directions and a long matched passage.                                      |
| Partial copy                 | `original.txt` and `copied_partial.txt`                    | Several shared passages and moderate directional coverage.                                               |
| Unrelated documents          | `original.txt` and `unrelated.txt`                         | Very low similarity.                                                                                     |
| Match-length effect          | Repeat the partial-copy check with `k = 8`, `20`, and `50` | Shorter `k` can reveal shorter/common overlaps; longer `k` is more selective and may miss short matches. |
| Hash collision demonstration | Choose modulus `101` in advanced settings                  | Candidate collisions may occur; verification rejects unequal text, preserving match correctness.         |
| Algorithm benchmark          | Use the **Benchmark** view                                 | Compare timings and character comparisons for the generated document sizes.                              |

Exact scores and passage counts depend on the sample content and settings. The benchmark generates synthetic text; its timings are machine-dependent and should not be treated as universal performance guarantees.

## Frequently asked questions

**Why use Rabin–Karp?**  
Rolling hashes make it efficient to find candidate matching windows without comparing every possible window pair character by character. Candidates are still checked against the actual text.

**What is a spurious hash hit?**  
A collision: two different k-grams with the same hash. The detector verifies every hash candidate, so a collision is not reported as a matching passage.

**What does `k` control?**  
It is the minimum match length in normalized characters. Smaller values can find short overlaps but may be less selective. Larger values require longer exact sequences.

**Does a high score prove plagiarism?**  
No. The score measures normalized exact-text coverage only. Similarity needs contextual and human review.

## Author

**Rohit Khobare**  
Email: [rohitkhobare2005@gmail.com]
