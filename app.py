import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="NOON Template Filler", layout="wide")

st.title("NOON Information Sheet Generator")
st.write("Upload your source data and the NOON Information sheet template to map columns and generate the final file.")

# File uploaders
col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("1. Upload Source Data (Excel/CSV)", type=["csv", "xlsx"])
with col2:
    template_file = st.file_uploader("2. Upload NOON Template (Excel/CSV)", type=["csv", "xlsx"])

if source_file and template_file:
    # Function to read files based on extension
    @st.cache_data
    def load_data(file):
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)

    try:
        df_source = load_data(source_file)
        df_template = load_data(template_file)
        
        template_headers = list(df_template.columns)
        source_headers = list(df_source.columns)
        
        st.divider()
        st.subheader("Column Mapping")
        st.write("Match the headers from your source data to the corresponding NOON template headers. The app will auto-match headers with the exact same name.")
        
        # Dictionary to store user's mapping choices
        mapping = {}
        
        # Option to leave a column empty if no source data matches
        source_options = ["--- Leave Empty ---"] + source_headers
        
        # Create a selectbox for every header in the template
        for header in template_headers:
            # Auto-select the column if the names match exactly
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
                
        # Generate the final file
        if st.button("Generate NOON Sheet", type="primary"):
            # Create an empty dataframe with the NOON template headers
            df_final = pd.DataFrame(columns=template_headers)
            
            # Fill in the data based on the mapping
            for temp_col, source_col in mapping.items():
                if source_col:  # If a column was mapped
                    df_final[temp_col] = df_source[source_col]
            
            st.success("Data mapped successfully! Preview below:")
            st.dataframe(df_final.head(10)) # Show preview
            
            # Convert final dataframe to an Excel file in memory for download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='NOON Info')
            
            st.download_button(
                label="📥 Download Filled NOON Sheet",
                data=buffer.getvalue(),
                file_name="Filled_NOON_Information_Sheet.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"An error occurred while processing the files: {e}")