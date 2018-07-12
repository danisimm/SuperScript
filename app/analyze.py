import pandas as pd
import numpy as np
import re, string

from nltk import WhitespaceTokenizer
from gensim.models.keyedvectors import KeyedVectors

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from scipy.spatial.distance import cosine
from scipy.stats.mstats import gmean

import pickle
import visualizations
import time

regex = re.compile('[%s]' % re.escape(string.punctuation))
tokenizer = WhitespaceTokenizer()
stoplist = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

import json
filename = "static/hedonometer.json"
with open(filename, 'r') as f:
    datastore = json.load(f)
hedonometer = dict()
for key in datastore.get('objects'):
    hedonometer[key.get('word')] = key.get('happs')

caps = "([A-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".","<stop>")
    text = text.replace("?","<stop>")
    text = text.replace("!","<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

def Analyze(des,dia):
    description = Parse(des)
    dialogue  = Parse(dia)
    glove_model = PrepGlove()
    timestamp = int(time.time())
    coher = Average(description, dialogue, 1)
    happs = Average(description, dialogue, 2)
    visualizations.create_image(coher*100, 'coher', timestamp, percentage=True)
    visualizations.create_image(happs, 'happs', timestamp)
    return timestamp

def Parse(text):
    sents = list()
    for sent in split_into_sentences(text):
        sent_tokens = tokenizer.tokenize(sent)
        sent_temp = list()
        for token in sent_tokens:
            if re.search('[a-zA-Z]', token):
                if not token.isupper():
                    if token.lower() not in stoplist:
                        splits = regex.sub(" ", token.lower()).strip().split(" ")
                        for x in splits:
                            sent_temp.append(x)
        sents.append(sent_temp)
    return sents

def Coherence(row,glove_model,plot=False, time=0):
    fig = plt.figure()
    sent_vecs = list()
    doc_vec = np.zeros([50])
    if len(row)>500:
        for sent in row:
            vec_sum = np.zeros([50])
            for word in sent:
                if word in glove_model:
                    vec_sum = np.add(vec_sum, glove_model[word])
            sent_vecs.append(vec_sum)
            doc_vec = np.add(doc_vec, vec_sum)
        cos_sim = list()

        for i, vec in enumerate(sent_vecs):
            if i<len(sent_vecs)-1:
                X = sent_vecs[i].reshape(-1,1)
                Y = doc_vec.reshape(-1,1)
                if np.linalg.norm(X) != 0 and np.linalg.norm(Y) != 0:
                    temp = cosine(X, Y)
                    cos_sim.append(temp)

        if len(cos_sim)>0:
            if plot:
                df = pd.DataFrame(cos_sim)
                window = int(len(df)/10)
                foo = df.dropna().rolling(window, center=True).apply(gmean)*100
                scale = foo.index.values/len(foo)*100
                plt.plot(scale, foo[0])
                plt.title("Script Coherence")
                plt.ylabel("% Coherence")
                plt.xlabel("% of script")
                plt.savefig('static/graphs/coher' + str(time) + '.png', transparent=True)
                plt.clf()
            mean = sum(cos_sim)/len(cos_sim)
            return mean
    return None

def PrepGlove():
    glove_model = KeyedVectors.load_word2vec_format("static/gensim_glove_vectors.txt", binary=False)
    return glove_model

def Happiness(row, plot=False, time=0):
    sent_sum = list()
    if len(row)>500:
        for sent in row:
            hap_sum = list()
            for word in sent:
                if word in hedonometer.keys():
                    hap_sum.append(hedonometer[word])
            if len(hap_sum) > 0:
                temp = sum(hap_sum)/len(hap_sum)
                sent_sum.append(temp)
        if len(sent_sum)>0:
            if plot:
                df = pd.DataFrame(sent_sum)
                window = int(len(df)/10)
                foo = df.dropna().rolling(window, center=True).apply(gmean)
                scale = foo.index.values/len(foo)*100
                plt.plot(scale, foo[0])
                plt.title("Script Sentiment")
                plt.ylabel("Happiness Score")
                plt.xlabel("% of script")
                plt.savefig('static/graphs/happs' + str(time) + '.png', transparent=True)
                plt.clf()
            mean = sum(sent_sum)/len(sent_sum)
            return mean
    return None  

def Average(col1, col2, x):
    if x==1:
        try:
            val1 = Coherence(col1 ,glove_model, plot=True, time=timestamp)
        except:
            return 0
        try:
            val2 = Coherence(col2 ,glove_model)
        except:
            val2 = val1
        return (val1+val2)/2
    if x==2:
        try:
            val1 = Happiness(col1, plot=True, time=timestamp)
        except:
            return 0
        try:
            val2 = Happiness(col2)
        except:
            val2 = val1
        return (val1+val2)/2