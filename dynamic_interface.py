import streamlit as st
import importlib
import inspect
import pandas as pd
from io import StringIO
import yaml

def format_function_name(name):
    formatted = name.replace('_', ' ').title()
    formatted = formatted.replace('Sql', 'SQL').replace('Mongo Db', 'MongoDB')
    return formatted.replace('Db', 'DB')

def generate_dynamic_interface(module):
    st.markdown("""
    <style>
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stApp {
        background: linear-gradient(
            -45deg,
            rgba(98, 114, 164, 0.15),
            rgba(139, 233, 253, 0.15),
            rgba(255, 182, 193, 0.2), 
            rgba(80, 250, 123, 0.15),
            rgba(255, 121, 198, 0.15)
        );
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        backdrop-filter: blur(20px);
    }
    .stTextInput:hover, .stSelectbox:hover, .stButton:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    div.stButton > button {
        background: linear-gradient(45deg, rgba(139, 233, 253, 0.1), rgba(80, 250, 123, 0.1));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(45deg, rgba(139, 233, 253, 0.2), rgba(80, 250, 123, 0.2));
    }
    @keyframes buttonClick {
        0% { transform: scale(1); }
        50% { transform: scale(0.95); }
        100% { transform: scale(1); }
    }
    div.stButton > button:active {
        animation: buttonClick 0.2s ease;
    }
    </style>
    """, unsafe_allow_html=True)

    def render_config_section():
        st.sidebar.header("Database Configuration")
        config = module.load_config()
        
        with st.sidebar.expander("Database Settings", expanded=False):
            st.subheader("SQL Server")
            sql_config = {
                'driver': st.text_input('Driver', value=config['database']['driver'], key='sql_driver'),
                'server': st.text_input('Server', value=config['database']['server'], key='sql_server'),
                'database': st.text_input('Database', value=config['database']['database'], key='sql_db'),
                'uid': st.text_input('User ID', value=config['database']['uid'], key='sql_uid'),
                'pwd': st.text_input('Password', value=config['database']['pwd'], type='password', key='sql_pwd')
            }
            
            st.subheader("MongoDB")
            mongo_server = st.text_input('MongoDB URL', value=config['mongo']['server'], key='mongo_server')
            
            if st.button("Save Configuration", key="save_config"):
                new_config = {
                    'database': sql_config,
                    'mongo': {'server': mongo_server}
                }
                try:
                    with open("appconfig.yaml", "w") as file:
                        yaml.dump(new_config, file)
                    st.success("Configuration saved successfully!")
                except Exception as e:
                    st.error(f"Error saving configuration: {e}")

    render_config_section()

    functions = [obj for name, obj in inspect.getmembers(module) 
                if inspect.isfunction(obj) and obj.__module__ == module.__name__]
    
    function_map = {
        func.__name__: format_function_name(func.__name__)
        for func in functions
    }

    selected_display = st.selectbox(
        "Select Operation",
        options=list(function_map.values())
    )
    selected_function = next(
        k for k, v in function_map.items() 
        if v == selected_display
    )
    func = next(f for f in functions if f.__name__ == selected_function)
    
    sig = inspect.signature(func)
    params = {}
    for name, param in sig.parameters.items():
     if name == 'cursor':
        conn = module.create_sql_connection()
        params[name] = conn.cursor()
        params['_connection'] = conn
     elif name == 'collection':
        params[name] = module.create_mongo_connection()
     elif name == 'record_id':
        params[name] = st.text_input("Enter Record ID")
     elif name == 'data':
        input_method = st.radio("Input method", 
                              ["Text Input", "CSV Upload"], 
                              key=f"{name}_input_method")
        
        if input_method == "Text Input":
            user_input = st.text_area("Paste container numbers (one per line)")
            params[name] = [line.strip() for line in StringIO(user_input) if line.strip()]
        else:
            uploaded_file = st.file_uploader("Upload CSV file", 
                                           type=["csv"], 
                                           key=f"{name}_csv_upload")
            data = []
            if uploaded_file is not None:
                has_header = st.checkbox("CSV contains header row", 
                                       key=f"{name}_csv_header")
                df = pd.read_csv(uploaded_file, header=0 if has_header else None)
                if not df.empty:
                    data = df.iloc[:, 0].astype(str).tolist()
                    st.success(f"Loaded {len(data)} items from CSV")
                else:
                    st.warning("Uploaded CSV file is empty")
            params[name] = data
     elif name == 'rf':
        params[name] = []

    if st.button(f"🔄 Execute {selected_display}"):
        try:
            with st.spinner("Processing..."):
                result = func(**params)
                
            if isinstance(result, (list, pd.DataFrame)):
                st.dataframe(result if isinstance(result, pd.DataFrame) else pd.DataFrame(result))
            else:
                st.success(str(result))
            
            if '_connection' in params:
                params['_connection'].commit()
                params['_connection'].close()
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            if '_connection' in params:
                params['_connection'].rollback()
                params['_connection'].close()

def main():
    module = importlib.import_module("original")
    st.title("PyDance")
    generate_dynamic_interface(module)

if __name__ == "__main__":
    main()
