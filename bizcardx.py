import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import sqlite3

mydb = sqlite3.connect('bizcard.db')
cursor=mydb.cursor()

st.set_page_config(page_title="Bizcard Extraction", page_icon=":anchor:", layout="wide", menu_items=None)

select= option_menu(menu_title=None,
                    options = ["Home","Uplode","Modify","Delete"],
                    default_index=0,
                    orientation="horizontal",
                    styles={
            "container": {"padding": "0!important", "background-color": "white","size":"cover"},
            "nav-link": {"font-size": "20px", "text-align": "center", "margin": "-2px", "--hover-color": "purple"},
            "nav-link-selected": {"background-color": "purple"}
        } )


if select == "Home":
  st.title(':blue[Business card data extraction using OCR] ')

  st.write("### :blue[Introduction]")
  description = """EasyOCR is a Python computer language Optical Character Recognition (OCR) module that is both flexible and easy to use.
                            OCR technology is useful for a variety of tasks, including data entry automation and image analysis.
                            It enables computers to identify and extract text from photographs or scanned documents.
                            EasyOCR stands out for its dedication to making OCR implementation easier for developers.
                            It’s made to be user-friendly even for people with no background in OCR or computer vision.
                            Multiple language support, pre-trained text detection and identification models,
                            and a focus on speed and efficiency in word recognition inside images are all provided by the library."""
  ocr="""
          EasyOCR is a dependable option for Python developers because of its versatility in handling typefaces and text layouts, as well as its focus on accuracy and speed.
          EasyOCR simplifies the process of extracting text from photos for use in various Python projects,
          including desktop software, online applications, and others.
          This frees up your time to concentrate on the unique requirements of your product.
          """
  st.write(description)
  st.write(ocr)

if select == "Uplode":
    st.title(':blue[Business card data extraction using OCR] ')



    s_img = st.file_uploader("Upload Image",type =["png","jpg","jpeg"])


    def img_text(img_path):

      input = Image.open(img_path)
      img_arr= np.array(input)
      r= easyocr.Reader(['en'])
      t= r.readtext(img_arr,detail=0)

      return input,t


    def table_info(t2):

      table_dict={'Name':[], 'Designation':[], 'Contact_num':[], 'Email':[], 'Website':[], 'Address':[],'State':[],'Pincode':[],'Company':[]}
      table_dict['Name'].append(text[0])
      table_dict['Designation'].append(text[1])

      for i in range(2,len(t2)):

        if t2[i].startswith('+') or (t2[i].replace("-","").isdigit() and '-'in t2[i]):
          table_dict["Contact_num"].append(t2[i])
          if len(table_dict["Contact_num"]) == 2:
              table_dict["Contact_num"] = " & ".join(table_dict["Contact_num"])

        elif '@' in t2[i] and '.com' in t2[i]:
          table_dict["Email"].append(t2[i])


        elif 'www' in t2[i] or 'WWW' in t2[i] or '.com' in t2[i]:
          table_dict["Website"].append(t2[i].lower())


        elif 'TamilNadu' in t2[i] or 'Tamil Nadu' in t2[i] or t2[i].isdigit():
          if t2[i].isdigit():
              # Assuming state comes before pincode
              state = t2[i-1]
              pincode = t2[i]
          else:
              parts = t2[i].split()
              state = parts[0]
              pincode = parts[-1]

          table_dict["State"].append(state)
          table_dict["Pincode"].append(pincode)

        elif re.match(r'^[A-Z a-z]',t2[i]):
          table_dict["Company"].append(t2[i])

        else:
          rm_colon = re.sub(r'[,;]', '', t2[i])
          table_dict['Address'].append(rm_colon)

      for key,value in table_dict.items():
        if len(value)>0:
          concat= " ".join(value)
          table_dict[key] = [concat]

        else:
          val= "NA"
          table_dict[key] = [val]

      return table_dict

    if s_img is not None:
      st.image(s_img, width=500)

      img,text=img_text(s_img)

      text_dict = table_info(text)

      if text_dict:
        st.success("Data extracted successfully!!!")

      df=pd.DataFrame(text_dict)

      st.dataframe(df.T)

      button = st.button("Upload Data to sql")

      if button:

        # Define SQL query to check if data already exists
        check_existing_query = '''SELECT COUNT(*) FROM bizcard_tab WHERE name=? AND designation=? AND company_name=? AND contact=? AND email=? AND website=? AND state=? AND pincode=? AND address=?'''

        # Extract data to be inserted
        data_to_insert = df.values.tolist()[0]

        # Execute the query to check if the data already exists
        cursor.execute(check_existing_query, data_to_insert)
        existing_data_count = cursor.fetchone()[0]

        # If no existing data found, insert new data
        
        if existing_data_count == 0:  
            create_table = '''CREATE TABLE IF NOT EXISTS bizcard_tab(name VARCHAR(50), designation VARCHAR(50), company_name VARCHAR(50), contact VARCHAR(50), email VARCHAR(50),
                                                website VARCHAR(50), state VARCHAR(50), pincode VARCHAR(50), address TEXT)'''
            cursor.execute(create_table)
            mydb.commit()

            insert_q = '''INSERT INTO bizcard_tab(name, designation, company_name, contact, email, website, state, pincode, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            cursor.execute(insert_q, data_to_insert)
            mydb.commit()

            st.success("Data Uploaded to SQL", icon="✅")
            st.snow()
        else:
            st.warning("Data already exists",icon="⚠️")


if select == "Modify":

  st.title(":blue[Database]")

  cursor.execute('select * from bizcard_tab')
  tab = pd.DataFrame(cursor.fetchall(),columns=("Name","Designation","Contact","Email","Website","Address","State","Pincode","Company"))
  mydb.commit()

  st.dataframe(tab)

  col1,col2 = st.columns(2)

  st.title(":blue[Modify the data]")
  with col1:
    slt_name=st.selectbox("Select Name for modification",tab["Name"])

  df_tab = tab[tab["Name"] == slt_name]

  df_cpy= df_tab.copy()

  col3,col4 = st.columns(2)
  with col3:
    name = st.text_input("Name",df_tab["Name"].unique()[0])
    Des = st.text_input("Designation",df_tab["Designation"].unique()[0])
    con = st.text_input("Contact",df_tab["Contact"].unique()[0])
    email = st.text_input("Email",df_tab["Email"].unique()[0])
    website = st.text_input("Website",df_tab["Website"].unique()[0])

    df_cpy["Name"] = name
    df_cpy["Designation"] = Des
    df_cpy["Contact"] = con
    df_cpy["Email"] = email
    df_cpy["Website"] = website

  with col4:

    address = st.text_input("Address",df_tab["Address"].unique()[0])
    state = st.text_input("State",df_tab["State"].unique()[0])
    pincode = st.text_input("Pincode",df_tab["Pincode"].unique()[0])
    company = st.text_input("Company_name",df_tab["Company"].unique()[0])

    df_cpy["Address"] = address
    df_cpy["State"] = state
    df_cpy["Pincode"] = pincode
    df_cpy["Company"] = company

  col5,col6 = st.columns(2)
  with col5:
    submit = st.button("Click to Modify the above details")

  st.title(":blue[Data after changes]")

  st.dataframe(df_cpy)

  if submit:

    cursor.execute(f"Delete from bizcard_tab where name = '{slt_name}'")

    insert_q = '''Insert into bizcard_tab(name, designation, company_name, contact, email, website, state, pincode, address) values(?,?,?,?,?,?,?,?,?)'''

    data1 = df_cpy.values.tolist()[0]
    cursor.execute(insert_q, data1)
    mydb.commit()

    st.success("Data Modified!!!")

if select == "Delete":

  cl1,cl2 = st.columns(2)
  with cl1:
    cursor.execute("Select name from bizcard_tab")
    tab1 = cursor.fetchall()
    names = []

    for i in tab1:
      names.append(i[0])
    select_name = st.selectbox("Select the name",names)

    cursor.execute(f"Select designation from bizcard_tab where name ='{select_name}'")
    tab2 = cursor.fetchall()
    des = []

    for j in tab2:
      des.append(j[0])

    cursor.execute(f"Select address from bizcard_tab where name ='{select_name}'")
    tab3 = cursor.fetchall()
    cmpny =[]

    for k in tab3:
      cmpny.append(k[0])

  if select_name:
    cl3,cl4,cl5 = st.columns(3)

    with cl3:
      st.write(f"Name : {select_name}")
      st.write(f"Designation : {des[0]}")
      st.write(f"Company : {cmpny[0]}")

    remove=st.button("Delete Data from Database")

    if remove:
      cursor.execute(f"Delete from bizcard_tab where name = '{select_name}'")
      mydb.commit()

      st.warning("Data Deleted Successfully!!!",icon="✅")
