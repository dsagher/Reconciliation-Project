# Reconciliation-Project

## Overview

The **Reconciliation Project** is a Python-based tool for reconciling invoice data with QuickBooks Online (QBO) data and customer information stored in Extensiv tables. It is designed to streamline the comparison and matching process, enabling users to identify discrepancies and create a consolidated output file.

---

## Features
- **Flexible Input:** Compatible with Excel and CSV files. 
- **Input Data Validation:** Ensures required files and folders are present in the input directory.
- **Automated Data Matching:**
  - Matches invoice data against QBO records.
  - Compares reference and receiver information from invoice data against Extensiv customer data.
- **Modular Keys:** Flexible keys allowing for scaling with more lookup values.
- **Error Handling:** Provides detailed feedback on missing files or invalid formats.
- **Custom Pattern Matching:** Uses regular expressions to create patterns for matching invoice references.
- **User-Friendly Output:** Generates an Excel file summarizing reconciled data.

---