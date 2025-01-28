import streamlit as st
import ast
import os
import pandas as pd
import inspect

import subprocess

import time
def update_pydance(function_code, function_name):
    try:
        # Read the content of PyDance.py
        with open("PyDance.py", "r") as file:
            content = file.read()

        # Locate the main() function
        main_pos = content.find("def main():")
        if main_pos == -1:
            st.error("Could not find main() function!")
            return False

        # Add the new function definition above main()
        new_content = content[:main_pos] + "\n\n" + function_code + "\n\n" + content[main_pos:]

        # Locate the method_options dictionary
        dict_start = new_content.find("method_options = {")
        if dict_start == -1:
            st.error("Could not find method_options dictionary!")
            return False

        # Parse and modify the dictionary safely
        dict_end = new_content.find("}", dict_start)
        dict_code = new_content[dict_start:dict_end + 1]

        # Create an updated method_options dictionary
        display_name = function_name.replace("_", " ").title()
        if display_name in dict_code:
            st.error(f"{display_name} already exists in method_options!")
            return False

        updated_dict_code = dict_code[:-1] + f'    "{display_name}": {function_name},\n' + dict_code[-1:]
        new_content = new_content[:dict_start] + updated_dict_code + new_content[dict_end + 1:]

        # Dynamically generate the user interface code for the new function
        function_obj = compile(function_code, "<string>", "exec")
        local_vars = {}
        exec(function_obj, {}, local_vars)

        # Extract the function parameters and their defaults
        func = local_vars[function_name]
        sig = inspect.signature(func)
        input_fields = []
        parameter_casts = []

        for param_name, param in sig.parameters.items():
            # Determine the input type and set up appropriate casting
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            if param_type == int:
                input_fields.append(f"""
        {param_name} = st.number_input("{param_name} (int)", value=0, step=1)
                """)
            elif param_type == float:
                input_fields.append(f"""
        {param_name} = st.number_input("{param_name} (float)", value=0.0)
                """)
            else:
                input_fields.append(f"""
        {param_name} = st.text_input("{param_name} (str)", value="")
                """)
            parameter_casts.append(param_name)

        interface_code = f"""
    elif selected_method == "{display_name}":
        st.subheader("{display_name}")
        {"".join(input_fields)}
        
        if st.button("Run {display_name}"):
            try:
                result = {function_name}({', '.join(parameter_casts)})
                st.write("Result:", result)
            except Exception as e:
                st.error(f"Error running {function_name}: {{e}}")
"""
        main_end = new_content.find("if __name__ ==")
        new_content = new_content[:main_end] + interface_code + "\n" + new_content[main_end:]

        # Write the updated content back to PyDance.py
        with open("PyDance.py", "w") as file:
            file.write(new_content)

        return True

    except Exception as e:
        st.error(f"Error updating PyDance.py: {e}")
        return False

st.markdown("""
<style>
@keyframes gradient {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

.stApp {
    background: linear-gradient(
        -45deg,
        rgba(0, 0, 0, 1),
        rgba(227, 239, 106, 0.45),
        rgba(240, 210, 105, 0.45), 
        rgba(116, 240, 105, 0.55),
        rgba(234, 242, 145, 0.55)
    );
    background-size: 400% 400%;
    animation: gradient 15s ease infinite;
    backdrop-filter: blur(20px);
}


.stTextInput:hover, .stSelectbox:hover, .stButton:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

/* Custom styling for buttons */
div.stButton > button {
    background: linear-gradient(
        45deg,
        rgba(240, 196, 120, 0.1),
        rgba(240, 136, 120, 0.1)
    );
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
}

div.stButton > button:hover {
    background: linear-gradient(
        45deg,
        rgba(240, 196, 120, 0.2),
        rgba(240, 136, 120, 0.2)
    );
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}


/* Animation for button clicks */
@keyframes buttonClick {
    0% { transform: scale(1); }
    50% { transform: scale(0.95); }
    100% { transform: scale(1); }
}

div.stButton > button:active {
    animation: buttonClick 0.2s ease;
}

/* Custom styling for sidebar */
.css-1d391kg {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
}

/* Improved input field styling */
input[type="text"], input[type="password"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    padding: 10px !important;
    color: #ffffff !important;
}

/* Delete field button adjustments */
.delete-button-col {
    margin-top: -40px !important;  /* Adjust this value to move buttons up */
}

</style>
""", unsafe_allow_html=True)


def main():
    st.title("PyDance Function Generator")

    # Input area for the function code
    function_code = st.text_area("Paste your function code here:", height=300)

    # Buttons for adding function and running PyDance.py
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Add Function"):
            if not function_code:
                st.error("Please provide function code!")
                return

            try:
                # Extract function name
                tree = ast.parse(function_code)
                function_name = tree.body[0].name

                if update_pydance(function_code, function_name):
                    st.success(f"Function '{function_name}' added successfully!")
                    st.info("Restart PyDance.py to see changes")

            except Exception as e:
                st.error(f"Error parsing function: {e}")

    with col2:
        if st.button("Run PyDance.py"):
            try:
                # Launch the command to run PyDance.py
                file_path = os.path.abspath("PyDance.py")
                subprocess.Popen(["streamlit", "run", file_path], shell=True)
                st.success("Launching PyDance.py...")
            except Exception as e:
                st.error(f"Error launching PyDance.py: {e}")


if __name__ == "__main__":
    main()
