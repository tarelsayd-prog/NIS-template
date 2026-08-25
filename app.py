import streamlit as st
import pandas as pd
import openpyxl
import io

st.set_page_config(page_title="NOON Template Filler", layout="wide")

st.title("NOON Information Sheet Generator")
st.write("Upload your source data and the NOON template. The app will preserve all formatting and hidden rows.")

col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("1. Upload Source Data (Excel/CSV)", type=["csv", "xlsx"])
with col2:
    # Template must be Excel to contain hidden rows/formatting
    template_file = st.file_uploader("2. Upload NOON Template (Excel ONLY)", type=["xlsx"])

if source_file and template_file:
    try:
        # 1. Load the source data
        if source_file.name.endswith('.csv'):
            df_source = pd.read_csv(source_file)
        else:
            df_source = pd.read_excel(source_file)
            
        source_headers = list(df_source.columns)

        # 2. Load the NOON template using openpyxl to KEEP formatting
        wb = openpyxl.load_workbook(template_file)
        sheet = wb.active # Assumes you want to fill the first sheet
        
        # 3. Extract headers exactly from Row 8
        template_headers = []
        header_col_map = {} # Remembers which column letter each header belongs to
        
        for cell in sheet[8]: # openpyxl is 1-indexed, so 8 is row 8
            if cell.value:
                header_name = str(cell.value).strip()
                template_headers.append(header_name)
                header_col_map[header_name] = cell.column

        if not template_headers:
            st.error("Could not find any headers in Row 8 of the template.")
            st.stop()

        st.divider()
        st.subheader("Column Mapping")
        st.write("Headers extracted from **Row 8**. Data will be inserted starting at **Row 10** (preserving hidden row 9).")
        
        mapping = {}
        source_options = ["--- Leave Empty ---"] + source_headers
        
        # Create mapping interface
        for header in template_headers:
            default_index = 0
            if header in source_headers:
                default_index = source_options.index(header)
                
            selected_col = st.selectbox(
                f"NOON Template Header: **{header}**", 
                options=source_options, 
                index=default_index
            )
            
            if selected_col != "--- Leave Empty ---":
                mapping[header] = selected_col
            else:
                mapping[header] = None

        # 4. Generate the final file
        if st.button("Generate NOON Sheet", type="primary"):
            
            # Start writing data at row 10
            start_row = 10
            
            # Iterate through source data and write directly into the template cells
            for index, row_data in df_source.iterrows():
                current_row = start_row + index
                
                for temp_header, source_col in mapping.items():
                    if source_col: 
                        # Get the exact column index for this header
                        col_idx = header_col_map[temp_header]
                        
                        # Write the data into the cell
                        val = row_data[source_col]
                        # Handle pandas NaNs/nulls so they write as blank cells
                        if pd.isna(val):
                            val = ""
                            
                        sheet.cell(row=current_row, column=col_idx, value=val)
            
            st.success("Data injected successfully! All formatting and hidden rows are preserved.")
            
            # Save the modified template into memory
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            st.download_button(
                label="📥 Download Filled NOON Sheet",
                data=buffer.getvalue(),
                file_name="Filled_NOON_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"An error occurred: {e}")
