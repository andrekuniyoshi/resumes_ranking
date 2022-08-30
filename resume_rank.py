# -*- coding: utf-8 -*-
"""Untitled21.ipynb
Automatically generated by Colaboratory.
Original file is located at
    https://colab.research.google.com/drive/1rRdcV7pQeq4hU6ajCYLaKyIbT3TgKoiv
"""
# importing data manipulation libs
import pandas as pd
import numpy as np

# importing visualization libs
import matplotlib.pyplot as plt
import seaborn as sns


# to read json file
import json

# gensim lib
import gensim

# for text processing
import re
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')

# for vectorizer
#from sklearn import feature_extraction, manifold
## for word embedding
import gensim.downloader as gensim_api
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
#from gensim.models import KeyedVectors

import streamlit as st
import sklearn
import pickle

# importing a pre-trained GloVe model
# nlp = gensim_api.load("glove-wiki-gigaword-300")

# -------------------------------------- Cabeçalho -------------------------------------------------------#

st.set_page_config(
    page_title="Summ.link Challenge",
    page_icon="📰",
)

st.title("Summ.link's resumés matching score")
st.header("")

with st.expander("ℹ️ - About this app", expanded=False):
	st.write(
        """     
	-   This analysis is part of the technical challenge of Summ.Link application process
	-   To evaluate the candidate`s capability of handling data structures, uncertainty, similarity metrics and text pre-processing.
	-   The challenge is about ranking resumes for a specific job description based on the matching content of both sides.
	-   Author: Andre Kuniyoshi
	    """
	)
	st.markdown("")

# -------------------------------------------------------------------------------------------------------------------------------#
#model = pickle.load(open('stock_pred.pkl','rb'))
         # loading the trained model
#pickle_in = open("stock_pred3.pkl", "rb") 
#model = pickle.load(pickle_in)

# ---------------------------------------------Functions-----------------------------------------------------#
def create_str_from_dict(dict_file):
  '''
  This function joins all values of a dict into a single string
  '''
  tags = []                                                 # create a list
  for tag in dict_file:
      tags.append(tag)                                      # create a list of all dict's attributes

  job_description = []                                      # create a list to insert the values from dict
  for tag in tags:                                          # loop for every attribute
    if type(dict_file[tag])==str:                           # if the value is already a str
      job_description.append(dict_file[tag])                # get the value
    elif type(dict_file[tag])==dict:                        # if it's another dict
      for item in dict_file[tag]:                           # loop for all attributes
        job_description.append(dict_file[tag][item])        # get the value
    else:                                                   # if it's not str nor dict (maybe a list)
      for i in range(len(dict_file[tag])):                  # loop for all items in the list
        for item in dict_file[tag][i]:                      # loop for all attributes in the dict
          job_description.append(dict_file[tag][i][item])   # get the value
  
  job_description_str = ' '.join(job_description)           # concatenate all values in the list
  return job_description_str

def get_positions(df,col):
  '''
  Given a series of float values, this function ranks them, from
  the higher to the lower. The higher gets the rank 1.
  '''
  positions = []
  for i in range(len(df)):
    positions.append(df[col].sort_values(ascending=False).\
                     reset_index(drop=True)[df[col].\
                     sort_values(ascending=False).\
                     reset_index(drop=True)==df[col][i]].index[0]+1)

  return positions

def transform_similars2(txt1, txt2):
  '''
  This function gets 2 vectors of strings and transforms words in
  vector2 in words of vector1, in case they are similar.
  The similarity is calculated by cosine_similarity and a pre-trained
  model ("glove-wiki-gigaword-300"). If similarity >= 0.6, the word1 is
  replaced by word2.
  In our case, txt1=resume and txt2=job_description
  '''

  count_mod = 0                                                     # count the words modified
  i=0                                                               # check the position of word2 in txt2    
  for word1 in txt1:                                                # loop for all the words in list txt1
    for word2 in txt2:                                              # loop for all the words in list txt2
      try:
        if cosine_similarity([nlp[word1]],[nlp[word2]])[0][0]>=0.6: # compares the similarity of two words (continue if >=0.6)
          txt1[i]=word2
          count_mod += 1
          break                                                     # if found a similar word, goes to the next word 
      except:
        pass
    i += 1
  return txt1, count_mod

def utils_preprocess_text(text, flg_stemm=False, flg_lemm=True, lst_stopwords=None):
    '''
    Preprocess a string.
    :parameter
        :param text: string - name of column containing text
        :param lst_stopwords: list - list of stopwords to remove
        :param flg_stemm: bool - whether stemming is to be applied
        :param flg_lemm: bool - whether lemmitisation is to be applied
    :return
        cleaned text
    '''

    ## clean (convert to lowercase and remove punctuations and characters and then strip)
    text = re.sub(r'[^\w\s]', '', str(text).lower().strip())
            
    ## Tokenize (convert from string to list)
    lst_text = text.split()
    ## remove Stopwords
    if lst_stopwords is not None:
        lst_text = [word for word in lst_text if word not in 
                    lst_stopwords]
        chars = ["a","w"]
        pattern = "[{}]{{2,}}".format("".join(chars))
        lst_text = [word for word in lst_text if not re.search(pattern, word)]
                
    ## Stemming (remove -ing, -ly, ...)
    if flg_stemm == True:
        ps = nltk.stem.porter.PorterStemmer()
        lst_text = [ps.stem(word) for word in lst_text]
                
    ## Lemmatisation (convert the word into root word)
    if flg_lemm == True:
        lem = nltk.stem.wordnet.WordNetLemmatizer()
        lst_text = [lem.lemmatize(word) for word in lst_text]
            
    ## back to string from list
    text = " ".join(lst_text)
    return text


# ---------------------------------------------Uploading files-----------------------------------------------------#
st.subheader('Load Files')

col1, col2, col3 = st.columns([1,1,1])
with col1:
	uploaded_job_desc = st.file_uploader("Choose Job Description file (json)")
	if uploaded_job_desc is not None:
		# reading job description file (json)
# 		df_job_desc = open(uploaded_job_desc)  	# opening job description file
		df_job_desc = json.load(uploaded_job_desc)	# reading the file
		df_job_desc = df_job_desc[0]		# once df_job_desc was in a list
# 		st.dataframe(df_job_desc)
	
with col2:
	uploaded_resume = st.file_uploader("Choose a resumes file (csv")
	if uploaded_resume is not None:
		# reading resumes
		df_resumes = pd.read_csv(uploaded_resume)
# 		st.dataframe(df_resumes)
		
with col3:
	method = st.radio(
		"Choose preprocessing method",
		('Clean_resumes', 'Clean_Transformed_Resumes'))

# -------------------------------------------------------------------------------------------------------------------------------#
st.subheader('"Must Have" experiences')

col4, col5, col6 = st.columns([1,1,1])

with col4:
	mh_1 = st.text_input('Must have 1', '')
with col5:
	mh_2 = st.text_input('Must have 2', '')
with col6:
	mh_3 = st.text_input('Must have 3', '')


# -------------------------------------------------------------------------------------------------------------------------------#
if st.button('Click to see the ranking'):

	# from the job description I defined these 3 must have expressions
	must_haves = []
	must_haves.append(mh_1)
	must_haves.append(mh_2)
	must_haves.append(mh_3)
	
# -------------------------------------------------------------------------------------------------------------------------------#

# ---------------------------------------------Cleaning Job Description-----------------------------------------------------#
	# creating the stop words list
	lst_stopwords = stopwords.words('english')

	add_stop_words = ['62d1605026380b51d3762637'] # adding this string present in the job description
	for word in add_stop_words:
	  lst_stopwords.append(word)

	# concatenating all values of job description
	# into one variable
	job_description_str = create_str_from_dict(df_job_desc)

	# applying the transformation in the job description string
	# for that I'm using the lemamtisation and the list of stop words just created
	txt = job_description_str
	txt = utils_preprocess_text(txt, flg_stemm=False, flg_lemm=True, lst_stopwords=lst_stopwords)
	
	
# ------------------------------------------------------------------------------------------------------------------#
# ---------------------------------------------Cleaning resumes-----------------------------------------------------#
# 	# creating a list of clean resumes
# 	txt_resume_clean = []
# 	for i in range(len(df_resumes)):
# 	  txt_resume = df_resumes[' resume_text'][i]
# 	  txt_resume = utils_preprocess_text(txt_resume, flg_stemm=False, flg_lemm=True, lst_stopwords=lst_stopwords)
# 	  txt_resume_clean.append(txt_resume)

	
	if method == 'Clean_resumes':
		# creating a list of clean resumes
		txt_resume_clean = []
		for i in range(len(df_resumes)):
			txt_resume = df_resumes[' resume_text'][i]
			txt_resume = utils_preprocess_text(txt_resume, flg_stemm=False, flg_lemm=True, lst_stopwords=lst_stopwords)
			txt_resume_clean.append(txt_resume)

		df_resumes_copy = df_resumes.copy()
		df_resumes_copy['resume_clean'] = txt_resume_clean
		


# 	# ---------------------------------------------cosine similarity-----------------------------------------------------#

		word_vectorizer = TfidfVectorizer()

		percentages = []
		for i in range(len(df_resumes)):                                          # loop for all resumes

		  text_list = [df_resumes_copy['resume_clean'][i], txt]
		  count_matrix = word_vectorizer.fit_transform(text_list)                 # getting tokens and frequencies

		  # get the match percentage
		  matchPercentage = round(cosine_similarity(count_matrix)[0][1] * 100, 2) # applying cosine similarity
		  percentages.append(matchPercentage)
		

		
		
		df_resumes_copy['percentages_Tfid_Transformed'] = percentages

		df_resumes_pts = df_resumes_copy[['id', 'percentages_Tfid_Transformed']]
		# for each must have expression
		j = 0
		for must_have in must_haves:
		  #breakpoint = 0

			m_have = []                                               # creating a list to keep values 0 or 100
			must_have_len = len(must_haves[j].split())                # getting the length of the expressions
			#if must_have_len == 0:

			if must_have_len == 1:
				for i in range(len(df_resumes_copy)):                        # running for all resumes
					resume = df_resumes_copy['resume_clean_transformed'][i]    
					coun_vect = CountVectorizer(ngram_range=(1, 1))       # creating values of 1 string
					count_matrix = coun_vect.fit_transform([resume])      
					list_1grams_resume = coun_vect.get_feature_names()    # list of values from resume

					if pd.Series(must_have).isin(list_1grams_resume)[0]:  # in the case the must_have exists in the resume list
						m_have.append(100)                                  # add value of 100
					else:
						m_have.append(0)                                    # else, keep the value 0
				df_resumes_pts[must_have] = m_have                          # create a column of 0 and 100 in df_resumes

			elif must_have_len == 2:
				for i in range(len(df_resumes_copy)):                        # running for all resumes
					resume = df_resumes_copy['resume_clean_transformed'][i]    
					coun_vect = CountVectorizer(ngram_range=(2, 2))       # creating values of 2 strings (2grams)
					count_matrix = coun_vect.fit_transform([resume])      
					list_2grams_resume = coun_vect.get_feature_names()    # list of 2grams values from resume

					if pd.Series(must_have).isin(list_2grams_resume)[0]:  # in the case the must_have exists in the resume list of 2 grams
						m_have.append(100)                                  # add value of 100
					else:
						m_have.append(0)                                    # else, keep the value 0
				df_resumes_pts[must_have] = m_have                          # create a column of 0 and 100 in df_resumes

			elif must_have_len == 3:
				for i in range(len(df_resumes_copy)):                          # running for all resumes
					resume = df_resumes_copy['resume_clean_transformed'][i]    
					coun_vect = CountVectorizer(ngram_range=(3, 3))       # creating values of 3 strings (3grams)
					count_matrix = coun_vect.fit_transform([resume])      
					list_3grams_resume = coun_vect.get_feature_names()    # list of 3grams values from resume

					if pd.Series(must_have).isin(list_3grams_resume)[0]:  # in the case the must_have exists in the resume list of 3 grams
						m_have.append(100)                                  # add value of 100
					else:
						m_have.append(0)                                    # else, keep the value 0
				df_resumes_pts[must_have] = m_have                          # create a column of 0 and 100 in df_resumes

			elif must_have_len > 3:
				df_resumes_pts = df_resumes_copy[['id', 'percentages_Count_Transformed', 'percentages_Tfid_Transformed']]
				print('Your must have expressions should have max 3 words')
				break
			j += 1

		df_resumes_final_ranking = df_resumes_pts[['id', 'percentages_Tfid_Transformed', 'business analyst', 'business process', 'stakeholder management']]
		df_resumes_final_ranking['final_score'] = df_resumes_final_ranking['percentages_Tfid_Transformed']+\
							  df_resumes_final_ranking['business analyst']+\
							  df_resumes_final_ranking['business process']+\
							  df_resumes_final_ranking['stakeholder management']
		df_resumes_final_ranking['final_ranking'] = get_positions(df_resumes_final_ranking,'final_score')

		# the final dataframe
		df_ranking = df_resumes_final_ranking[['id','final_ranking']]
		
		st.write(percentages)
		st.write(df_ranking.sort_values('final_ranking', ascending=True))
	
# else:
# 	# creating a list of clean and transformed resumes (not only clean).
# 	# Let's get similarities between resumes words and job description words.
# 	# If similarity >= 0.6, the word in the resume is replaced by the word in the job description

# 	txt_resume_clean = []
# 	count_mods = []
# 	for i in range(len(df_resumes)):
# 	  txt_resume = df_resumes[' resume_text'][i]                                      # get the text from resumes
# 	  txt_resume = utils_preprocess_text(txt_resume, flg_stemm=False,
# 					     flg_lemm=True, lst_stopwords=lst_stopwords)  # cleaning the resumes strings

# 	  txt_split = txt.split()
# 	  txt_resume_split = txt_resume.split()
# 	  txt_resume_transformed, count_mod = transform_similars2(txt_resume_split,       # comparing and transforming by similarities
# 								  txt_split)
# 	  txt_resume_transformed = ' '.join(txt_resume_transformed)                       # transforming in a only string again

# 	  count_mods.append(count_mod)                                                    # counting the number of words transformed
# 	  txt_resume_clean.append(txt_resume_transformed)

# 	df_resumes_copy = df_resumes.copy()
# 	df_resumes_copy['resume_clean']
# # ---------------------------------------------cosine similarity-----------------------------------------------------#
		
# 	word_vectorizer = TfidfVectorizer()

# 	percentages = []
# 	for i in range(len(df_resumes)):                                          # loop for all resumes

# 	  text_list = [df_resumes_copy['resume_clean'][i], txt]
# 	  count_matrix = word_vectorizer.fit_transform(text_list)                 # getting tokens and frequencies

# 	  # get the match percentage
# 	  matchPercentage = round(cosine_similarity(count_matrix)[0][1] * 100, 2) # applying cosine similarity
# 	  percentages.append(matchPercentage)

# 	df_resumes_copy['percentages_Tfid_Transformed'] = percentages
		
# 	df_resumes_pts = df_resumes_copy[['id', 'percentages_Tfid_Transformed']]
# 	# for each must have expression
# 	j = 0
# 	for must_have in must_haves:
# 	  #breakpoint = 0

# 	  m_have = []                                               # creating a list to keep values 0 or 100
# 	  must_have_len = len(must_haves[j].split())                # getting the length of the expressions
# 	  #if must_have_len == 0:

# 	  if must_have_len == 1:
# 	    for i in range(len(df_resumes_copy)):                        # running for all resumes
# 	      resume = df_resumes_copy['resume_clean_transformed'][i]    
# 	      coun_vect = CountVectorizer(ngram_range=(1, 1))       # creating values of 1 string
# 	      count_matrix = coun_vect.fit_transform([resume])      
# 	      list_1grams_resume = coun_vect.get_feature_names()    # list of values from resume

# 	      if pd.Series(must_have).isin(list_1grams_resume)[0]:  # in the case the must_have exists in the resume list
# 		m_have.append(100)                                  # add value of 100
# 	      else:
# 		m_have.append(0)                                    # else, keep the value 0
# 	    df_resumes_pts[must_have] = m_have                          # create a column of 0 and 100 in df_resumes

# 	  elif must_have_len == 2:
# 	    for i in range(len(df_resumes_copy)):                        # running for all resumes
# 	      resume = df_resumes_copy['resume_clean_transformed'][i]    
# 	      coun_vect = CountVectorizer(ngram_range=(2, 2))       # creating values of 2 strings (2grams)
# 	      count_matrix = coun_vect.fit_transform([resume])      
# 	      list_2grams_resume = coun_vect.get_feature_names()    # list of 2grams values from resume

# 	      if pd.Series(must_have).isin(list_2grams_resume)[0]:  # in the case the must_have exists in the resume list of 2 grams
# 		m_have.append(100)                                  # add value of 100
# 	      else:
# 		m_have.append(0)                                    # else, keep the value 0
# 	    df_resumes_pts[must_have] = m_have                          # create a column of 0 and 100 in df_resumes

# 	  elif must_have_len == 3:
# 	    for i in range(len(df_resumes_copy)):                          # running for all resumes
# 	      resume = df_resumes_copy['resume_clean_transformed'][i]    
# 	      coun_vect = CountVectorizer(ngram_range=(3, 3))       # creating values of 3 strings (3grams)
# 	      count_matrix = coun_vect.fit_transform([resume])      
# 	      list_3grams_resume = coun_vect.get_feature_names()    # list of 3grams values from resume

# 	      if pd.Series(must_have).isin(list_3grams_resume)[0]:  # in the case the must_have exists in the resume list of 3 grams
# 		m_have.append(100)                                  # add value of 100
# 	      else:
# 		m_have.append(0)                                    # else, keep the value 0
# 	    df_resumes_pts[must_have] = m_have                          # create a column of 0 and 100 in df_resumes

# 	  elif must_have_len > 3:
# 	    df_resumes_pts = df_resumes_copy[['id', 'percentages_Count_Transformed', 'percentages_Tfid_Transformed']]
# 	    print('Your must have expressions should have max 3 words')
# 	    break

# 	  j += 1
		
# 	df_resumes_final_ranking = df_resumes_pts[['id', 'percentages_Tfid_Transformed', 'business analyst', 'business process', 'stakeholder management']]
# 	df_resumes_final_ranking['final_score'] = df_resumes_final_ranking['percentages_Tfid_Transformed']+\
# 						  df_resumes_final_ranking['business analyst']+\
# 						  df_resumes_final_ranking['business process']+\
# 						  df_resumes_final_ranking['stakeholder management']
# 	df_resumes_final_ranking['final_ranking'] = get_positions(df_resumes_final_ranking,'final_score')
	
# 	# the final dataframe
# 	df_ranking = df_resumes_final_ranking[['id','final_ranking']]
# 	st.dataframe(df_ranking.sort_values('final_ranking', ascending=True))
		
