# Setup Instructions

1. **Download the Project**
   - Clone the repository or download the project folder from:
     (https://github.com/dsagher/Reconciliation-Project)

2. **Prepare the Directory Structure**
Input and output folders must be structured as follows:
```
.
└── Reconciliation Project/
    ├── input_files/
    │   ├── customers/
    │   │   ├── customer1
    │   │   ├── customer2
    │   │   └── customer3
    │   ├── invoice_data
    │   └── qbo
    ├── output_files/
    │   └── output_excel_file
    ├── scripts/
    │   ├── main.py
    │   ├── file_io.py
    │   ├── pattern_match.py
    │   ├── processing.py
    │   └── io_tests.py
    ├── instructions.txt
    ├── requirements.txt
    ├── README.md
    └── .gitignore
```
3. **Install Requirements**
   Choose one of the following options to install the project dependencies:

   - **Option A: Use a Virtual Environment (Recommended)**
     1. While cd'd into the project folder, create and activate a virtual environment:
        - Linux/macOS:
          ```bash
          python -m venv venv
          source venv/bin/activate
          ```
        - Windows:
          ```Powershell
          python -m venv venv
          venv\Scripts\activate
          ```
     2. Install the required packages:
        ```bash
        pip install -r requirements.txt
        ```

   - **Option B: Install Requirements Globally**
     - Run the following command to install the dependencies globally:
       ```bash
       pip install -r path/to/folder/requirements.txt
       ```
4. **Run the Program**:
   This script handles input files, processes data, and generates output in the `output_files/` folder.
   Creates 'output_files/' folder if doesn't exist.

    1. Change directory to project folder
        ```bash
        cd path/to/folder
        ```
    2. Execute the `main.py` script to start the program.
        ```bash
        python scripts/main.py
        ```
