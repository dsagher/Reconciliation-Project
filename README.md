# Reconciliation-Project

## Overview

The **Reconciliation Project** is a Python-based tool for reconciling invoice data with QuickBooks Online (QBO) data and customer information stored in Extensiv tables. It is designed to streamline the comparison and matching process, enabling users to identify discrepancies and create a consolidated output file.

---

## Features

- **Input Data Validation:** Ensures required files and folders are present in the input directory.
- **Automated Data Matching:**
  - Matches invoice data against QBO records using `Customer PO #` and `Display_Name`.
  - Compares reference and receiver information from invoice data against Extensiv customer data.
- **Error Handling:** Provides detailed feedback on missing files, invalid formats, or unmatched data.
- **Custom Pattern Matching:** Uses regular expressions to create patterns for matching invoice references.
- **Flexible Output:** Generates an Excel file summarizing reconciled data.

---

## Planned Improvements

- **Flexibility for File Type IO:** Add functionality to support additional input file types such as `.csv` for broader compatibility.
- **Code Optimization:**
  - Utilize modular helper functions to reduce redundancy and improve code readability.
  - Consolidate repetitive code patterns into reusable components.
- **Performance Enhancements:**
  - Rewrite pattern-matching functions to leverage vectorized Pandas operations instead of nested loops for greater efficiency.
  - Optimize processing of large datasets to minimize runtime and memory usage.

