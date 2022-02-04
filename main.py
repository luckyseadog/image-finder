import streamlit as st
from PIL import Image
import random
import pandas as pd
import abc
import torch
import ruclip
import clip
import numpy as np
from numbers import Number
from typing import List
import os
import glob
import math
from pathlib import Path
import regex as re

from searchmodel import SearchModel
from embedder import EmbedderRuCLIP, EmbedderCLIP
from dummyindexer import DummyIndexer

st.set_page_config(page_title="Image Finder",
                   page_icon='⚙',
                   layout="centered",
                   initial_sidebar_state="expanded",
                   menu_items=None)

with st.expander("About"):
    st.text("""
        This is project explanation
    """)

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def load_model():
	#CLIP
	clip_model = SearchModel(EmbedderCLIP(device='cpu'), DummyIndexer())
	#ruCLIP
	ruclip_model = SearchModel(EmbedderRuCLIP(device='cpu'), DummyIndexer())
	return clip_model, ruclip_model

clip_model, ruclip_model = load_model()

#Functions
def function_images(input_format):
    data = []
    
    input_format = dict(sorted(input_format.items(), key=lambda item: item[1], reverse=True))

    col1, col2 = st.columns([1, 1])
    count = 0
    for i in input_format.items():
        if i[1] >= threshold / 100:
            count += 1
            df = pd.DataFrame()
            data.append([i[0].split('/')[len(i[0].split('/'))-1], i[1]])
            df = df.append(data)
            df = df.rename(columns={0: "Image", 1: "Cosine distance"})

    if count == 0:
        st.info(f"No images for {threshold} or above cosine distance, %")
    else:
        for _, i in enumerate(input_format.items(), 1):
            with col1:
                if i[1] >= threshold / 100:
                    image = Image.open(i[0])
                    st.image(image, caption=f"{i[0].split('/')[len(i[0].split('/'))-1]}, {i[1]}")
            with col2:
                if _ == 1:
                    st.write("Output cosine distance")
                    st.dataframe(df.style.text_gradient(axis=0, cmap='Spectral'))

st.image(Image.open('assets/logo.png'))
indexer = st.sidebar.selectbox(
    "Select indexer",
    ("Variant1", "Variant2")
)

dict_indexer = {'Variant1':'stl10', 'Variant2':'film'}

st.title('Project')
st.caption(f"Current indexer: {indexer}")
option = st.selectbox(
    'What would you like to do?',
     ('Text query', 'Image')
)
#Text query
if option == 'Text query':
    text = st.text_input('Input text query', '')
else:
#Image
    file = st.file_uploader("Choose image", type=['jpeg', 'jpg', 'png'], accept_multiple_files=False)

values = st.slider('Select a range of sample images', 1, 10, 5)
threshold = st.slider('Select a threshold for output images, %', 1, 100, 25)

#Processing
if st.button('Process'):
    indexer_name = dict_indexer.get(indexer)
    if option == 'Text query' and text:
        st.write(f"Output images for text query: {text}")
        #function_images()
        general_model = None
        
        if re.findall(r'[а-яА-Я0-9]', text):
            general_model = ruclip_model
            general_model.load_imgs(f"/content/{indexer_name}/train_images",'RuCLIP')
        elif re.findall(r'[a-zA-Z0-9]', text):
            general_model = clip_model
            general_model.load_imgs(f"/content/{indexer_name}/train_images",'CLIP')
        else:
            st.info(f"Error in query: {text}")
        general_model.indexer.load(str(general_model.features_path) + '/features.npy')
        query = general_model.embedder.encode_text(text)
        input_data = general_model.get_k_imgs(query, values)
        input_format = {}
        
        for i,j in zip(input_data[0], input_data[1]):
            input_format.update({str(j):i})
        
        function_images(input_format)
        
    elif option == 'Image' and file is not None:
        clip_model.load_imgs(f"/content/{indexer_name}/train_images",'CLIP')
        clip_model.indexer.load(str(clip_model.features_path) + '/features.npy')
        image = Image.open(file)
        query = clip_model.embedder.encode_imgs([image])
        st.image(image, caption=file.name)
        st.write(f"Output images for current input image: {file.name}")
        
        input_data = clip_model.get_k_imgs(query, values)
        input_format = {}
        
        for i,j in zip(input_data[0], input_data[1]):
            input_format.update({str(j):i})
        
        function_images(input_format)
        
    else:
        st.info("Error")
